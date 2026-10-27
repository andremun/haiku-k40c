// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Host owner-lifetime simulation. No device files, VM or physical GPU access.
#include "os/NativeOwner.h"
#include "i2c_wire.h"
#include <fstream>
#include <chrono>
#include <thread>
#include <iostream>
#include <map>
#include <memory>
#include <new>
#include <stdexcept>
#include <vector>
using namespace k40::os;
using namespace k40::devinit;
using k40::runtime::startup::BootState;
static unsigned checks=0, cases=0, freed=0;
static std::map<int,std::vector<uint8_t>> areas;
static int nextArea=1;
static void require(bool value,const char* message) { ++checks;if(!value)throw std::runtime_error(message); }
extern "C" status_t k40_os_allocate_dma32(size_t bytes,k40_host_allocation* out)
{
    auto& memory=areas[nextArea]; memory.resize(bytes);
    *out={nextArea++,memory.data(),bytes,0x10000000};return B_OK;
}
extern "C" status_t k40_os_free(k40_host_allocation* allocation)
{
    areas.erase(allocation->area);++freed;*allocation={-1,nullptr,0,0};return B_OK;
}
struct Boot {
    struct alignas(NativeOwner) Storage { unsigned char bytes[sizeof(NativeOwner)]; };
    std::unique_ptr<Storage> storage=std::make_unique<Storage>();
    NativeOwner* owner=new(storage->bytes) NativeOwner;
    uint64_t lease=0;
    Boot() { require(owner->acquire(lease)==OwnerError::None,"acquire"); }
    OwnerPostInfo post() { OwnerPostInfo result;require(owner->inspectPost(lease,result)==OwnerError::None,"post inspect");return result; }
    OwnerInfo info() { OwnerInfo result;require(owner->inspect(result)==OwnerError::None,"owner inspect");return result; }
    void reload(OwnerError expected) {
        const auto old=lease;require(owner->detach(lease)==expected,"detach");
        require(owner->acquire(lease)==OwnerError::None && lease>old,"reacquire");
        OwnerPostInfo result;require(owner->inspectPost(old,result)==OwnerError::Lease,"stale inspect");
    }
};
struct Host : Wire {
    NativeOwner* owner=nullptr;
    uint64_t lease=0;
    unsigned straps=0,pins=0,reentries=0;
    uint32_t fallback=0;
    bool strapFailure=false,pinFailure=false,throwPin=false,interpreting=false;
    void trace(uint32_t,uint8_t,bool) override { interpreting=true; }
    bool read32(uint32_t reg,uint32_t& value) override {
        if(reg==0x101000) {
            if(!interpreting)++straps;
            requireRunning();if(strapFailure)return false;
        }
        if(reg==0xd054) { requireRunning();return Wire::read32(reg,value); }
        value=reg==0x101000?0:fallback;return event('R',4,reg,value);
    }
    bool write32(uint32_t reg,uint32_t value) override {
        requireRunning();
        if(reg==0xd054) {
            ++pins;if(throwPin)throw std::runtime_error("injected host callback exception");
            if(pinFailure)return false;
            return Wire::write32(reg,value);
        }
        return BoardFake::write32(reg,value);
    }
    void requireRunning() {
        OwnerInfo info;
        require(owner->inspect(info)==OwnerError::Busy,"callback escaped owner guard");
        require(owner->detach(lease)==OwnerError::Busy,"callback detached owner");
        require(owner->begin(lease)==OwnerError::Busy,"callback reset startup");
        ++reentries;
    }
};
static void run(const std::vector<uint8_t>& rom)
{
    {
        Boot boot;Host host;host.owner=boot.owner;host.lease=boot.lease;
        require(boot.owner->simulatePost(boot.lease,host,host)==OwnerError::Input && !host.calls,"unbound execution");
        require(boot.owner->bindPost(boot.lease+1,rom.data(),rom.size())==OwnerError::Lease,"invalid bind lease");
        require(boot.owner->bindPost(boot.lease,nullptr,rom.size())==OwnerError::Input,"null ROM");
        require(boot.owner->bindPost(boot.lease,rom.data(),rom.size()-1)==OwnerError::Input,"short ROM");
        require(!boot.post().bindingAttempted,"invalid extent consumed slot");
        auto wrong=rom;wrong[0]^=1;
        require(boot.owner->bindPost(boot.lease,wrong.data(),wrong.size())==OwnerError::Input,"wrong identity");
        require(boot.post().bindingAttempted && !boot.post().bound,"rejected image status");
        boot.reload(OwnerError::None);
        require(boot.owner->bindPost(boot.lease,rom.data(),rom.size())==OwnerError::Input,"replaced rejected image");
        require(boot.owner->simulatePost(boot.lease,host,host)==OwnerError::Input && !host.calls,"rejected image executed");++cases;
    }
    for(unsigned profile=0;profile<2;++profile) {
        Boot boot;auto input=rom;
        require(boot.owner->bindPost(boot.lease,input.data(),input.size())==OwnerError::None,"bind exact ROM");
        input.assign(input.size(),0); // Caller bytes cannot change resident execution.
        require(boot.owner->bindPost(boot.lease,rom.data(),rom.size())==OwnerError::Input,"replaced bound image");
        boot.reload(OwnerError::None);
        uint64_t token=0;require(boot.owner->allocate(boot.lease,4096,4096,token)==OwnerError::None,"allocate before POST");
        require(boot.owner->publish(boot.lease,token)==OwnerError::DmaDenied,"published unverified DMA");
        OwnerPostInfo outcome;
        {
            Host host;host.owner=boot.owner;host.lease=boot.lease;host.fallback=profile?UINT32_MAX:0;
            require(boot.owner->simulatePost(boot.lease+1,host,host)==OwnerError::Lease && !host.calls,"stale run lease");
            require(boot.owner->simulatePost(boot.lease,host,host,{0,32,1000})==OwnerError::Input && !host.calls,"zero budget");
            host.simulation=false;
            require(boot.owner->simulatePost(boot.lease,host,host)==OwnerError::Input && !host.calls,"hardware backend");
            host.simulation=true;
            require(boot.info().startup==BootState::Fresh && !boot.post().executionAttempted,"preflight consumed latch");
            require(boot.owner->simulatePost(boot.lease,host,host,{100000,32,1000000000})==OwnerError::None,"host simulation rejected");
            outcome=boot.post();
            require(host.straps==1 && host.reentries && outcome.ramSelected && outcome.ramIndex==0,"selection/reentrancy");
            require(outcome.result.error==Error::None || (outcome.result.error==Error::Denied && outcome.result.offset==0x89c2),"unexpected POST result");
            if(outcome.result.error==Error::None)require(host.decoded==std::vector<uint8_t>({0x40,0xdd,3,0x98,0x19,0x73,0x98,0x0d,0x73}),"resident POST payload");
            require(boot.info().startup==(outcome.result.error==Error::None?BootState::Complete:BootState::Failed),"terminal boot state");
        } // All callback objects die before detach/reload and inspection.
        require(boot.info().owned==1 && boot.info().quarantined==1,"immediate quarantine");
        HaikuMemory::Info retained;
        require(boot.owner->describe(boot.lease,0,retained)==OwnerError::None && retained.token==token && retained.quarantined,"retained record");
        const auto releases=freed;
        boot.reload(OwnerError::Retained);
        Host replacement;replacement.owner=boot.owner;replacement.lease=boot.lease;
        require(boot.owner->simulatePost(boot.lease,replacement,replacement)==OwnerError::Startup && !replacement.calls,"reload retried POST");
        require(boot.owner->bindPost(boot.lease,rom.data(),rom.size())==OwnerError::Startup,"reload replaced POST");
        require(boot.owner->begin(boot.lease)==OwnerError::Retained,"separate latch bypass");
        require(boot.owner->allocate(boot.lease,64,64,token)==OwnerError::Retained,"quarantine allocation");
        require(boot.post().result.error==outcome.result.error && freed==releases,"lost outcome/storage after callback death");++cases;
    }
    // Failed selection, failed init, NACK and a throwing host callback all retain
    // the same one-shot outcome after the client and its callbacks are replaced.
    for(unsigned fault=0;fault<4;++fault) {
        Boot boot;require(boot.owner->bindPost(boot.lease,rom.data(),rom.size())==OwnerError::None,"fault bind");
        uint64_t token=0;require(boot.owner->allocate(boot.lease,64,64,token)==OwnerError::None,"fault allocation");
        {
            Host host;host.owner=boot.owner;host.lease=boot.lease;
            host.strapFailure=fault==0;host.pinFailure=fault==1;host.nackAt=fault==2?1:0;host.throwPin=fault==3;
            bool caught=false;
            try { require(boot.owner->simulatePost(boot.lease,host,host)==OwnerError::None,"fault admission"); }
            catch(const std::runtime_error& e) { if(std::string(e.what())!="injected host callback exception")throw;caught=true; }
            require(caught==(fault==3),"exception fixture");
            require(host.straps==1 && (fault!=0 || !host.pins),"failed strap reached preinit");
            require(boot.post().result.error==Error::Io && boot.info().startup==BootState::Failed,"fault state not retained");
        }
        boot.reload(OwnerError::Retained);
        Host next;next.owner=boot.owner;next.lease=boot.lease;
        require(boot.owner->simulatePost(boot.lease,next,next)==OwnerError::Startup && !next.calls,"fault retried");
        require(boot.info().quarantined==1 && boot.post().selectionAttempted,"fault quarantine/selection lost");++cases;
    }
    {
        Boot boot;require(boot.owner->bindPost(boot.lease,rom.data(),rom.size())==OwnerError::None,"concurrent bind");
        struct BlockingHost : Host {
            std::atomic<bool> entered{false},proceed{false};
            bool read32(uint32_t reg,uint32_t& value) override {
                if(reg==0x101000 && !interpreting) {
                    entered.store(true,std::memory_order_release);
                    const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(5);
                    while(!proceed.load(std::memory_order_acquire)) {
                        if(std::chrono::steady_clock::now()>deadline)throw std::runtime_error("host fixture gate timeout");
                        std::this_thread::yield();
                    }
                }
                return Host::read32(reg,value);
            }
        } host;
        host.owner=boot.owner;host.lease=boot.lease;
        OwnerError admitted=OwnerError::Input;std::exception_ptr exception;
        std::thread runner([&]{try { admitted=boot.owner->simulatePost(boot.lease,host,host); }catch(...){exception=std::current_exception();}});
        struct Join {
            BlockingHost& host;std::thread& runner;
            ~Join() {host.proceed.store(true,std::memory_order_release);if(runner.joinable())runner.join();}
        } join{host,runner};
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(5);
        while(!host.entered.load(std::memory_order_acquire) && std::chrono::steady_clock::now()<deadline)std::this_thread::yield();
        require(host.entered.load(std::memory_order_acquire),"concurrent fixture entry");
        // These Busy calls do not read or mutate the host callback's data.
        OwnerPostInfo post;
        if(boot.owner->inspectPost(boot.lease,post)!=OwnerError::Busy)throw std::runtime_error("concurrent inspection escaped guard");
        if(boot.owner->detach(boot.lease)!=OwnerError::Busy)throw std::runtime_error("concurrent detach escaped guard");
        if(boot.owner->bindPost(boot.lease,rom.data(),rom.size())!=OwnerError::Busy)throw std::runtime_error("concurrent bind escaped guard");
        host.proceed.store(true,std::memory_order_release);runner.join();
        if(exception)std::rethrow_exception(exception);
        require(admitted==OwnerError::None && boot.info().startup!=BootState::Running,"concurrent completion");++cases;
    }
    {
        Boot boot;require(boot.owner->bindPost(boot.lease,rom.data(),rom.size())==OwnerError::None,"latch conflict bind");
        require(boot.owner->begin(boot.lease)==OwnerError::None,"consume other startup");
        Host host;host.owner=boot.owner;host.lease=boot.lease;
        require(boot.owner->simulatePost(boot.lease,host,host)==OwnerError::Startup && !host.calls,"other latch bypassed");
        boot.reload(OwnerError::None);
        require(boot.info().startup==BootState::Failed && boot.post().bound && !boot.post().executionAttempted,"abandoned startup lost");++cases;
    }
}
int main(int argc,char** argv)
{
    try {
        require(argc==2,"usage: owner_post_probe ROM");std::ifstream input(argv[1],std::ios::binary);
        require(bool(input),"ROM absent");input.seekg(0,std::ios::end);require(input.tellg()==approvedRomBytes,"ROM size");input.seekg(0);
        std::vector<uint8_t> rom(approvedRomBytes);input.read(reinterpret_cast<char*>(rom.data()),rom.size());require(bool(input),"short ROM");
        run(rom);
        std::cout<<"owner_post host_cases "<<cases<<" assertions "<<checks<<" failures 0 native_execution 0 hardware_execution 0\n";
        return 0;
    } catch(const std::exception& error) { std::cerr<<"owner_post_probe: "<<error.what()<<'\n';return 1; }
}
