// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memory/VramArena.h"
#include <cassert>
#include <cstdio>
#include <vector>
using namespace k40::memory::vram;
namespace k40::memory::vram {
struct ArenaProbe {static bool table(Arena& a,Token t){return a.tableDirty(t);}};
}
static Probe uniform(uint32_t parts,uint32_t per) {Probe p;p.parts=p.units=parts;for(unsigned i=0;i<parts;++i)p.mib[i]=per;return p;}
int main()
{
    unsigned checks=0;
    for(unsigned parts=1;parts<=16;++parts)for(unsigned per: {4u,128u,1920u}) {
        ++checks;Arena a;const auto total=uint64_t(parts)*per*1048576;
        assert(a.configure(uniform(parts,per),total,31,9));
        // Independent free-space oracle scans page positions, not the bump formula.
        std::vector<std::pair<uint64_t,uint64_t>> used={{0,256*1024+4096},{total-1048576,total}};
        for(unsigned i=0;i<2;++i){Record r;assert(a.at(i,r));used.push_back({r.physical.value,r.physical.value+r.bytes});}
        for(auto role: {Role::Directory,Role::SmallTable,Role::Instance,Role::DataA,Role::DataB}) {
            Token t;const auto bytes=Arena::requiredBytes(role);
            uint64_t expected=0;
            for(uint64_t candidate=0;candidate<total;candidate+=4096) {
                bool overlap=false;
                for(auto [first,end]:used)overlap|=candidate<end && first<candidate+bytes;
                if(!overlap && candidate+bytes<=total){expected=candidate;break;}
            }
            assert(expected && a.allocate(role,bytes,4096,t));Record r;assert(a.describe(t,r));
            assert(r.physical.value==expected);used.push_back({expected,expected+bytes});
            k40::memory::VramPhysical address;assert(a.span(t,0,bytes,address));
            assert(!a.span(t,bytes,1,address) && !a.span(t,UINT64_MAX,8,address));
            auto stale=t;stale.epoch++;assert(!a.span(stale,0,4,address));stale=t;stale.owner++;assert(!a.describe(stale,r));
            assert(!a.reference(t));assert(a.dirty(t) && a.staged(t) && a.reference(t));
            assert(!a.dirty(t));
            if(role==Role::SmallTable){assert(ArenaProbe::table(a,t));assert(a.describe(t,r) && !r.staged);assert(a.staged(t));}
            else assert(!ArenaProbe::table(a,t));
        }
        assert(!a.configure(uniform(parts,per),total,31,10));
        a.fail();for(unsigned i=0;i<a.count();++i){Record r;assert(a.at(i,r) && r.retained);}
    }
    const auto p=uniform(6,1920);const uint64_t total=11520ULL*1048576;
    Layout layout;assert(normalLayout(p,total,layout));
    auto bad=p;bad.mib[1]--;assert(!normalLayout(bad,total-1048576,layout));
    bad=p;bad.parts=7;assert(!normalLayout(bad,total,layout));
    bad=p;bad.disabled=63;assert(!normalLayout(bad,total,layout));
    Arena partial;assert(!partial.configure(p,total,1,1,1));assert(partial.count()==1 && !partial.healthy());
    Record retained;assert(partial.at(0,retained) && retained.retained);
    Arena cap;assert(cap.configure(p,total,1,2,2));Token t;assert(!cap.allocate(Role::Instance,4096,4096,t));assert(!t.id);
    assert(cap.at(1,retained) && retained.retained);
    Arena align;assert(align.configure(p,total,1,3));assert(!align.allocate(Role::DataA,4096,3,t));
    Arena duplicate;assert(duplicate.configure(p,total,1,4));assert(!duplicate.allocate(Role::DebugRead,131072,4096,t));
    Arena wrap;assert(wrap.configure(p,total,1,5));assert(!wrap.allocate(Role::DataA,4096,uint64_t(1)<<63,t));
    Arena aligned;assert(aligned.configure(p,total,1,7));
    assert(aligned.allocate(Role::Directory,65536,65536,t));
    assert(aligned.describe(t,retained) && retained.physical.value%65536==0);
    assert(aligned.dirty(t));aligned.fail();
    assert(aligned.describe(t,retained) && !retained.staged && retained.retained);
    Arena fresh;assert(fresh.configure(p,total,1,6));assert(!fresh.describe(retained.token,retained));
    std::printf("VRAM arena: %u layout/oracle cases; stale/partial/capacity/retention checks pass; HOST_ONLY\n",checks);
}
