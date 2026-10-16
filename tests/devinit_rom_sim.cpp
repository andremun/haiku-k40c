// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
// Reads a caller-supplied offline ROM. No firmware bytes are embedded here.
#include "devinit/Interpreter.h"
#include <fstream>
#include <iterator>
#include <map>
#include <cstdio>
#include <cstdlib>
#include <vector>
using namespace k40::devinit;
struct Simulation : Backend {
    uint64_t clock=0;unsigned boards=0,reads=0,writes=0;uint32_t fallback;
    std::map<uint32_t,uint32_t> regs;
    explicit Simulation(uint32_t value):fallback(value){}
    bool hostSimulation()const override{return true;}
    uint64_t nowUs()override{return ++clock;}
    bool delayUs(uint64_t us)override{clock+=us;return true;}
    bool read32(uint32_t r,uint32_t& value)override{++reads;auto i=regs.find(r);value=i==regs.end()?fallback:i->second;return true;}
    bool write32(uint32_t r,uint32_t value)override{++writes;regs[r]=value;return true;}
    bool board(uint8_t,uint32_t,const uint8_t*,uint32_t,bool)override{++boards;return true;}
};
int main(int argc,char** argv){
    if(argc<7)return 2;
    std::ifstream file(argv[1],std::ios::binary);
    std::vector<uint8_t> rom((std::istreambuf_iterator<char>(file)),{});
    if(rom.empty() || rom.size()>UINT32_MAX)return 2;
    Tables tables{uint32_t(std::strtoul(argv[2],nullptr,0)),uint32_t(std::strtoul(argv[3],nullptr,0)),uint8_t(std::strtoul(argv[4],nullptr,0)),0};
    unsigned scenarios=0,failed=0;
    for(unsigned index=0;index<tables.ramGroups;++index){
        tables.ramIndex=index;
        for(uint32_t fallback : {0u,0xffffffffu}){
            Simulation backend(fallback);
            for(int arg=5;arg<argc;++arg){
                ++scenarios;
                uint32_t start=std::strtoul(argv[arg],nullptr,0);
                Interpreter interpreter(rom.data(),rom.size(),tables,backend);
                Result r=interpreter.run(start,{100000,32,100000000});
                if(r.error!=Error::None){++failed;std::printf("ROM scenario failed: group %u root %#x error %u offset %#x\n",index,start,unsigned(r.error),r.offset);}
            }
        }
    }
    std::printf("offline ROM interpreter: %u artificial scenarios, %u failures; board helpers simulated, NO hardware evidence\n",scenarios,failed);
    return failed?1:0;
}
