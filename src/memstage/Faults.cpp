// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memstage/Faults.h"
namespace k40::memstage {
bool Faults::stop(Error error)
{
    if(error_==Error::None)error_=error;
    journal_.append({phase_,error_,0,0,0,last_>=start_?last_-start_:0,Operation::Failure});
    return false;
}
bool Faults::clock()
{
    uint64_t current=0;
    if(!port_.now(current) || current<last_)return stop(Error::Clock);
    last_=current;
    if(current-start_>2000000)return stop(Error::Budget); // no source: diagnostic software budget, microseconds.
    return true;
}
bool Faults::read(uint32_t offset,uint32_t& value)
{
    value=0;
    if(!clock())return false;
    if(!port_.read32(offset,value))return stop(Error::Read);
    if(!clock())return false;
    if(!journal_.append({phase_,Error::None,offset,value,0,last_-start_}))return stop(Error::Overflow);
    return true;
}
bool Faults::details(uint32_t mask,uint32_t base,unsigned count,unsigned firstBit)
{
    for(unsigned i=0;i<count;++i)if(mask&(uint32_t(1)<<(firstBit+i))) {
        for(unsigned word=0;word<3;++word) {
            uint32_t value;
            if(!read(base+i*0x800+word*4,value))return false; // privring/gk104.c:28-55 detail layout.
        }
    }
    return true;
}
bool Faults::topology()
{
    Routing current{};bool continuation=false;bool hasType=false;
    for(unsigned i=0;i<64;++i) { // top/gk104.c:37.
        uint32_t word;
        if(!read(0x022700+i*4,word))return false; // top/gk104.c:45.
        if(!(word&3))continue;
        switch(word&3) {
        case 1:
            current.instance=(word&0x3c000000)>>26; // top/gk104.c:51.
            current.address=word&0x00fff000; // top/gk104.c:52.
            if(word&4){current.fault=(word&0x000003f8)>>3;current.hasFault=true;} // top/gk104.c:53-54.
            break;
        case 2:
            if(word&0x20){current.engine=(word&0x3c000000)>>26;current.hasEngine=true;} // top/gk104.c:57-58.
            if(word&0x10){current.runlist=(word&0x01e00000)>>21;current.hasRunlist=true;} // top/gk104.c:59-60.
            break;
        case 3:current.type=(word&0x7ffffffc)>>2;hasType=true;break; // top/gk104.c:67-68.
        }
        continuation=(word&0x80000000)!=0; // top/gk104.c:72.
        if(!continuation) {
            if(!hasType || routes_==64)return stop(Error::Topology); // no source: fail closed on incomplete/over-capacity descriptors.
            if(current.hasFault && current.fault>=32)return stop(Error::Topology); // fifo/gf100.c:726 covers 32 fault units.
            routing_[routes_++]=current;current={};hasType=false;
        }
    }
    if(continuation || !routes_)return stop(Error::Topology);
    return true;
}
bool Faults::capture(Phase phase,uint64_t epoch)
{
    if(!healthy())return false;
    phase_=phase;
    if(!epoch_ || epoch!=epoch_ || unsigned(phase)!=next_)return stop(Error::Order);
    if(!port_.now(start_) || start_<last_)return stop(Error::Clock);
    last_=start_;
    uint32_t mc;
    if(!read(0x000100,mc))return false; // fb/gf100.c:37 raw master status.
    if(phase==Phase::Reset) {
        if(mc)return stop(Error::Dirty);
        ++next_;return true;
    }
    uint32_t fifo,mask,priv0,priv1,hubs,rops,gpcs;
    if(!read(0x002100,fifo) || !read(0x00259c,mask))return false; // fifo/gk104.c:658; fifo/gf100.c:723.
    for(unsigned unit=0;unit<32;++unit)if(mask&(uint32_t(1)<<unit)) { // fifo/gf100.c:726.
        for(unsigned word=0;word<4;++word) {
            uint32_t value;
            if(!read(0x002800+unit*16+word*4,value))return false; // fifo/gf100.c:699-702.
        }
    }
    // privring/gk104.c:62-66 raw status and discovery counts.
    if(!read(0x120058,priv0) || !read(0x12005c,priv1)
        || !read(0x120070,hubs) || !read(0x120074,rops) || !read(0x120078,gpcs))return false; // privring/gk104.c:62-66.
    if(hubs>8 || rops>16 || gpcs>32)return stop(Error::Topology); // privring/gk104.c:69-87 status bit capacities.
    // privring/gk104.c:28-55 pending-unit detail windows.
    if(!details(priv0,0x122120,hubs,8) || !details(priv0,0x124120,rops,16)
        || !details(priv1,0x128120,gpcs,0))return false; // privring/gk104.c:28-55.
    if(mc || fifo || mask || priv0 || priv1)return stop(Error::Dirty);
    if(phase==Phase::Post && !topology())return false;
    ++next_;return true;
}
}
