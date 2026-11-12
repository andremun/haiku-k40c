// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memstage/Upload.h"
namespace k40::memstage {
using namespace memory::vram;
bool Upload::fail(Error e,uint32_t offset,uint32_t value)
{
    if(error_==Error::None)error_=e;
    arena_.fail();journal_.append({phase_,error_,offset,value,0,last_>=start_?last_-start_:0,Operation::Failure});return false;
}
bool Upload::allowed()
{
    if(!healthy())return false;
    if(!io_.active())return fail(Error::Authority);
    if(io_.profile()!=CacheProfile::ExplicitUncached)return fail(Error::Profile);
    if(journal_.overflow())return fail(Error::Overflow);
    return true;
}
bool Upload::begin()
{
    if(!allowed())return false;
    uint64_t now;
    if(!io_.now(now) || now<last_)return fail(Error::Clock);
    start_=last_=now;return true;
}
bool Upload::tick(uint64_t budget)
{
    if(!allowed())return false;
    uint64_t now;
    if(!io_.now(now) || now<last_)return fail(Error::Clock);
    last_=now;if(now-start_>=budget)return fail(Error::Budget);
    return true;
}
uint32_t Upload::pattern(uint64_t physical,Image image)
{
    if(image==Image::Zero)return 0;
    const auto word=uint32_t(physical>>2)^uint32_t(physical>>32)^0xa53c9e71; // no source: software address-dependent test pattern.
    return image==Image::Complement?~word:word;
}
bool Upload::address(Token t,uint64_t offset,uint64_t& out)
{
    memory::VramPhysical physical;
    if((offset&3) || !arena_.span(t,offset,4,physical))return fail(Error::Bounds);
    out=physical.value;return true;
}
bool Upload::window(uint64_t physical,uint64_t& selected)
{
    const auto base=physical&~uint64_t(0xfffff); // instmem/nv50.c:62-63.
    if(base==selected)return true;
    if(!io_.write32(0x001700,uint32_t(base>>16)))return fail(Error::Write,0x001700); // instmem/nv50.c:68.
    selected=base;
    return journal_.append({phase_,Error::None,0x001700,uint32_t(base>>16),0,last_-start_,Operation::Write}) || fail(Error::Overflow); // instmem/nv50.c:68.
}
bool Upload::flushLocked()
{
    if(!allowed() || !io_.storeFence())return fail(Error::Profile);
    if(!io_.write32(0x070000,1))return fail(Error::Write,0x070000,1); // bar/g84.c:33.
    if(!journal_.append({phase_,Error::None,0x070000,1,0,last_-start_,Operation::Write}))return fail(Error::Overflow); // bar/g84.c:33.
    uint64_t start;
    if(!io_.now(start) || start<last_)return fail(Error::Clock);
    last_=start;
    for(unsigned poll=0;poll<100000;++poll) { // no source: finite software poll cap.
        if(!tick(5000000))return false; // no source: bulk-operation budget in microseconds.
        if(last_-start>=2000000)return fail(Error::Flush); // bar/g84.c:34-37 2000 ms.
        uint32_t value=0;
        if(!io_.read32(0x070000,value))return fail(Error::Read,0x070000); // bar/g84.c:35.
        if(!tick(5000000))return false; // no source: bulk-operation budget.
        if(last_-start>=2000000)return fail(Error::Flush); // bar/g84.c:34-37.
        if(!(value&2)) {
            if(!io_.loadFence())return fail(Error::Profile);
            if(!journal_.append({phase_,Error::None,0x070000,value,poll+1,last_-start,Operation::Poll}))return fail(Error::Overflow); // bar/g84.c:35.
            return true;
        }
    }
    return fail(Error::Flush);
}
bool Upload::flush()
{
    if(!begin())return false;
    LockGuard lock(io_,Lock::Window);
    return lock.held()?flushLocked():fail(Error::Budget);
}
bool Upload::transfer(Token token,Image image,bool write,const Record* like)
{
    Record r;
    if(!arena_.describe(token,r) || !arena_.healthy())return fail(Error::Bounds);
    if(image!=Image::Zero && r.role!=Role::DataA && r.role!=Role::DataB && r.role!=Role::CopySource
        && !(like && !write && r.role==Role::CopyDest))return fail(Error::Bounds);
    if(like && (write || like->role!=Role::CopySource || like->bytes!=r.bytes))return fail(Error::Bounds);
    if(write && !arena_.dirty(token))return fail(Error::Bounds);
    uint64_t selected=UINT64_MAX;
    for(uint64_t offset=0;offset<r.bytes;offset+=4) {
        if(!tick(5000000))return false; // no source: software bulk-operation budget.
        uint64_t physical;
        if(!address(token,offset,physical) || !window(physical,selected))return false;
        const auto reg=0x700000+uint32_t(physical&0xfffff); // instmem/nv50.c:71,91.
        const auto expected=pattern(like?like->physical.value+offset:physical,image);
        if(write){if(!io_.write32(reg,expected))return fail(Error::Write,reg,expected);}
        else {
            uint32_t value=0;
            if(!io_.read32(reg,value))return fail(Error::Read,reg);
            if(value!=expected) {
                if(!like)return fail(Error::Compare,reg,value);
                // Copy result differs: record it. No error latch: teardown must still run.
                journal_.append({phase_,Error::Compare,reg,value,0,last_-start_,Operation::Failure,uint8_t(r.role),uint8_t(image)});
                return false;
            }
        }
        if(!tick(5000000))return false; // no source: software bulk-operation budget.
    }
    if(!journal_.append({phase_,Error::None,0,r.bytes,0,last_-start_,write?Operation::BulkWrite:Operation::BulkRead,uint8_t(r.role),uint8_t(image)}))return fail(Error::Overflow);
    return true;
}
bool Upload::zero(Token token)
{
    if(!begin())return false;
    LockGuard lock(io_,Lock::Window);
    if(!lock.held())return fail(Error::Budget);
    return transfer(token,Image::Zero,true) && flushLocked()
        && transfer(token,Image::Zero,false) && arena_.staged(token);
}
bool Upload::exercise(Token a,Token b)
{
    if(!begin())return false;
    Record ar,br;
    if(!arena_.describe(a,ar) || !arena_.describe(b,br) || ar.role!=Role::DataA || br.role!=Role::DataB)return fail(Error::Bounds);
    LockGuard lock(io_,Lock::Window);
    if(!lock.held())return fail(Error::Budget);
    // Both pages are completely written before either is verified. A physical
    // alias cannot pass by immediate write/read reuse. Leave the first pattern.
    const Image images[]={Image::Pattern,Image::Complement,Image::Pattern};
    for(auto image:images) {
        if(!transfer(a,image,true) || !transfer(b,image,true) || !flushLocked()
            || !transfer(a,image,false) || !transfer(b,image,false))return false;
    }
    return arena_.staged(a) && arena_.staged(b);
}
bool Upload::fill(Token source)
{
    if(!begin())return false;
    Record r;
    if(!arena_.describe(source,r) || r.role!=Role::CopySource || r.referenced)return fail(Error::Bounds);
    LockGuard lock(io_,Lock::Window);
    if(!lock.held())return fail(Error::Budget);
    return transfer(source,Image::Pattern,true) && flushLocked()
        && transfer(source,Image::Pattern,false) && arena_.staged(source);
}
bool Upload::matches(Token dest,Token source)
{
    if(!begin())return false;
    Record d,s;
    if(!arena_.describe(dest,d) || !arena_.describe(source,s) || d.role!=Role::CopyDest || s.role!=Role::CopySource)return fail(Error::Bounds);
    LockGuard lock(io_,Lock::Window);
    if(!lock.held())return fail(Error::Budget);
    return transfer(dest,Image::Pattern,false,&s);
}
bool Upload::patch(Token token,uint64_t offset,uint64_t value,bool update)
{
    if(!begin())return false;
    Record r;
    if(!arena_.describe(token,r) || r.staged==update || (offset&7) || offset>r.bytes || r.bytes-offset<8
        || (r.role!=Role::Directory && r.role!=Role::SmallTable && r.role!=Role::Instance
            && r.role!=Role::ChanDirectory && r.role!=Role::ChanSmall && r.role!=Role::ChanInstance
            && r.role!=Role::Gpfifo && r.role!=Role::Push && r.role!=Role::Runlist))return fail(Error::Bounds);
    if(update) {
        if(r.role!=Role::SmallTable || !r.referenced || !r.writeGeneration)return fail(Error::Bounds);
    } else if(!arena_.dirty(token))return fail(Error::Bounds);
    LockGuard lock(io_,Lock::Window);
    if(!lock.held())return fail(Error::Budget);
    uint64_t selected=UINT64_MAX;
    for(unsigned word=0;word<2;++word) {
        uint64_t physical;
        if(!tick(5000000) || !address(token,offset+word*4,physical) || !window(physical,selected))return false; // no source: software bulk-operation budget.
        const auto reg=0x700000+uint32_t(physical&0xfffff); // instmem/nv50.c:71.
        if(!io_.write32(reg,uint32_t(value>>(word*32))))return fail(Error::Write,reg);
    }
    if(!flushLocked())return false;
    selected=UINT64_MAX;
    for(unsigned word=0;word<2;++word) {
        uint64_t physical;uint32_t actual=0;
        if(!tick(5000000) || !address(token,offset+word*4,physical) || !window(physical,selected))return false; // no source: software bulk-operation budget.
        const auto reg=0x700000+uint32_t(physical&0xfffff); // instmem/nv50.c:91.
        if(!io_.read32(reg,actual))return fail(Error::Read,reg);
        if(actual!=uint32_t(value>>(word*32)))return fail(Error::Compare,reg,actual);
    }
    if(!arena_.staged(token))return fail(Error::Bounds);
    return journal_.append({phase_,Error::None,uint32_t(offset),value,0,last_-start_,Operation::Patch,uint8_t(r.role),0}) || fail(Error::Overflow);
}
}
