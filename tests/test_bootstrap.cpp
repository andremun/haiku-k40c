// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#include "runtime/Bootstrap.h"
#include <cstdio>
#include <map>
#include <tuple>
#include <vector>
using namespace k40::runtime;
static unsigned checks=0,failed=0;
#define CHECK(c) do{++checks;if(!(c)){++failed;std::printf("FAIL line %d: %s\n",__LINE__,#c);}}while(0)
struct Fake:BootstrapPort {
    bool simulation=true,held=false,allowLock=true,busy=false,writeOk=true,freeze=false,alias=false;
    unsigned unlocks=0;uint64_t clock=0,window=0;
    std::map<uint64_t,uint32_t> memory;std::vector<std::tuple<char,uint32_t,uint32_t>> log;
    bool hostSimulation()const override{return simulation;}
    bool lock()override{if(!allowLock)return false;held=true;return true;}
    void unlock()override{held=false;++unlocks;}
    uint64_t nowUs()override{return freeze?0:++clock;}
    bool write32(uint32_t r,uint32_t v)override{
        CHECK(held);log.emplace_back('W',r,v);if(!writeOk)return false;
        if(r==0x1700)window=uint64_t(v)<<16;
        else if(r>=0x700000 && r<0x800000)memory[alias ? ((window+(r-0x700000))&0xfff) : window+(r-0x700000)]=v;
        return true;
    }
    bool read32(uint32_t r,uint32_t& v)override{
        CHECK(held);v=busy?0x00100002:0;
        if(r>=0x700000 && r<0x800000)v=memory[alias ? ((window+(r-0x700000))&0xfff) : window+(r-0x700000)];
        log.emplace_back('R',r,v);return true;
    }
};
int main(){
    {Fake f;uint32_t in[]={0x1234,0x5678},out[2]={};OwnedVram owned{{0xffffc},8};
     CHECK(writeSlowWindow(f,owned,0,in,2));CHECK(f.memory[0xffffc]==in[0] && f.memory[0x100000]==in[1]);
     CHECK(readSlowWindow(f,owned,0,out,2));CHECK(out[0]==in[0] && out[1]==in[1]);CHECK(f.unlocks==2&&!f.held);}
    {Fake f;uint32_t v=1;CHECK(!writeSlowWindow(f,{{0},4},0,&v,2));CHECK(f.log.empty());}
    {Fake f;uint32_t v=1;CHECK(!writeSlowWindow(f,{{(1ULL<<44)-4},8},0,&v,1));CHECK(f.log.empty());}
    {Fake f;f.writeOk=false;uint32_t v=1;CHECK(!writeSlowWindow(f,{{0},4},0,&v,1));CHECK(!f.held&&f.unlocks==1);}
    {Fake f;CHECK(flushBar(f,{100,5}));CHECK(std::get<1>(f.log[0])==0x70000);}
    {Fake f;f.busy=true;f.freeze=true;CHECK(!flushBar(f,{100,3}));CHECK(!f.held&&f.log.size()==4);}
    {Fake f;CHECK(commitRunlist(f,4,0x12345000,RunlistTarget::NoncoherentHost,1,{100,3}));
     CHECK(std::get<1>(f.log[0])==0x2270 && std::get<2>(f.log[0])==0x30012345);
     CHECK(std::get<1>(f.log[1])==0x2274 && std::get<2>(f.log[1])==0x400001);
     CHECK(std::get<1>(f.log[2])==0x22a4);}
    {Fake f;CHECK(!commitRunlist(f,16,0,RunlistTarget::Vram,1,{100,3}));CHECK(f.log.empty());}
    {Fake f;CHECK(!commitRunlist(f,0,3,RunlistTarget::Vram,1,{100,3}));CHECK(f.log.empty());}
    {Fake f;CHECK(!commitRunlist(f,0,1ULL<<40,RunlistTarget::Vram,1,{100,3}));}
    {Fake f;f.simulation=false;CHECK(!flushBar(f,{100,3}));CHECK(f.log.empty());}
    {Fake f;f.allowLock=false;CHECK(!flushBar(f,{100,3}));CHECK(f.log.empty()&&f.unlocks==0);}
    {Fake f;uint64_t offsets[]={0,4096};CHECK(checkOwnedScratch(f,{{0},8192},offsets,2,{1000,20}));}
    {Fake f;f.alias=true;uint64_t offsets[]={0,4096};CHECK(!checkOwnedScratch(f,{{0},8192},offsets,2,{1000,20}));}
    {Fake f;uint64_t offsets[]={0,0};CHECK(!checkOwnedScratch(f,{{0},8192},offsets,2,{1000,20}));CHECK(f.log.empty());}
    std::printf("bootstrap operations: %u checks, %u failures (HOST_SIMULATION_ONLY)\n",checks,failed);return failed?1:0;
}
