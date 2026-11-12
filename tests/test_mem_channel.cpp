// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Host test of the S1 channel phase through the resident Policy. The simulated
// FIFO advances GP_GET only if the encoded RAMFC, channel page tables, GPFIFO
// entry and push-buffer NOP decode correctly. HOST_ONLY, not card evidence.
#include "memstage_fifo.h"
#include "memstage/Experiment.h"
#include <cstdio>
namespace k40::memnative {struct PolicyProbe {static void aperture(Policy& p,uint64_t bytes){p.aperture(bytes);}};}
static bool scenario(bool stall,bool mmuFault,k40::memstage::ChannelReport& report,unsigned& step,unsigned& denials,bool dump=false)
{
    using namespace k40::memstage;
    Arena arena;Journal journal;Fifo io;io.stall=stall;io.mmuFault=mmuFault;
    Faults faults(io,journal,2);Policy policy(arena,faults);io.policy=&policy;
    PolicyProbe::aperture(policy,256*1048576);Upload upload(io,faults,journal,arena);Mapper mapper(io,faults,journal,arena,upload,2);
    Experiment experiment(io,faults,arena,upload,mapper,2,2,11520ULL*1048576,256*1048576);
    Channel channel(io,faults,journal,arena,upload,mapper,2);
    assert(experiment.run());
    // Forbidden in the channel phase: interrupt enables and clears, other channels, BAR2.
    const bool passed=channel.run();
    for(uint32_t reg:{0x2140u,0x2100u,0x40108u,0x4010cu,0x800000u,0x800010u,0x1714u,0x100c10u})
        assert(!policy.write(reg,0xffffffff,true,true));
    assert(!policy.barWrite(ch::gpPut,1,true) && !policy.barWrite(0,1,true));
    assert(!policy.read(bar0View,false) && !policy.write(bar0View,0,true,true)); // beyond the BAR0 view
    report=channel.report();step=policy.channelStep();denials=io.denials;
    assert(mapper.closure()==Closure::OwnedDisabled);
    if(dump)dumpReport(journal,arena,faults,channel,step);
    return passed;
}
int main(int argc,char**)
{
    k40::memstage::ChannelReport r;unsigned step=0,denials=0;
    if(argc>1)return scenario(false,false,r,step,denials,true)?0:1;
    assert(scenario(false,false,r,step,denials));
    assert(r.progress==k40::memstage::Progress::Consumed && r.getAfter==1 && r.putAfter==1 && r.closed);
    assert(r.runlist==4 && r.pbdma==2 && r.pbdmaMask==7 && step==24 && denials==0);
    assert(!scenario(true,false,r,step,denials));
    assert(r.progress==k40::memstage::Progress::Stalled && r.getAfter==0 && r.closed && step==24 && denials==0);
    assert(!scenario(false,true,r,step,denials));
    assert(r.progress==k40::memstage::Progress::Consumed && r.mmuPending && r.closed && step==24);
    std::puts("memory channel: S1 NOP path, stall teardown and fault refusal pass through Policy; HOST_ONLY");
}
