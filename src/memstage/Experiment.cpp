// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memstage/Experiment.h"
namespace k40::memstage {
using namespace memory::vram;
bool Experiment::discover()
{
    if(!io_.read32(0x22438,probe_.parts))return false; // ramgf108.c:30.
    known_|=1;
    if(!io_.read32(0x2243c,probe_.units))return false; // ramgf108.c:31.
    known_|=2;
    if(!io_.read32(0x22554,probe_.disabled))return false; // ramgf100.c:477.
    known_|=4;
    if(!probe_.parts || !probe_.units || probe_.parts>32 || probe_.units>32 || probe_.units%probe_.parts)return false;
    for(unsigned unit=0;unit<probe_.units;++unit)if(!(probe_.disabled&(uint32_t(1)<<unit))) {
        if(!io_.read32(0x11020c+unit*0x1000,probe_.mib[unit]))return false; // ramgf100.c:467.
        known_|=uint64_t(1)<<(unit+3);
    }
    return true;
}
bool Experiment::work()
{
    if(!io_.active() || io_.profile()!=CacheProfile::ExplicitUncached)return false;
    step_=Step::Discovery;if(!discover())return false;
    step_=Step::Arena;if(!arena_.configure(probe_,vram_,owner_,epoch_))return false;
    if(arena_.begin()!=256*1024+4096 || arena_.end()!=vram_-1048576)return false; // ramgf100.c:497-498; no source: extra A7 scratch exclusion matches signed binding.
    step_=Step::Baselines;
    if(!faults_.capture(Phase::Reset,epoch_) || !faults_.capture(Phase::Post,epoch_))return false;
    step_=Step::Preflight;if(!mapper_.preflight())return false;
    step_=Step::Debug;
    for(unsigned i=0;i<2;++i) {
        Record debug;if(!arena_.at(i,debug) || !upload_.zero(debug.token) || !arena_.reference(debug.token))return false;
    }
    step_=Step::Data;Token a,b;
    if(!arena_.allocate(Role::DataA,4096,4096,a) || !arena_.allocate(Role::DataB,4096,4096,b)
        || !upload_.exercise(a,b) || !faults_.capture(Phase::Physical,epoch_))return false; // no source: finite two-page software witness.
    step_=Step::Tables;
    return mapper_.run(aperture_,a,b) && mapper_.closure()==Closure::OwnedDisabled;
}
bool Experiment::run()
{
    if(attempted_)return false;
    attempted_=true;const bool passed=work();if(!passed)arena_.fail();return passed;
}
}
