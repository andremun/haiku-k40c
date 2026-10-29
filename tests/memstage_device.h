// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memstage/Mapper.h"
#include <cassert>
#include <vector>
using namespace k40::memstage;
using namespace k40::memory::vram;
struct Device:Io {
    std::vector<uint32_t> ram=std::vector<uint32_t>(4*1024*1024);
    std::vector<std::pair<uint32_t,uint32_t>> writes;
    uint64_t clock=10,step=1,window=0,cached[2]{};
    uint32_t context=0,pdbSelector=0,failReg=0,failReadReg=0;unsigned flushes=0,invalidates=0,disables=0;
    bool backwards=false,slowSlots=false,dirtyAfterInvalidate=false,wrongContextRead=false;
    bool locks[2]{},modeSticks=false,mode16=true,slots=true,queued=true,ignoreInvalidate=false,alias=false,failDisable=false;
    bool active() const override{return true;}
    CacheProfile profile() const override{return CacheProfile::ExplicitUncached;}
    bool acquire(Lock l) override{auto& held=locks[unsigned(l)];if(held)return false;held=true;return true;}
    void release(Lock l) override{assert(locks[unsigned(l)]);locks[unsigned(l)]=false;}
    bool now(uint64_t& t) override{if(backwards)--clock;else clock+=step;t=clock;return true;}
    bool storeFence() override{assert(locks[0]);return true;}
    bool loadFence() override{return true;}
    uint64_t word64(uint64_t address) const{return uint64_t(ram.at(address/4))+uint64_t(ram.at(address/4+1))*4294967296ULL;}
    bool read32(uint32_t reg,uint32_t& value) override{
        if(reg==failReadReg)return false;
        if(reg==0x2100 && dirtyAfterInvalidate && invalidates){value=1;return true;}
        if(reg>=0x700000 && reg<0x800000){assert(locks[0]);value=ram.at((window+reg-0x700000)/4);return true;}
        if(reg==0x1704){value=context+((wrongContextRead && invalidates==3)?1:0);return true;}
        if(reg==0x100c80){if(slowSlots && !slots)clock+=1000000;value=(slots?0x10000:0)+(queued?0x8000:0)+(mode16?1:0);return true;}
        if(reg==0x22438 || reg==0x2243c){value=6;return true;}
        if(reg>=0x11020c && reg<=0x11520c && (reg-0x11020c)%4096==0){value=1920;return true;}
        value=reg==0x22700?3:0;return true;
    }
    bool write32(uint32_t reg,uint32_t value) override {
        writes.push_back({reg,value});if(reg==failReg)return false;
        if(reg==0x1700){assert(locks[0]);window=uint64_t(value)*65536;return true;}
        if(reg>=0x700000 && reg<0x800000){assert(locks[0]);ram.at((window+reg-0x700000)/4)=value;return true;}
        if(reg==0x70000){assert(locks[0] && value==1);++flushes;return true;}
        assert(locks[1]);
        if(reg==0x100c80){if(!modeSticks)mode16=value&1;return true;}
        if(reg==0x100cb8){assert(!(value&15));pdbSelector=value;return true;}
        if(reg==0x100cbc){assert(value==0x80000005 && pdbSelector);++invalidates;if(!ignoreInvalidate)cached[0]=cached[1]=0;return true;}
        assert(reg==0x1704);
        if(!(value&0x80000000)){++disables;if(failDisable)return false;}
        else cached[0]=cached[1]=0;
        context=value;return true;
    }
    bool barRead32(uint64_t offset,uint32_t& value) override {
        assert(locks[1] && !locks[0]);if(!(context&0x80000000) || offset>=8192 || (offset%4))return false;
        unsigned page=unsigned(offset/4096);if(alias)page=0;
        if(!cached[page]) {
            const uint64_t instance=uint64_t(context%0x80000000)*4096;
            const auto directory=word64(instance+512);assert(directory%4096==0);
            if(offset>word64(instance+520))return false;
            const auto pde=word64(directory+(offset/134217728)*8);
            assert(uint32_t(pde)==0 && ((pde/4294967296ULL)%16)==1);
            const auto spt=(pde/68719476736ULL)*4096;
            const auto pte=word64(spt+page*8);
            assert(pte%16==5 && pte/68719476736ULL==0);
            cached[page]=(pte/16)*4096;
        }
        value=ram.at((cached[page]+offset%4096)/4);return true;
    }
};
