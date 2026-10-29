// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Actual A7 owner/authentication/control path with simulated MMIO. No OS/GPU calls.
#include "a7/Owner.h"
#include "i2c_wire.h"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <iterator>
#include <memory>
#include <string>
#include <vector>
using namespace k40;
static unsigned checks=0;
static void require(bool value,const char* message){++checks;if(!value)throw std::runtime_error(message);}
static const uint8_t key[32]={0xd7,0x5a,0x98,0x01,0x82,0xb1,0x0a,0xb7,0xd5,0x4b,0xfe,0xd3,0xc9,0x64,0x07,0x3a,
    0x0e,0xe1,0x72,0xf3,0xda,0xa6,0x23,0x25,0xaf,0x02,0x1a,0x68,0xf7,0x07,0x51,0x1a}; // RFC 8032 public TEST 1 key, never production.
namespace k40::a7 {
struct OwnerBoundaryProbe {
    static void overflow(Owner& owner) {
        for(unsigned i=0;i<=PostDiagnostics::capacity;++i)
            owner.diagnostics_.record("synthetic overflow",0,0,owner.platform_.nowUs());
    }
    static bool posting(const Owner& owner) {return owner.io_.phase_==Owner::Transport::Phase::Post;}
    static void rejectOtherPreinitWrites(Owner& owner) {
        auto& io=owner.io_;const auto saved=io.phase_;
        io.phase_=Owner::Transport::Phase::I2c;
        require(io.i2cPin_!=0,"missing derived pin");
        require(io.allowed(io.i2cPin_,4,true),"derived pin denied");
        for(unsigned bus=0;bus<16;++bus) {
            const uint32_t at=0xd014+bus*0x20;
            if(at!=io.i2cPin_)require(!io.write32(at,7),"unrelated I2C bus admitted");
        }
        require(!io.write32(io.i2cPin_,0),"wrong I2C init value admitted");
        uint32_t old=0;require(!io.read32(io.i2cPin_,old),"I2C init read admitted");
        io.phase_=Owner::Transport::Phase::Fifo;
        require(!io.write32(0x200,0),"FIFO write without read admitted");
        require(io.read32(0x200,old),"FIFO probe read denied");
        require(!io.write32(0x200,(old&~0x100u)^2u),"FIFO changed an unrelated bit");
        require(!io.write32(0x200,old|0x100u),"FIFO set before clear admitted");
        require(!io.write32(0x204,0),"other FIFO register admitted");
        io.fifoRead_=false;io.phase_=saved;
    }
    static void rejectThirdFifoWrite(Owner& owner) {
        auto& io=owner.io_;const auto saved=io.phase_;uint32_t value=0;
        io.phase_=Owner::Transport::Phase::Fifo;
        require(io.read32(0x200,value),"FIFO final read denied");
        require(!io.write32(0x200,value&~0x100u),"third FIFO write admitted");
        io.phase_=saved;
    }
};
}
struct Storage:memory::ArmStorage {
    unsigned reserves=0,retains=0;std::vector<uint8_t> bytes;
    bool reserveZeroed(memory::ArmAllocation& out) override {++reserves;bytes.assign(4096,0);out={7,4096,{0x400000}};return true;}
    void retain(const memory::ArmAllocation&) override {++retains;}
};
struct PolicyWire:Wire {
    unsigned fault=0,frameBegin=0;
    bool sawNack=false;
    bool sensor() const {return decoded.size()>frameBegin && decoded[frameBegin]==0x98;}
    bool read32(uint32_t at,uint32_t& out) override {
        if(fault==6 && active && phase==9 && sensor())clock+=100001;
        if(fault==8 && active && phase==9 && sensor())return false;
        if(!Wire::read32(at,out))return false;
        if(active && phase==9) {
            const unsigned byte=unsigned(decoded.size())-frameBegin;
            const bool target=sensor();
            const bool nack=(target && ((fault==1 || fault==4) && byte==1))
                || (target && fault==2 && byte==2) || (target && fault==3 && byte==3)
                || (fault==7 && byte==1 && decoded[frameBegin]==0x40);
            if(nack){out|=0x20;sawNack=true;}
            if(target && fault==5)out&=~0x10u;
        }
        return true;
    }
    bool write32(uint32_t at,uint32_t value) override {
        if(fault==4 && sawNack && active && phase==0 && sensor())return false;
        const auto before=starts;
        if(!Wire::write32(at,value))return false;
        if(starts!=before){frameBegin=unsigned(decoded.size());sawNack=false;}
        return true;
    }
};
struct Hardware:a7::Platform {
    PolicyWire wire;
    unsigned i2cAttempts=0,referenceNacks=0,retries=0,lastI2cPrimary=0,lastI2cCleanup=0;
    std::map<uint32_t,uint32_t> registers;
    a7::Owner* owner=nullptr;
    uint32_t fallback=0,strap=0;
    unsigned writes=0,arms=0,reentries=0;
    bool post=false,failPins=false,denyClock=false,overflow=false;
    bool initialize() override {return true;}
    bool pciCommand(uint16_t& value) override {value=7;return true;}
    uint64_t nowUs() override {return wire.nowUs();}
    bool delayUs(uint64_t us) override {return wire.delayUs(us);}
    bool read32(uint32_t at,uint32_t& value) override {
        if(at==0xd054)return !failPins && wire.read32(at,value);
        if(at==0){value=0x0f1240a1;return true;}
        if(at==0x101000){value=strap<<2;return true;}
        if(owner && a7::OwnerBoundaryProbe::posting(*owner)){
            if(overflow){overflow=false;a7::OwnerBoundaryProbe::overflow(*owner);}
            value=fallback;return true;
        }
        if(at==0x100c10 && arms==1){
            if(owner){const auto before=writes;a7::OwnerBoundaryProbe::rejectThirdFifoWrite(*owner);require(writes==before,"third FIFO write reached hardware");}
            value=0xdeadbeef;return true;
        }
        if(at==0x9400){value=denyClock?0:uint32_t(wire.clock*32+1);return true;}
        if(at==0x9410 || at==0x100 || at==0x22554 || at==0x70000){value=0;return true;}
        if(at==0x22438 || at==0x2243c){value=6;return true;}
        if(at>=0x11020c && at<=0x11520c && (at-0x11020c)%0x1000==0){value=1920;return true;}
        value=registers[at];return true;
    }
    bool write32(uint32_t at,uint32_t value) override {
        require(writesAuthorized(),"physical write escaped permit");++writes;
        if(at==0xd054)return !failPins && wire.write32(at,value);
        if(at==0x100c10){++arms;require(value==0x4000,"wrong arm encoding");}
        registers[at]=value;return true;
    }
    bool read8(uint32_t at,uint8_t& value) override {value=uint8_t(registers[at]);return true;}
    bool write8(uint32_t at,uint8_t value) override {require(writesAuthorized(),"byte write escaped permit");++writes;registers[at]=value;return true;}
    void log(const char* event,uint64_t first,uint64_t second=0) override {
        const std::string name(event);
        if(name=="I2C_REQUEST")++i2cAttempts;
        if(name=="I2C_RESULT"){lastI2cPrimary=unsigned(first);lastI2cCleanup=unsigned(second);}
        if(name=="I2C_DISPOSITION") {
            if(second==unsigned(devinit::I2cDisposition::ReferenceNack))++referenceNacks;
            if(second==unsigned(devinit::I2cDisposition::RetryAddress))++retries;
        }
        if(name=="SCRIPT_ACTIVE" || name=="SCRIPT_SKIPPED") {
            post=true;
            if(owner) {
                uint64_t lease=0;uint8_t request[128];
                require(owner->prepare(lease,request)==a7::Status::Busy,"reentrant prepare");
                require(owner->detach(1)==a7::Status::Busy,"reentrant detach");++reentries;
            }
        }
        if(name=="ARM_BEFORE" && owner) {
            const auto before=writes;a7::OwnerBoundaryProbe::rejectOtherPreinitWrites(*owner);
            require(writes==before,"denied preinit writes reached hardware");
        }


        if(name=="TRACE_BEGIN" || name=="PASS ARM_ONLY_POST")require(!writesAuthorized(),"permit survived execution");
    }
};
int main(int argc,char** argv)
try {
    if(argc<3)return 2;
    std::ifstream input(argv[1],std::ios::binary);
    std::vector<uint8_t> rom((std::istreambuf_iterator<char>(input)),{});
    uint8_t nonce[32],challenge[16];std::fill_n(nonce,32,0x51);std::fill_n(challenge,16,0x61);
    const std::string mode(argv[2]);
    Storage storage;Hardware hardware;
    if(argc>3)hardware.fallback=std::stoul(argv[3])?UINT32_MAX:0;
    if(argc>4)hardware.strap=std::stoul(argv[4]);
    if(mode=="pins-fail")hardware.failPins=true;
    if(mode=="clock-fail")hardware.denyClock=true;
    if(mode=="trace-overflow")hardware.overflow=true;
    const char* faultNames[]={"sensor-address-nack","sensor-register-nack","sensor-value-nack","sensor-stop-fail","sensor-stretch","sensor-timeout","other-address-nack","sensor-io"};
    for(unsigned i=0;i<8;++i)if(mode==faultNames[i])hardware.wire.fault=i+1;
    auto owner=std::make_unique<a7::Owner>(hardware,storage,key,nonce,challenge,rom.data(),rom.size(),11520ULL<<20);
    hardware.owner=owner.get();uint64_t lease=0;uint8_t request[128];
    require(owner->prepare(lease,request)==a7::Status::Ok && lease==1,"prepare failed");
    require(storage.reserves==1 && storage.retains==1 && !hardware.writes,"prepare effects");
    if(mode=="request"){std::cout.write(reinterpret_cast<char*>(request),sizeof(request));return 0;}
    uint8_t grant[192];std::cin.read(reinterpret_cast<char*>(grant),sizeof(grant));require(std::cin.gcount()==192,"grant framing");
    const auto status=owner->submit(lease,grant,sizeof(grant));const auto result=owner->outcome();
    const auto effects=hardware.writes;
    require(owner->submit(lease,grant,sizeof(grant))==a7::Status::Retained && hardware.writes==effects,"startup replay");
    require(owner->detach(lease)==a7::Status::Retained,"detach lost retention");
    uint64_t next=0;require(owner->prepare(next,request)==a7::Status::Retained && !next,"reload bypass");
    require(storage.retains==1 && storage.reserves==1 && std::all_of(storage.bytes.begin(),storage.bytes.end(),[](auto b){return b==0;}),"arm payload touched");
    if(status==a7::Status::Ok) {
        require(result.startup.armAttempts==2 && result.startup.flushReadback==0xdeadbeef,"arming/readback order");
        require(hardware.arms==2 && hardware.registers[0x100c10]==0x4000 && result.scratch,"readiness failed");
        require(owner->state()==runtime::startup::BootState::Complete && hardware.reentries>0,"one-shot completion");
    } else require(owner->state()==runtime::startup::BootState::Failed,"failure lost latch");
    if(mode=="trace-overflow")require(status!=a7::Status::Ok && hardware.arms==1,"overflow reached rearm");
    if(hardware.wire.fault) {
        if(hardware.wire.fault==1) {
            require(status==a7::Status::Ok && hardware.i2cAttempts==9 && hardware.referenceNacks==2 && hardware.retries==6,"sensor NACK policy scope/count");
        } else {
            require(status!=a7::Status::Ok && !hardware.referenceNacks && !hardware.retries,"fatal I2C failure was tolerated");
            const devinit::I2cError expected[]={devinit::I2cError::None,devinit::I2cError::Nack,devinit::I2cError::Nack,devinit::I2cError::Nack,devinit::I2cError::Nack,devinit::I2cError::Stretch,devinit::I2cError::Timeout,devinit::I2cError::Nack,devinit::I2cError::Io};
            require(hardware.lastI2cPrimary==unsigned(expected[hardware.wire.fault]),"wrong native I2C error class");
            if(hardware.wire.fault==4)require(hardware.lastI2cCleanup==unsigned(devinit::I2cError::Io),"STOP error was hidden");
        }
    }
    std::cout<<"status "<<unsigned(status)<<" step "<<unsigned(result.startup.step)<<" error "<<unsigned(result.startup.error)
             <<" arms "<<hardware.arms<<" writes "<<hardware.writes<<" checks "<<checks<<" i2c "<<hardware.i2cAttempts<<" reference-nacks "<<hardware.referenceNacks<<" retries "<<hardware.retries<<" primary "<<hardware.lastI2cPrimary<<" cleanup "<<hardware.lastI2cCleanup<<'\n';
    return 0;
} catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}
