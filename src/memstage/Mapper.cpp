// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memstage/Mapper.h"
namespace k40::memstage {
using namespace memory::vram;
bool Mapper::fail(Error error,uint32_t offset,uint32_t value)
{
    if(error_==Error::None)error_=error;
    arena_.fail();journal_.append({phase_,error_,offset,value,0,last_>=start_?last_-start_:0,Operation::Failure});return false;
}
bool Mapper::tick()
{
    if(error_!=Error::None || !faults_.ready() || !arena_.healthy() || journal_.overflow())return fail(Error::Dirty);
    if(!io_.active())return fail(Error::Authority);
    if(io_.profile()!=CacheProfile::ExplicitUncached)return fail(Error::Profile);
    uint64_t now;
    if(!io_.now(now) || now<last_)return fail(Error::Clock);
    last_=now;
    if(now-start_>=30000000)return fail(Error::Budget); // no source: aggregate memory-stage software budget, microseconds.
    return true;
}
bool Mapper::read(uint32_t offset,uint32_t& value)
{
    if(!tick())return false;
    if(!io_.read32(offset,value))return fail(Error::Read,offset);
    return tick();
}
bool Mapper::write(uint32_t offset,uint32_t value)
{
    if(!tick())return false;
    if(!io_.write32(offset,value))return fail(Error::Write,offset,value);
    if(!journal_.append({phase_,Error::None,offset,value,0,last_-start_,Operation::Write}))return fail(Error::Overflow);
    return tick();
}
bool Mapper::preflight()
{
    if(prepared_ || attempted_)return fail(Error::Order);
    if(!io_.now(start_))return fail(Error::Clock);
    last_=start_;
    if(!faults_.completed(Phase::Post))return fail(Error::Order);
    uint32_t context;
    if(!read(0x001704,context))return false; // bar/gf100.c:52-58 BAR1 context.
    if(context&0x80000000)return fail(Error::Dirty,0x001704,context); // bar/gf100.c:46-58 enable field.
    prepared_=true;return true;
}
bool Mapper::stage(Phase phase)
{
    phase_=phase;upload_.phase_=phase;
    if(!faults_.capture(phase,epoch_))return fail(faults_.error());
    return tick();
}
bool Mapper::poll(uint32_t mask)
{
    const auto start=last_;
    for(unsigned i=0;i<100000;++i) { // no source: software poll-count bound.
        uint32_t value;
        if(!read(0x100c80,value))return false; // vmmgf100.c:199-224 free-slot/queued status.
        if(last_-start>=2000000)return fail(Error::Invalidate); // vmmgf100.c:198,221 2000 ms.
        if(value&mask) {
            if(!journal_.append({phase_,Error::None,0x100c80,value,i+1,last_-start,Operation::Poll}))return fail(Error::Overflow); // vmmgf100.c:199-224.
            return true;
        }
    }
    return fail(Error::Invalidate);
}
bool Mapper::invalidate()
{
    Record r;
    if(!arena_.describe(directory_,r) || !r.referenced || !r.staged)return fail(Error::Bounds);
    const auto selector=(r.physical.value>>12)<<4; // vmmgf100.c:216 VRAM target zero.
    if(selector>UINT32_MAX)return fail(Error::Bounds);
    if(!poll(0x00ff0000))return false; // vmmgf100.c:199 free slots; not general quiescence.
    return write(0x100cb8,uint32_t(selector)) // vmmgf100.c:185,216-218 this PDB only.
        && write(0x100cbc,0x80000005) // vmmgf100.c:221,230-233 PAGE_ALL|HUB_ONLY, no ALL_PDB.
        && poll(0x00008000); // vmmgf100.c:224 queued condition only.
}
bool Mapper::witness(Token first,Token second)
{
    if(!io_.loadFence())return fail(Error::Profile);
    const Token tokens[]={first,second};
    for(unsigned page=0;page<2;++page) {
        Record r;if(!arena_.describe(tokens[page],r) || !r.staged || !r.referenced)return fail(Error::Bounds);
        uint64_t fingerprint=0xcbf29ce484222325ULL; // no source: software FNV-1a evidence checksum.
        for(unsigned offset=0;offset<4096;offset+=4) { // no source: two-page finite witness extent.
            if(!tick())return false;
            uint32_t value;
            if(!io_.barRead32(uint64_t(page)*4096+offset,value))return fail(Error::Read);
            if(!tick())return false;
            if(value!=Upload::pattern(r.physical.value+offset,Image::Pattern))return fail(Error::Compare,offset,value);
            for(unsigned byte=0;byte<4;++byte){fingerprint^=uint8_t(value>>(byte*8));fingerprint*=1099511628211ULL;} // no source: software FNV-1a, no device semantics.
        }
        if(!journal_.append({phase_,Error::None,page*4096,fingerprint,0,last_-start_,Operation::Witness,uint8_t(r.role),uint8_t(Image::Pattern)}))return fail(Error::Overflow);
    }
    return true;
}
bool Mapper::update(Token target)
{
    Record r;uint64_t entry;
    if(!arena_.describe(target,r) || !r.staged || !r.referenced || !tables::pte(r.physical,entry))return fail(Error::Bounds);
    if(!arena_.tableDirty(small_) || !upload_.patch(small_,0,entry,true))return fail(upload_.error()==Error::None?Error::Bounds:upload_.error());
    return invalidate();
}
bool Mapper::run(uint64_t aperture,Token a,Token b)
{
    if(attempted_ || !prepared_ || !faults_.completed(Phase::Physical))return fail(Error::Order);
    attempted_=true;a_=a;b_=b;phase_=Phase::Tables;upload_.phase_=phase_;
    if(!tick())return false;
    for(unsigned i=0;i<2;++i) {
        Record debug;
        if(!arena_.at(i,debug) || debug.role!=(i?Role::DebugWrite:Role::DebugRead)
            || !debug.staged || !debug.referenced || !debug.retained)return fail(Error::Bounds);
    }
    uint32_t current;
    if(!read(0x001704,current))return false; // bar/gf100.c:46-58 ownership guard.
    if(current&0x80000000)return fail(Error::Dirty,0x001704,current); // bar/gf100.c:46-58.
    uint64_t dummyBase,dummyLimit;
    if(!tables::instance({4096},aperture,dummyBase,dummyLimit))return fail(Error::Bounds); // no source: software aperture validation before effects.
    LockGuard lock(io_,Lock::Mmu);
    if(!lock.held())return fail(Error::Budget);
    if(!arena_.allocate(Role::Directory,Arena::requiredBytes(Role::Directory),4096,directory_)
        || !arena_.allocate(Role::SmallTable,Arena::requiredBytes(Role::SmallTable),4096,small_)
        || !arena_.allocate(Role::Instance,Arena::requiredBytes(Role::Instance),4096,instance_))return fail(Error::Bounds); // vmmgk104.c:39-43; bar/gf100.c:93 alignment.
    if(!upload_.zero(directory_) || !upload_.zero(small_) || !upload_.zero(instance_))return fail(upload_.error());
    Record d,s,in,ar,br;
    if(!arena_.describe(directory_,d) || !arena_.describe(small_,s) || !arena_.describe(instance_,in)
        || !arena_.describe(a,ar) || !arena_.describe(b,br) || ar.role!=Role::DataA || br.role!=Role::DataB
        || !ar.staged || !br.staged)return fail(Error::Bounds);
    uint64_t pde,pa,pb,base,limit;
    if(!tables::smallDirectory(s.physical,pde) || !tables::pte(ar.physical,pa) || !tables::pte(br.physical,pb)
        || !tables::instance(d.physical,aperture,base,limit))return fail(Error::Bounds);
    if(!upload_.patch(directory_,0,pde) || !upload_.patch(small_,0,pa) || !upload_.patch(small_,8,pb)
        || !upload_.patch(instance_,0x200,base) || !upload_.patch(instance_,0x208,limit))return fail(upload_.error()); // vmmgf100.c:358-360 instance offsets.
    const Token references[]={directory_,small_,instance_,a,b};
    for(auto token:references)if(!arena_.reference(token))return fail(Error::Bounds);
    if(!arena_.candidateBar(a,{0}) || !arena_.candidateBar(b,{4096}) || !stage(Phase::Tables))return fail(Error::Dirty);
    uint32_t mode;
    if(!read(0x100c80,mode) || !write(0x100c80,mode&~uint32_t(1)) || !read(0x100c80,mode))return false; // fb/gf100.c:66-77 mode 17 preserves other fields.
    if(mode&1)return fail(Error::Profile,0x100c80,mode); // fb/gf100.c:72-73.
    if(!invalidate())return false;
    const auto inst=in.physical.value>>12; // bar/gf100.c:56.
    if(inst>=uint64_t(1)<<31)return fail(Error::Bounds); // bar/gf100.c:58 enable field must remain distinct.
    enabled_=0x80000000|uint32_t(inst);closure_=Closure::RetainedUnknown; // bar/gf100.c:58 unknown write outcome retains all objects.
    if(!write(0x001704,enabled_) || !upload_.flush() || !upload_.flush())return fail(upload_.error()==Error::None?Error::Write:upload_.error()); // bar/gf100.c:38-44,58 two-flush wait.
    if(!witness(a,b) || !stage(Phase::Mapped))return false;
    phase_=upload_.phase_=Phase::Remapped;
    if(!update(b) || !witness(b,b) || !stage(Phase::Remapped))return false;
    phase_=upload_.phase_=Phase::Restored;
    if(!update(a) || !witness(a,b) || !stage(Phase::Restored))return false;
    phase_=upload_.phase_=Phase::Disabled;
    if(!read(0x001704,current))return false; // bar/gf100.c:46-49 source-owned disable.
    if(current!=enabled_)return fail(Error::Dirty,0x001704,current); // bar/gf100.c:46-58 never restore an unknown pointer.
    if(!write(0x001704,enabled_&0x7fffffff) || !read(0x001704,current))return false; // bar/gf100.c:46-49 clear only enable.
    if(current!=(enabled_&0x7fffffff))return fail(Error::Compare,0x001704,current); // bar/gf100.c:46-49.
    closure_=Closure::OwnedDisabled;
    return stage(Phase::Disabled);
}
}
