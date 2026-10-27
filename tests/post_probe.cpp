// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Offline exact-ROM binding/policy exercise. Never outputs firmware payloads.
#include "devinit/BoundPost.h"
#include "board_fake.h"
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
