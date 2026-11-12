// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Host test of the S2 copy phase through the resident Policy. The simulated copy
// engine moves bytes only if the second GPFIFO entry, the object bind, the eight
// methods and the launch word decode correctly, and the destination entry is
// writable. HOST_ONLY, not card evidence.
#include "memstage_fifo.h"
#include "memstage/Experiment.h"
#include <cstdio>
namespace k40::memnative {struct PolicyProbe {static void aperture(Policy& p,uint64_t bytes){p.aperture(bytes);}};}
using k40::memstage::Progress;
struct Result {k40::memstage::ChannelReport report;unsigned step=0,denials=0,copies=0,allocations=0;bool closed=false;};
enum Fault {None,Stall,LaunchError,WrongWord,Busy,NopStall,MmuFault};
static bool scenario(Fault fault,Result& out,bool dump=false)
{
    using namespace k40::memstage;
    Arena arena;Journal journal;Fifo io;
    io.copyStall=fault==Stall;io.copyError=fault==LaunchError;io.copyWrong=fault==WrongWord;io.copyBusy=fault==Busy;
    io.stall=fault==NopStall;io.mmuFault=fault==MmuFault;
    Faults faults(io,journal,2);Policy policy(arena,faults);io.policy=&policy;
    PolicyProbe::aperture(policy,256*1048576);Upload upload(io,faults,journal,arena);Mapper mapper(io,faults,journal,arena,upload,2);
    Experiment experiment(io,faults,arena,upload,mapper,2,2,11520ULL*1048576,256*1048576);
    Channel channel(io,faults,journal,arena,upload,mapper,2,true);
    assert(experiment.run());
    const bool passed=channel.run();
    // Still forbidden: interrupt enables and clears of FIFO and copy engine, a third entry, other USERD words.
    for(uint32_t reg:{0x2140u,0x2100u,0x104904u,0x104908u,0x104f14u,0x2660u,0x800000u,0x1714u})
        assert(!policy.write(reg,0xffffffff,true,true));
    assert(!policy.barWrite(ch::gpPut,2,true) && !policy.barWrite(ch::gpPut,3,true) && !policy.barWrite(0,2,true));
    out.report=channel.report();out.step=policy.channelStep();out.denials=io.denials;out.copies=io.copies;
    out.allocations=arena.count();out.closed=mapper.closure()==Closure::OwnedDisabled;
    if(dump)dumpReport(journal,arena,faults,channel,out.step);
    // The source page still holds its pattern in every scenario.
    Record source;bool found=false;
    for(unsigned i=0;i<arena.count();++i)if(arena.at(i,source) && source.role==Role::CopySource){found=true;break;}
    assert(found);
    for(unsigned offset=0;offset<4096;offset+=4)
        assert(io.ram.at((source.physical.value+offset)/4)==Upload::pattern(source.physical.value+offset,Image::Pattern));
    return passed;
}
int main(int argc,char**)
{
    Result r;
    if(argc>1)return scenario(None,r,true)?0:1;
    assert(scenario(None,r));
    assert(r.report.progress==Progress::Consumed && r.report.copyGet==2 && r.report.copyPut==2 && r.report.copied);
    assert(r.report.engine==4 && r.copies==1 && r.step==24 && r.denials==0 && r.allocations==16 && r.closed);
    assert(!scenario(Stall,r)); // second entry not fetched: no compare, teardown still complete
    assert(r.report.copyGet==1 && !r.report.copied && r.copies==0 && r.step==24 && r.denials==0 && r.closed);
    assert(!scenario(LaunchError,r));
    assert(r.report.copyGet==2 && (r.report.ceIntr&4) && r.report.ceLaunchErr==2 && !r.report.copied && r.step==24 && r.closed);
    assert(!scenario(WrongWord,r)); // one bit differs in the destination
    assert(r.report.copyGet==2 && !r.report.copied && r.copies==1 && r.step==24 && r.denials==0 && r.closed);
    assert(!scenario(Busy,r)); // data equal, engine still busy after the bound: refused
    assert(r.report.copied && (r.report.engineStatus&0x80000000) && r.step==24 && r.closed);
    assert(!scenario(NopStall,r)); // S1 part stalls: the copy is never submitted
    assert(r.report.progress==Progress::Stalled && !r.report.copySubmitted && r.copies==0 && r.step==24 && r.closed);
    assert(!scenario(MmuFault,r));
    assert(r.report.mmuPending && r.step==24 && r.closed);
    std::puts("memory copy: S2 copy path, stall, launch error, wrong word, busy engine and fault refusal pass through Policy; HOST_ONLY");
}
