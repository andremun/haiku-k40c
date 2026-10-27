// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Offline exact-ROM binding/policy exercise. Never outputs firmware payloads.
#include "devinit/BoundPost.h"
#include "board_fake.h"
#include "i2c_wire.h"
#include <fstream>
#include <iostream>
#include <memory>
#include <vector>
using namespace k40::devinit;
struct Fake : BoardFake {
    uint32_t fallback=0, straps=0;
    bool failStrap=false, rollback=false;
    unsigned nowCalls=0;
    uint64_t nowUs() override { return rollback && ++nowCalls>5?0:++clock; }
    bool read32(uint32_t at,uint32_t& value) override {
        if(at==0x101000) { ++straps; if(failStrap)return false; }
        const auto found=regs.find(at);value=found==regs.end()?fallback:found->second;
        return event('R',4,at,value);
    }
};
static void require(bool value,const char* text) { if(!value)throw std::runtime_error(text); }
struct PostWire : Wire {
    const PostImage* image = nullptr;
    uint32_t pc = 0, fallback = 0;
    unsigned pinCalls = 0, failPin = 0, transactionCallbacks = 0, deadlinePin = 0, rollbackPin = 0;
    bool policyViolation = false, preparing = true;
    void trace(uint32_t at,uint8_t,bool) override { pc=at; }
    bool pin(char kind,uint32_t at,uint32_t value=0) {
        ++pinCalls;
        if (preparing) policyViolation |= kind!='W' || value!=7;
        else policyViolation |= !image->allow(pc,at,4,kind=='W');
        if(pinCalls==deadlinePin) clock+=1000000000;
        if(pinCalls==rollbackPin) clock=0;
        return !failPin || pinCalls!=failPin;
    }
    bool read32(uint32_t at,uint32_t& value) override {
        if (at==0xd054) return pin('R',at) && Wire::read32(at,value);
        value=at==0x101000?0:fallback;
        return event('R',4,at,value);
    }
    bool write32(uint32_t at,uint32_t value) override {
        if (at==0xd054) return pin('W',at,value) && Wire::write32(at,value);
        return BoardFake::write32(at,value);
    }
    bool i2cWrite(const I2cBus&,uint8_t,uint8_t,uint8_t) override {
        ++transactionCallbacks; return false;
    }
};
static void pins(const std::vector<uint8_t>& rom)
{
    unsigned complete=0,denied=0,faults=0;
    for (unsigned profile=0;profile<2;++profile) {
        auto image=std::make_unique<PostImage>(rom.data(),rom.size()); PostWire wire;
        wire.image=image.get(); wire.fallback=profile?UINT32_MAX:0;
        require(image->selectRam(wire)==Error::None,"pin RAM setup");
        BoundPost bound(*image,wire,wire,PostI2c::DedicatedPins);
        const auto count=wire.calls;
        require(bound.runPost().error==Error::Input && wire.calls==count,"implicit bus initialization");
        require(bound.prepareI2c()==Error::None && wire.pinCalls==1 && wire.events.back().value==7,"separate bus preinit");
        wire.preparing=false;
        const auto initCalls=wire.calls;
        require(bound.prepareI2c()==Error::Input && wire.calls==initCalls,"preinit retry");
        const auto result=bound.runPost({100000,32,1000000000});
        if(result.error==Error::None)++complete;
        else if(result.error==Error::Denied && result.offset==0x89c2)++denied;
        else throw std::runtime_error("pin run error "+std::to_string(int(result.error))+" at "+std::to_string(result.offset));
        require(!wire.policyViolation && !wire.transactionCallbacks,"pin permission bypass");
        const std::vector<uint8_t> payload={0x40,0xdd,3,0x98,0x19,0x73,0x98,0x0d,0x73};
        if(result.error==Error::None) require(wire.decoded==payload && wire.starts==3 && wire.stops==3,"bound I2C wire payload");
        else require(wire.decoded==std::vector<uint8_t>({0x40,0xdd,3}),"denied GPIO effects crossed");
        BoundPost fresh(*image,wire,wire,PostI2c::DedicatedPins);
        const auto end=wire.calls;
        require(fresh.prepareI2c()==Error::Input && fresh.runPost().error==Error::Input && wire.calls==end,"new adapter bypassed once guard");
    }
    // Existing standalone wire tests cover every callback. These exercise the
    // bound path: failed preparation, payload NACKs, pin I/O and stretch limits.
    for(unsigned kind=0;kind<10;++kind) {
        auto image=std::make_unique<PostImage>(rom.data(),rom.size()); PostWire wire;wire.image=image.get();
        require(image->selectRam(wire)==Error::None,"pin fault setup");
        BoundPost bound(*image,wire,wire,PostI2c::DedicatedPins);
        if(kind==0) wire.failPin=1;
        const auto prepared=bound.prepareI2c();
        if(kind==0) {
            require(prepared==Error::Io && bound.prepareI2c()==Error::Input,"failed initialization retry");
            const auto calls=wire.calls;
            require(bound.runPost().error==Error::Input && wire.calls==calls,"failed preinit executed");
        } else {
            require(prepared==Error::None,"pin fault preinit"); wire.preparing=false;
            if(kind<=3) wire.nackAt=kind;
            if(kind==4) wire.failPin=2;
            if(kind==5) wire.failPin=100;
            if(kind==6) wire.stuck=true;
            if(kind==7) wire.rollbackPin=2;
            if(kind==8) wire.deadlinePin=2;
            if(kind==9) { wire.frozen=true;wire.stuck=true; }
            const auto result=bound.runPost({100000,32,1000000000});
            require(result.error==(kind==7?Error::Clock:(kind==8?Error::Timeout:Error::Io)),("bound pin fault lost kind "+std::to_string(kind)+" error "+std::to_string(int(result.error))).c_str());
            if(kind<=3) require(wire.stops==1 && bound.i2cResult().primary==I2cError::Nack
                && bound.i2cResult().cleanup==I2cError::None,"bound NACK cleanup");
            if(kind==4 || kind==5) require(bound.i2cResult().cleanup==I2cError::Io,"bound transport fail-closed cleanup");
            const auto calls=wire.calls;
            require(bound.runPost().error==Error::Input && calls==wire.calls,"pin fault retried");
        }
        require(!wire.policyViolation && !wire.transactionCallbacks,"fault bypassed pin guard");++faults;
    }
    {
        auto image=std::make_unique<PostImage>(rom.data(),rom.size());PostWire wire;wire.image=image.get();wire.simulation=false;
        BoundPost bound(*image,wire,wire,PostI2c::DedicatedPins);
        require(bound.prepareI2c()==Error::HardwareDisabled && bound.runPost().error==Error::HardwareDisabled && wire.events.empty(),"pin hardware refusal");
    }
    std::cout<<"dedicated_pins profiles 2 complete "<<complete<<" policy_denials "<<denied<<" faults "<<faults<<" permission_bypasses 0 transaction_callbacks 0\n";
}
int main(int argc,char** argv)
{
    try {
        require(argc==3,"usage: post_probe ROM --policy|--exercise");
        std::ifstream input(argv[1],std::ios::binary);require(bool(input),"ROM absent");
        input.seekg(0,std::ios::end);require(input.tellg()==approvedRomBytes,"wrong ROM size");input.seekg(0);
        std::vector<uint8_t> rom(approvedRomBytes);input.read(reinterpret_cast<char*>(rom.data()),rom.size());require(bool(input),"short ROM");
        auto image=std::make_unique<PostImage>(rom.data(),rom.size());
        require(image->approved(),("layout/identity rejected: "+std::to_string(int(image->layoutError()))).c_str());
        if(std::string(argv[2])=="--policy") {
            uint32_t pc,reg,width,write;
            while(std::cin>>std::hex>>pc>>reg>>width>>write)std::cout<<image->allow(pc,reg,width,write!=0)<<'\n';
            return 0;
        }
        if(std::string(argv[2])=="--pins") { pins(rom);return 0; }
        require(std::string(argv[2])=="--exercise","unknown mode");
        require(image->instructionCount()==530 && image->roots()==8,"unexpected compiled closure");
        Fake unbound;BoundPost noRam(*image,unbound,unbound);
        require(noRam.runPost().error==Error::Input && unbound.events.empty(),"missing live input accepted");
        Fake first;first.regs[0x101000]=12;
        require(image->selectRam(first)==Error::None && first.straps==1 && image->ramIndex()==3,"RAM binding differs");
        first.regs[0x101000]=0;
        require(image->selectRam(first)==Error::Input && first.straps==1,"strap reread allowed");
        const auto before=image->root(0);
        rom[0]=uint8_t(~rom[0]);rom[before]=0xfe;
        require(image->approved() && image->root(0)==before,"snapshot aliases caller");
        auto changed=std::make_unique<PostImage>(rom.data(),rom.size());require(!changed->approved(),"wrong image accepted");
        // Hardware refusal precedes the one-shot attempt and every callback.
        Fake hardware;hardware.simulation=false;BoundPost denied(*image,hardware,hardware);
        require(denied.runPost().error==Error::HardwareDisabled && hardware.events.empty(),"hardware reached adapter");
        BoundPost preserved(*image,first,first);
        const auto retained=preserved.runPost({100000,32,1000000000});
        require(retained.error==Error::None || (retained.error==Error::Denied && retained.offset==0x89c2),"caller mutation reached execution");
        rom[0]=uint8_t(~rom[0]); // Restore input by re-reading, not by reconstructing firmware bytes.
        input.clear();input.seekg(0);input.read(reinterpret_cast<char*>(rom.data()),rom.size());
        auto failed=std::make_unique<PostImage>(rom.data(),rom.size());Fake failure;failure.failStrap=true;
        require(failed->selectRam(failure)==Error::Io && failed->selectRam(failure)==Error::Input && failure.straps==1,"failed strap retry");
        for(unsigned problem=0;problem<4;++problem) {
            auto selected=std::make_unique<PostImage>(rom.data(),rom.size());Fake fake;
            require(selected->selectRam(fake)==Error::None,"fault setup failed");
            Limits limits{100000,32,1000000000};
            Error expected=Error::None;
            if(problem==0) { fake.failAt=int(fake.calls); expected=Error::Io; }
            if(problem==1) { limits.timeoutUs=5; expected=Error::Timeout; }
            if(problem==2) { limits.steps=1; expected=Error::Budget; }
            if(problem==3) { fake.rollback=true; expected=Error::Clock; }
            BoundPost bound(*selected,fake,fake);
            require(bound.runPost(limits).error==expected,"failure budget/clock/I/O not preserved");
            const auto effects=fake.events.size();
            require(bound.runPost().error==Error::Input && fake.events.size()==effects,"failed POST retry allowed");
        }
        unsigned successes=0,denials=0;
        for(unsigned profile=0;profile<2;++profile)for(unsigned strap=0;strap<16;++strap) {
            auto selected=std::make_unique<PostImage>(rom.data(),rom.size());Fake fake;
            fake.fallback=profile?UINT32_MAX:0;fake.regs[0x101000]=strap<<2;
            require(selected->selectRam(fake)==Error::None && fake.straps==1,"strap selection failed");
            BoundPost bound(*selected,fake,fake);
            const auto result=bound.runPost({100000,32,1000000000});
            if(result.error==Error::None)++successes;
            else if(result.error==Error::Denied && result.offset==0x89c2)++denials;
            else throw std::runtime_error("unexpected run failure at "+std::to_string(result.offset)+" error "+std::to_string(int(result.error)));
            const auto calls=fake.events.size();
            require(bound.runPost().error==Error::Input && fake.events.size()==calls,"POST repeated");
        }
        std::cout<<"instructions 530 roots 8 scenarios 32 successes "<<successes<<" policy_denials "<<denials<<"\n";
        return 0;
    } catch(const std::exception& error) { std::cerr<<"post_probe: "<<error.what()<<'\n';return 1; }
}
