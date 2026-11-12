// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "gr/Runner.h"
namespace k40::gr {
namespace {
constexpr uint64_t waitUs=2000000; // engine/gr/gf100.c:1053 and nvkm_msec(device, 2000, ...) at engine/gr/gf100.c:1123,1869: 2000 ms.
constexpr uint32_t maxPolls=20000000; // no source: software poll-count bound above the time bound.
}
bool Runner::fail(Error error,uint32_t index,uint32_t addr,uint32_t value,uint32_t expected)
{
    if(failure_.error==Error::None)failure_={error,index,addr,value,expected};
    return false;
}
bool Runner::read(uint32_t index,uint32_t addr,uint32_t& value)
{
    value=0;
    if(!port_.read32(addr,value))return fail(Error::Read,index,addr);
    ++reads_;return true;
}
bool Runner::write(uint32_t index,uint32_t addr,uint32_t value)
{
    if(!port_.write32(addr,value))return fail(Error::Write,index,addr,value);
    ++writes_;return true;
}
bool Runner::poll(uint32_t index,const Op& op)
{
    uint64_t start,now;uint32_t value=0;
    if(!port_.now(start))return fail(Error::Clock,index);
    for(uint32_t i=0;i<maxPolls;++i) {
        if(!read(index,op.addr,value))return false;
        if((value&op.a)==op.b)return true;
        if(!port_.now(now) || now<start)return fail(Error::Clock,index);
        if(now-start>=waitUs)break;
    }
    return fail(Error::Poll,index,op.addr,value,op.b);
}
bool Runner::waitIdle(uint32_t index)
{
    // gf100_gr_wait_idle (engine/gr/gf100.c:1049-1075). The engine status is that of the GR
    // engine, 0x002640 in the reference run (fifo/gk104.c:206; mmiotrace line 616724).
    uint64_t start,now;
    if(!port_.now(start))return fail(Error::Clock,index);
    for(uint32_t i=0;i<maxPolls;++i) {
        uint32_t unused,enable,status,busy;
        if(!read(index,0x400700,unused) || !read(index,0x000200,enable) // engine/gr/gf100.c:1061,1063.
            || !read(index,0x002640,status) || !read(index,0x40060c,busy))return false; // fifo/gk104.c:206; engine/gr/gf100.c:1065.
        const bool enabled=enable&0x1000; // engine/gr/gf100.c:1063.
        const bool switching=(status&0x80000000) && (status&0x00008000); // fifo/gk104.c:208,212,261-263.
        if(!enabled || (!(busy&1) && !switching))return true; // engine/gr/gf100.c:1065,1067.
        if(!port_.now(now) || now<start)return fail(Error::Clock,index);
        if(now-start>=waitUs)return fail(Error::Idle,index,0x40060c,busy); // engine/gr/gf100.c:1065,1069.
    }
    return fail(Error::Idle,index);
}
uint32_t Runner::patchValue(const Patch& patch) const
{
    if(patch.slot==noSlot)return patch.b;
    return (uint32_t(slots_[patch.slot&(maxSlots-1)]>>patch.shift)&patch.a)|patch.b;
}
bool Runner::run(const Stage& stage)
{
    if(failed())return fail(Error::Order,0);
    if(slotCount>maxSlots)return fail(Error::Program,0);
    for(uint32_t i=0;i<stage.count;++i) {
        const Op& op=stage.ops[i];uint32_t value=0;
        const bool slotted=op.slot!=noSlot;
        if(slotted && op.slot>=maxSlots)return fail(Error::Program,i);
        switch(op.kind) {
        case Kind::Write:if(!write(i,op.addr,op.a))return false;break;
        case Kind::WriteSlot:
            if(!slotted || op.shift>=64)return fail(Error::Program,i);
            if(!write(i,op.addr,(uint32_t(slots_[op.slot]>>op.shift)&op.a)|op.b))return false;
            break;
        case Kind::Read:
            if(!slotted)return fail(Error::Program,i);
            if(!read(i,op.addr,value))return false;
            slots_[op.slot]=value;break;
        case Kind::Expect:
            if(!read(i,op.addr,value))return false;
            if((value&op.a)!=op.b)return fail(Error::Expect,i,op.addr,value,op.b);
            break;
        case Kind::Mask:
            if(!read(i,op.addr,value) || !write(i,op.addr,(value&~op.a)|op.b))return false;
            if(slotted)slots_[op.slot]=value;
            break;
        case Kind::MaskSlot:
            if(!slotted)return fail(Error::Program,i);
            if(!read(i,op.addr,value) || !write(i,op.addr,(value&~op.a)|uint32_t(slots_[op.slot])))return false;
            break;
        case Kind::Poll:if(!poll(i,op))return false;break;
        case Kind::WaitIdle:if(!waitIdle(i))return false;break;
        case Kind::Delay:if(!port_.delay(op.a))return fail(Error::Delay,i);break;
        case Kind::Hook:if(!port_.hook(op.a))return fail(Error::Hook,i,0,op.a);break;
        default:return fail(Error::Program,i);
        }
        ++done_;
    }
    return true;
}
}
