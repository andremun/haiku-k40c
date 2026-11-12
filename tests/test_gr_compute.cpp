// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Host test of the S3 compute stage through the resident Policy and gr::Guard.
// The simulated card answers the GR registers from the Linux reference trace
// (fixture of tools/gr/program.py) and refuses any GR access that is not the
// next access of that trace. On GP_PUT it decodes the channel on its own: page
// tables, instance block, context words, push buffer, descriptor, constant
// buffer 7, and runs out[i] = in[i] + 1. HOST_ONLY, not card evidence.
#include "gr/Compute.h"
#include "gr/Guard.h"
#include "memstage/Experiment.h"
#include "memstage_device.h"
#include <cstdio>
#include <fstream>
#include <map>
#include <sstream>
#include <string>
namespace k40::memnative {struct PolicyProbe {static void aperture(Policy& p,uint64_t bytes){p.aperture(bytes);}};}
using namespace k40::memnative;
namespace ch=k40::memstage::channel;
namespace gr=k40::gr;
struct Access {char op;uint32_t addr,value;};
enum Fault {None,NoLaunch,FecsSilent,WrongSum,Stall,ReadOnlyOutput};
struct Card:Device {
    Policy* policy=nullptr;Arena* arena=nullptr;Fault fault=None;unsigned denials=0;
    std::vector<Access> trace;size_t next=0;bool follow=false,armed=false,mismatch=false,launched=false;
    std::map<uint32_t,uint32_t> regs{{0x2390,0x1},{0x2394,0x6e},{0x2398,0x10},{0x2a04,0x800003ff},{0x4013c,0xffffffff},
        {0x204,0x7},{0x200,0xe011212d}}; // trace 230517-230519, 560973, 46125.
    uint32_t runlistBase=0,entries=0;
    Card(){ram.resize(24*1024*1024);}
    uint64_t physical(Role role) const {Record r;for(unsigned i=0;i<arena->count();++i)if(arena->at(i,r) && r.role==role)return r.physical.value;assert(false);return 0;}
    uint64_t pte(uint64_t instance,uint64_t va) const {
        const auto directory=word64(instance+0x200);const auto pde=word64(directory+(va>>27)*8);
        assert(uint32_t(pde)==0 && ((pde>>32)&15)==1);
        return word64((pde>>36)*4096+((va>>12)&32767)*8);
    }
    uint64_t walk(uint64_t instance,uint64_t va,bool write=false) const {
        const auto entry=pte(instance,va);assert(entry&1);assert(!write || !(entry&4));
        return (entry>>4<<12)+(va&4095);
    }
    uint32_t at(uint64_t instance,uint64_t va) const{return ram.at(walk(instance,va)/4);}
    uint64_t bar(uint64_t offset,bool write) const {
        assert(context&0x80000000);
        const auto entry=pte(uint64_t(context&0x7fffffff)*4096,offset);
        assert((entry&1) && (!write || !(entry&4)));return (entry>>4<<12)+(offset&4095);
    }
    // Run data that the trace cannot hold: checked against the owned ledger.
    bool runData(uint32_t reg,uint32_t value) const {
        const uint64_t pool=gr::regions[7].va,bundle=gr::regions[8].va,attrib=gr::regions[9].va;
        switch(reg) {
        case 0x4188b4:return value==uint32_t(physical(Role::DebugWrite)>>8);
        case 0x4188b8:return value==uint32_t(physical(Role::DebugRead)>>8);
        case 0x409500:return value==(0x80000000|uint32_t(physical(Role::ChanInstance)>>12));
        case 0x40800c:case 0x419004:return value==uint32_t(pool>>8) || value==0;
        case 0x408004:case 0x418808:return value==uint32_t(bundle>>8) || value==0;
        case 0x418810:return value==(0x80000000|uint32_t(attrib>>12)) || value==0;
        case 0x419848:return value==(0x10000000|uint32_t(attrib>>12)) || value==0;
        default:return false;
        }
    }
    bool traced(char op,uint32_t reg,uint32_t& value) {
        if(!follow || next>=trace.size())return false;
        const auto& row=trace[next];
        if(row.op!=op || row.addr!=reg){mismatch=true;return false;}
        if(op=='W' && row.value!=value && !runData(reg,value)){mismatch=true;return false;}
        if(op=='R')value=row.value;
        ++next;return true;
    }
    bool gr(uint32_t reg) const {
        // Not the instance-memory flush and window of the hooks, and not the channel
        // and BAR1 registers of a teardown that follows a failed GR stage.
        if(reg==0x70000 || reg==0x1700 || reg==0x1704 || reg>=0x800000 || reg==0x2634 || reg==0x2270 || reg==0x2274 || reg==0x2284)return false;
        return follow && next<trace.size();
    }
    bool read32(uint32_t reg,uint32_t& value) override {
        if(!policy->read(reg,locks[0])){++denials;return false;}
        if(reg>=0x700000 && reg<0x800000)return Device::read32(reg,value);
        if(fault==FecsSilent && reg==0x409800 && follow){value=0;policy->observed(reg,value);return true;} // Never ready.
        if(reg==0x2284 && entries && !armed){armed=follow=true;value=0;policy->observed(reg,value);return true;} // Bind ends with this poll; the GR stages follow.
        if(gr(reg)){if(!traced('R',reg,value))return false;policy->observed(reg,value);return true;}
        if(reg==0x22700){value=2|0x10|0x20|0x80000000;policy->observed(reg,value);return true;} // top/gk104.c:57-60: GR, runlist 0, engine 0.
        if(reg==0x22704){value=3;policy->observed(reg,value);return true;} // top/gk104.c:67-68,78 type 0.
        if(reg==0x22708){value=2|0x10|0x20|(4u<<21)|(4u<<26)|0x80000000;policy->observed(reg,value);return true;} // CE0, runlist 4.
        if(reg==0x2270c){value=3|(1u<<2);policy->observed(reg,value);return true;}
        if(regs.count(reg) || (reg>=0x800000 && reg<0x808000) || reg==0x2634 || (reg>=0x2284 && reg<0x2304)){value=regs[reg];policy->observed(reg,value);return true;}
        const auto ok=Device::read32(reg,value);if(ok)policy->observed(reg,value);return ok;
    }
    bool write32(uint32_t reg,uint32_t value) override {
        if(!policy->write(reg,value,locks[0],locks[1])){++denials;return false;}
        if(reg==0x1700 || reg==0x70000 || (reg>=0x700000 && reg<0x800000))return Device::write32(reg,value);
        if(gr(reg)){uint32_t v=value;return traced('W',reg,v);}
        if(reg==0x100cbc && value==0x80000001){assert(locks[1] && pdbSelector);return true;}
        if(reg==0x204){regs[reg]=value==0xffffffff?0x7:value;return true;}
        if(reg==0x200){regs[reg]=value;return true;}
        if(reg==0x2270){runlistBase=value;return true;}
        if(reg==0x2274){assert((value>>20)==0);entries=value&0xfffff;return true;} // GR runlist 0.
        if(regs.count(reg) || (reg>=0x800000 && reg<0x808000) || reg==0x2634 || reg==0x2254){
            if(reg==0x800004+ch::chid*8)value&=~0xc00u;
            regs[reg]=value;return true;
        }
        return Device::write32(reg,value);
    }
    bool storeFence() override{return true;}
    bool barRead32(uint64_t offset,uint32_t& value) override {
        if(!policy->barRead(offset,locks[1])){++denials;return false;}
        value=ram.at(bar(offset,false)/4);return true;
    }
    void compute(uint64_t inst) {
        // Independent decode: nvc0_winsys.h:66-88 headers, nve4_compute.xml.h methods, cla0c0qmd.h bits.
        const auto gp=word64(inst+0x48)&0xffffffffffULL;
        const auto entry=word64(walk(inst,gp));const unsigned words=unsigned((entry>>42)&0x1fffff);
        const auto base=entry&0xffffffffffULL;std::map<uint32_t,uint32_t> m;uint32_t object=0;unsigned nonInc=0;
        assert(words==gr::pushBytes/4);
        for(unsigned i=0;i<words;) {
            const auto header=at(inst,base+i*4);++i;
            const auto op=header>>29,count=(header>>16)&0x1fff,subc=(header>>13)&7,method=(header&0xfff)<<2;
            assert(subc==1);
            if(op==4){m[method]=count;continue;}
            assert(op==1 || op==3);
            for(unsigned k=0;k<count;++k,++i) {
                const auto value=at(inst,base+i*4);const auto target=op==1?method+k*4:method;
                if(target==0)object=value;else m[target]=value;
                if(op==3){assert(value==(0x38000u|(63-k)));++nonInc;}
                if(target==0x2bc){assert(value==3 && object==0xa1c0);launch(inst,m);}
            }
        }
        assert(launched && nonInc==64);
    }
    void launch(uint64_t inst,std::map<uint32_t,uint32_t>& m) {
        // Set-up state the launch depends on (nve4_compute.c:54-120).
        assert(m[0x77c]==0xff000000 && m[0x214]==0xfe000000 && m[0x310]==0x400 && m[0x2e8]==0x408000 && m[0x2f4]==0x408000);
        const uint64_t text=(uint64_t(m[0x1608])<<32)|m[0x160c],tls=(uint64_t(m[0x790])<<32)|m[0x794];
        assert(text==gr::regions[0].va && tls==gr::regions[1].va);
        // Context: instance words 0x210/0x214, the two list words and the first list pair.
        const auto pointer=word64(inst+0x210);assert((pointer&7)==4);
        const auto image=pointer&~7ull;assert(image==gr::regions[10].va+0x80000);
        assert(at(inst,image)==gr::patchCount && at(inst,image+4)==uint32_t(gr::regions[11].va>>8));
        assert(at(inst,gr::regions[11].va)==0x40800c && at(inst,gr::regions[11].va+4)==uint32_t(gr::regions[7].va>>8));
        walk(inst,gr::regions[10].va+0xcefff,true);walk(inst,gr::regions[1].va+gr::regions[1].bytes-4,true);
        const uint64_t qmd=uint64_t(m[0x2b4])<<8;
        const auto bits=[&](unsigned high,unsigned low){uint64_t v=0;for(unsigned b=low;b<=high;++b)v|=uint64_t((at(inst,qmd+(b/32)*4)>>(b%32))&1)<<(b-low);return v;};
        const auto offset=bits(287,256),width=bits(415,384),block=bits(607,592); // cla0c0qmd.h:93 and the raster and thread fields.
        assert(bits(1503,1496)==5 && bits(1535,1528)==0x30 && bits(647,647)==1); // REGISTER_COUNT, SASS_VERSION, CONSTANT_BUFFER_VALID(7).
        const uint64_t aux=bits(959+7*64,928+7*64)|(bits(967+7*64,960+7*64)<<32); // cla0c0qmd.h:203-206.
        assert(at(inst,text+offset)==0xa0a09c80 && at(inst,text+offset+156)==0x18000000); // firmware/compute_add1.md first and last word.
        assert(at(inst,aux+0x100)==block && at(inst,aux+0x10c)==width); // nvc0_context.h:128 grid information.
        const uint64_t in=at(inst,aux+0x2a0)|(uint64_t(at(inst,aux+0x2a4))<<32),out=at(inst,aux+0x2b0)|(uint64_t(at(inst,aux+0x2b4))<<32);
        assert(at(inst,aux+0x2a8)==width*block*4 && at(inst,aux+0x2b8)==width*block*4);
        for(uint64_t i=0;i<width*block;++i)
            ram.at(walk(inst,out+i*4,fault!=ReadOnlyOutput)/4)=at(inst,in+i*4)+(fault==WrongSum && i==777?2:1);
        launched=true;
    }
    bool barWrite32(uint64_t offset,uint32_t value) override {
        if(!policy->barWrite(offset,value,locks[1])){++denials;return false;}
        const auto slot=bar(offset,true)-0x8c;ram.at((slot+0x8c)/4)=value;
        const auto inst=uint64_t(regs[0x800000+ch::chid*8]&0x7fffffff)*4096;
        assert(value==1 && entries==1 && (regs[0x800000+ch::chid*8]&0x80000000) && next==trace.size());
        assert(ram.at(uint64_t(runlistBase)*4096/4)==ch::chid && word64(inst+8)==slot);
        if(fault==Stall)return true;
        compute(inst);
        ram.at((slot+0x88)/4)=1;return true;
    }
};
static std::vector<Access> load(const char* path)
{
    std::vector<Access> rows;std::ifstream in(path);assert(in);std::string line;
    while(std::getline(in,line)) {
        std::istringstream s(line);char tag;s>>tag;
        if(tag!='R' && tag!='W')continue;
        Access a{tag,0,0};s>>std::hex>>a.addr>>a.value;rows.push_back(a);
    }
    return rows;
}
struct Result {gr::Report report;unsigned denials=0,stage=0,index=0;bool mismatch=false,closed=false,launched=false;size_t next=0;};
static bool scenario(const std::vector<Access>& trace,Fault fault,Result& out,bool dump=false,bool report=false)
{
    using namespace k40::memstage;
    Arena arena;Journal journal;Card io;io.fault=fault;io.trace=trace;io.arena=&arena;
    Faults faults(io,journal,2);Policy policy(arena,faults);io.policy=&policy;gr::Guard guard(arena,policy);
    PolicyProbe::aperture(policy,256*1048576);Upload upload(io,faults,journal,arena);Mapper mapper(io,faults,journal,arena,upload,2);
    Experiment experiment(io,faults,arena,upload,mapper,2,2,11520ULL*1048576,256*1048576);
    gr::Compute compute(io,faults,journal,arena,upload,mapper,2,fault!=NoLaunch);
    assert(experiment.run());
    policy.extend(&guard);
    const bool passed=compute.run();
    // Still refused afterwards: any GR or FIFO register, GP_PUT, interrupt enables.
    for(uint32_t reg:{0x409614u,0x400500u,0x409100u,0x2140u,0x400140u,0x000640u,0x800008u,0x2634u,0x1704u})
        assert(!policy.write(reg,1,true,true));
    assert(!policy.barWrite(ch::gpPut,1,true) && !policy.barWrite(ch::gpPut,2,true));
    out.report=compute.report();out.denials=io.denials;out.mismatch=io.mismatch;out.closed=mapper.closure()==Closure::OwnedDisabled;
    out.launched=io.launched;out.next=io.next;out.stage=guard.stage();out.index=guard.index();
    if(dump) {
        const auto& r=out.report;
        std::printf("passed=%d step=%u error=%u runner=%u@%u addr=%x value=%x expected=%x closing=%u denials=%u mismatch=%d next=%zu/%zu guard=%u/%u upload=%u mapper=%u\n",passed,unsigned(r.step),unsigned(r.error),
            unsigned(r.runner.error),r.runner.index,r.runner.addr,r.runner.value,r.runner.expected,unsigned(r.closing.error),io.denials,io.mismatch,io.next,io.trace.size(),
            guard.stage(),guard.index(),unsigned(upload.error()),unsigned(mapper.error()));
        for(unsigned i=journal.count()>6?journal.count()-6:0;i<journal.count();++i){const auto* e=journal.at(i);
            std::printf("  event phase=%u error=%u offset=%x value=%llx op=%u role=%u\n",unsigned(e->phase),unsigned(e->error),e->offset,(unsigned long long)e->value,unsigned(e->operation),e->role);}
        std::printf("allocations=%u journal=%u reads=%u writes=%u ops=%u total_us=%llu wrong=%u get=%u/%u\n",arena.count(),journal.count(),
            r.reads,r.writes,r.ops,(unsigned long long)r.totalUs,r.wrong,r.getAfter,r.putAfter);
    }
    if(report) { // The line formats of memnative/NativeOwner.cpp, for tools/memstage/evidence.py.
        const auto& g=out.report;
        std::puts("k40_mem: IO_REJECT kind=0 offset=0 value=0");
        for(unsigned i=0;i<journal.count();++i){const auto* e=journal.at(i);
            std::printf("k40_mem: EVENT phase=%u error=%u offset=%x value=%llx polls=%u elapsed=%llu operation=%u role=%u detail=%u\n",
                unsigned(e->phase),unsigned(e->error),e->offset,(unsigned long long)e->value,e->polls,(unsigned long long)e->elapsed,unsigned(e->operation),e->role,e->detail);}
        for(unsigned i=0;i<arena.count();++i){Record r;assert(arena.at(i,r));std::printf("k40_mem: ALLOCATION id=%llu role=%u physical=%llx bytes=%llu generation=%llu staged=%u referenced=%u retained=%u\n",
            (unsigned long long)r.token.id,unsigned(r.role),(unsigned long long)r.physical.value,(unsigned long long)r.bytes,(unsigned long long)r.writeGeneration,r.staged,r.referenced,r.retained);}
        std::printf("k40_mem: GR step=%u error=%u bound=%u started=%u golden=%u attached=%u submitted=%u consumed=%u computed=%u closed=%u\n",
            unsigned(g.step),unsigned(g.error),g.bound,g.started,g.golden,g.attached,g.submitted,g.consumed,g.computed,g.closed);
        std::printf("k40_mem: GR_PROGRAM ops=%u reads=%u writes=%u guard=%u/%u total_us=%llu\n",g.ops,g.reads,g.writes,guard.stage(),guard.index(),(unsigned long long)g.totalUs);
        std::printf("k40_mem: GR_FAILURE runner=%u index=%u addr=%x value=%x expected=%x closing=%u closing_index=%u\n",unsigned(g.runner.error),
            g.runner.index,g.runner.addr,g.runner.value,g.runner.expected,unsigned(g.closing.error),g.closing.index);
        std::printf("k40_mem: GR_GET after=%u/%u polls=%u us=%llu result_polls=%u result_us=%llu wrong=%u first=%u value=%x\n",g.getAfter,g.putAfter,
            g.polls,(unsigned long long)g.progressUs,g.resultPolls,(unsigned long long)g.resultUs,g.wrong,g.firstWrong,g.firstValue);
        std::printf("k40_mem: GR_STATUS mc=%x fifo=%x mmu=%x pbdma=%x hce=%x state=%x gr=%x trap=%x fecs=%x engine=%x\n",g.mc,g.fifoIntr,
            g.mmuPending,g.pbdmaIntr,g.pbdmaHce,g.state,g.grIntr,g.grTrap,g.fecsIntr,g.engineStatus);
        std::printf("k40_mem: GR_IMAGE %x %x %x %x %x %x %x %x\n",g.image[0],g.image[1],g.image[2],g.image[3],g.image[4],g.image[5],g.image[6],g.image[7]);
        std::printf("k40_mem: %s faults=0 upload=0 mapper=0 closure=2 allocations=%u journal_overflow=0\n",
            !passed?"FAIL":fault==NoLaunch?"PASS S3_GOLDEN":"PASS S3_COMPUTE",arena.count());
        std::puts("k40_mem: SUBMIT result=0 state=3\nk40_mem: RETAINED owner=2 state=3\nK40-MEM-END");
    }
    return passed;
}
int main(int argc,char** argv)
{
    assert(argc>=2);setvbuf(stdout,nullptr,_IONBF,0);
    const auto trace=load(argv[1]);Result r;
    if(argc>2 && std::string(argv[2])=="--report")return scenario(trace,argc>3?NoLaunch:None,r,false,true)?0:1;
    const bool first=scenario(trace,None,r,argc>2);
    assert(first);
    assert(r.report.golden && r.report.attached && r.report.consumed && r.report.computed && r.report.closed && r.closed);
    assert(r.launched && !r.mismatch && r.denials==0 && r.next==trace.size() && r.stage==6 && r.report.wrong==0);
    assert(scenario(trace,NoLaunch,r)); // rung 4: golden context and teardown, no submission
    assert(r.report.golden && r.report.attached && !r.report.submitted && !r.launched && r.closed && r.denials==0);
    const bool silent=scenario(trace,FecsSilent,r,argc>2);assert(!silent); // FECS never reports ready: stop, then teardown
    assert(!r.report.started && r.report.runner.error==gr::Error::Poll && r.report.runner.addr==0x409800 && r.report.closed && r.closed && !r.launched);
    assert(!scenario(trace,WrongSum,r)); // one wrong output element
    assert(r.report.consumed && !r.report.computed && r.report.wrong==1 && r.report.firstWrong==777 && r.closed);
    assert(!scenario(trace,Stall,r)); // entry never fetched
    assert(r.report.submitted && !r.report.consumed && r.closed && !r.launched);
    std::puts("GR compute stage: golden context, attach, launch and result pass through Policy and Guard; no-launch, silent FECS, wrong sum and stall cases pass; HOST_ONLY");
}
