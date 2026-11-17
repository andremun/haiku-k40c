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
enum Fault {None,NoLaunch,FecsSilent,WrongSum,Stall,ReadOnlyOutput,BindOnly,SetupOnly,AlignedBind,PrintImage,Observe,ObserveFault,ObserveStall,Registers,RegistersStall,ReportOnly,ReportStall,NoList,NoListStall,ShortList,FullList,AlignedFull,FaultMode,JobFault};
static bool faultMode(Fault f){return f==FaultMode || f==JobFault;} // s3v: gr::Observe::Fault
static bool unlisted(Fault f){return f==NoList || f==NoListStall || f==ShortList || f==FullList;}
static uint32_t listOf(Fault f){return f==FullList?gr::allList:f==ShortList?34:unlisted(f)?0:gr::allList;}
static bool reports(Fault f){return f==ReportOnly || f==ReportStall || unlisted(f);}
static bool registers(Fault f){return f==Registers || f==RegistersStall || reports(f);}
static bool observes(Fault f){return f==Observe || f==ObserveFault || f==ObserveStall || registers(f);}
static gr::Launch launchOf(Fault f){return f==NoLaunch || f==PrintImage?gr::Launch::None:f==BindOnly || f==AlignedBind || observes(f)?gr::Launch::Bind:f==SetupOnly?gr::Launch::Setup:gr::Launch::Full;}
// Records the live progress calls; with print, in the line format of memnative/NativeOwner.cpp.
struct Live final:gr::Progress {
    std::vector<std::pair<unsigned,uint32_t>> steps;bool print=false;
    void live(gr::Step step,uint64_t us,uint32_t a,uint32_t b) override {
        steps.push_back({unsigned(step),a});
        if(print)std::printf("k40_mem: LIVE step=%u us=%llu a=%x b=%x\n",unsigned(step),(unsigned long long)us,a,b);
    }
    std::map<uint32_t,std::vector<uint32_t>> image; // printed image lines by byte offset
    void words(uint32_t offset,const uint32_t values[8]) override {
        assert(!image.count(offset));image[offset].assign(values,values+8);
        if(print)std::printf("k40_mem: IMG %x %x %x %x %x %x %x %x %x\n",offset,values[0],values[1],values[2],values[3],values[4],values[5],values[6],values[7]);
    }
    struct Group {uint32_t sample,group;std::vector<uint32_t> values;};
    std::vector<Group> groups; // observe lines in call order
    void observed(uint32_t sample,uint32_t group,uint64_t us,const uint32_t* values,unsigned count) override {
        groups.push_back({sample,group,std::vector<uint32_t>(values,values+count)});
        uint32_t v[7]{};for(unsigned i=0;i<count && i<7;++i)v[i]=values[i];
        if(print)std::printf("k40_mem: OBS n=%u g=%u us=%llu c=%u %x %x %x %x %x %x %x\n",sample,group,(unsigned long long)us,count,v[0],v[1],v[2],v[3],v[4],v[5],v[6]);
    }
};
struct Card:Device {
    Policy* policy=nullptr;Arena* arena=nullptr;Fault fault=None;unsigned denials=0;
    std::vector<Access> trace;size_t next=0;bool follow=false,armed=false,mismatch=false,launched=false,alignedSeen=false;
    std::map<uint32_t,uint32_t> regs{{0x2390,0x1},{0x2394,0x6e},{0x2398,0x10},{0x2a04,0x800003ff},{0x4013c,0xffffffff},
        {0x204,0x7},{0x200,0xe011212d}}; // trace 230517-230519, 560973, 46125.
    uint32_t runlistBase=0,entries=0;unsigned barReads=0,barReadsAfterPut=0,windowAfterPut=0;bool put=false,down=false;
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
        if(reg>=0x700000 && reg<0x800000){if(put && (!down || (reports(fault) && !unlisted(fault))))++windowAfterPut;return Device::read32(reg,value);}
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
        if(reg==0x1704 && put)down=true; // bar/gf100.c:46-49: the BAR1 context disable ends the teardown.
        if(reg==0x1700 || reg==0x70000 || (reg>=0x700000 && reg<0x800000))return Device::write32(reg,value);
        if(gr(reg)){uint32_t v=value;const bool ok=traced('W',reg,v);if(ok && reg==0x409000 && value==0x100)save();return ok;}
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
        ++barReads;if(put)++barReadsAfterPut;
        value=ram.at(bar(offset,false)/4);return true;
    }
    void compute(uint64_t inst) {
        // Independent decode: nvc0_winsys.h:66-88 headers, nve4_compute.xml.h methods, cla0c0qmd.h bits.
        const auto gp=word64(inst+0x48)&0xffffffffffULL;
        const auto entry=word64(walk(inst,gp));const unsigned words=unsigned((entry>>42)&0x1fffff);
        const auto base=entry&0xffffffffffULL;std::map<uint32_t,uint32_t> m;uint32_t object=0;unsigned nonInc=0;
        // Bind, set-up or whole job: prefixes of the same push words (work/S3DIAG/PLAN.md).
        if(fault==AlignedBind || fault==AlignedFull || faultMode(fault) || observes(fault))aligned(inst);
        assert(words==(fault==BindOnly || fault==AlignedBind || observes(fault)?gr::pushBindBytes:fault==SetupOnly?gr::pushSetupBytes:gr::pushBytes)/4);
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
        if(fault==BindOnly || fault==AlignedBind || observes(fault))assert(words==2 && object==0xa1c0 && !launched && nonInc==0 && m.empty());
        else if(fault==SetupOnly)assert(object==0xa1c0 && !launched && nonInc==64 && !m.count(0x2bc) && !m.count(0x2b4));
        else assert(launched && nonInc==64);
    }
    // work/S3DIAG/FINDINGS.md: the state Linux has at its first GR schedule, decoded on its own.
    // The context unload of the generation (engine/gr/ctxgf100.c:1497-1503): the card saves the image
    // through the channel address space at the pointer of instance + 0x210. A software pattern
    // with lines of zeros; the first 256 bytes stay 0 as in the reference image (trace 811578).
    void save() {
        const auto inst=physical(Role::ChanInstance);const auto pointer=word64(inst+0x210);
        if((pointer&7)!=4)return;
        for(uint32_t o=0x100;o<gr::imageBytes;o+=4)
            ram.at(walk(inst,(pointer&~7ull)+o,true)/4)=(o/32)%3?0x9e3779b9u*(o/4+1):0;
    }
    void aligned(uint64_t inst) {
        assert(uint32_t(word64(inst+0xe0)>>32)==0); // RAMFC 0xe4: user channel (fifo/gk104.c:98).
        const auto pointer=word64(inst+0x210);assert((pointer&7)==4);
        const auto copy=pointer&~7ull;assert(copy==gr::regions[12].va); // the channel's own image.
        assert(at(inst,copy)==(unlisted(fault) && fault!=FullList?listOf(fault):gr::patchCount) && at(inst,copy+4)==uint32_t(gr::regions[11].va>>8));
        const auto golden=gr::regions[10].va+0x80000;
        assert(at(inst,golden)!=gr::patchCount || at(inst,golden+4)!=uint32_t(gr::regions[11].va>>8)); // no list words in the generation memory
        for(uint32_t o=8;o<gr::imageBytes;o+=4)assert(at(inst,copy+o)==at(inst,golden+o));
        assert(!(pte(inst,gr::regions[4].va)&4) && (pte(inst,gr::regions[3].va)&4)); // Qmd writable (s3v), Aux read-only (vmmgf100.c:315).
        for(unsigned r:{7u,8u,11u}){const auto e=pte(inst,gr::regions[r].va);assert((e&7)==3);} // valid, PRIV, writable (vmmgf100.c:315).
        for(unsigned r:{0u,9u,10u}){const auto e=pte(inst,gr::regions[r].va);assert(!(e&2));} // no PRIV elsewhere.
        alignedSeen=true;
    }
    void launch(uint64_t inst,std::map<uint32_t,uint32_t>& m) {
        // Set-up state the launch depends on (nve4_compute.c:54-120).
        assert(m[0x77c]==0xff000000 && m[0x214]==0xfe000000 && m[0x310]==0x400 && m[0x2e8]==0x408000 && m[0x2f4]==0x408000);
        const uint64_t text=(uint64_t(m[0x1608])<<32)|m[0x160c],tls=(uint64_t(m[0x790])<<32)|m[0x794];
        assert(text==gr::regions[0].va && tls==gr::regions[1].va);
        // Context: instance words 0x210/0x214, the two list words and the first list pair.
        const auto pointer=word64(inst+0x210);assert((pointer&7)==4);
        const auto image=pointer&~7ull;assert(image==(fault==AlignedFull || faultMode(fault)?gr::regions[12].va:gr::regions[10].va+0x80000)); // s3u: the channel's own image.
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
        if(fault==JobFault) { // s3u: an MMU fault of unit 0, GR (fifo/gk104.c:474), with a software record; no output.
            regs[0x259c]=1;regs[0x2800]=uint32_t(inst>>12);regs[0x2804]=uint32_t(out);regs[0x2808]=uint32_t(out>>32);regs[0x280c]=0x102;
            launched=true;return;
        }
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
        put=true;
        if(fault==RegistersStall || fault==ReportStall || fault==NoListStall)regs[0x2640]=0x8001c001; // the engine status of the s3q run after the preempt: busy, never ends.
        if(fault==Stall || fault==ObserveStall || fault==RegistersStall || fault==ReportStall || fault==NoListStall)return true;
        if(fault==ObserveFault) { // A fault of unit 4, BAR1 (fifo/gk104.c:478), with a software fault record.
            regs[0x259c]=0x10;regs[0x2840]=uint32_t(inst>>12);regs[0x2844]=0x1000;regs[0x2848]=0;regs[0x284c]=0x82;return true;
        }
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
struct Result {gr::Report report;unsigned denials=0,stage=0,index=0;bool mismatch=false,closed=false,launched=false,aligned=false;size_t next=0;std::vector<std::pair<unsigned,uint32_t>> live;std::map<uint32_t,std::vector<uint32_t>> image;std::vector<uint32_t> golden;std::vector<Live::Group> groups;unsigned barAfterPut=0,windowAfterPut=0;std::vector<uint32_t> list;};
static bool scenario(const std::vector<Access>& trace,Fault fault,Result& out,bool dump=false,bool report=false)
{
    using namespace k40::memstage;
    Arena arena;Journal journal;Card io;io.fault=fault;io.trace=trace;io.arena=&arena;
    Faults faults(io,journal,2);Policy policy(arena,faults);io.policy=&policy;gr::Guard guard(arena,policy);
    PolicyProbe::aperture(policy,256*1048576);Upload upload(io,faults,journal,arena);Mapper mapper(io,faults,journal,arena,upload,2);
    Experiment experiment(io,faults,arena,upload,mapper,2,2,11520ULL*1048576,256*1048576);
    Live live;live.print=report;
    gr::Compute compute(io,faults,journal,arena,upload,mapper,2,launchOf(fault),&live,
        fault==AlignedBind || fault==AlignedFull || faultMode(fault) || observes(fault)?gr::Align{true,true,true,listOf(fault)}:gr::Align{},fault==PrintImage,faultMode(fault)?gr::Observe::Fault:unlisted(fault)?gr::Observe::Last:reports(fault)?gr::Observe::Report:registers(fault)?gr::Observe::Registers:observes(fault)?gr::Observe::Window:gr::Observe::None);
    assert(experiment.run());
    policy.extend(&guard);
    const bool passed=compute.run();
    // Still refused afterwards: any GR or FIFO register, GP_PUT, interrupt enables.
    for(uint32_t reg:{0x409614u,0x400500u,0x409100u,0x2140u,0x400140u,0x000640u,0x800008u,0x2634u,0x1704u})
        assert(!policy.write(reg,1,true,true));
    assert(!policy.barWrite(ch::gpPut,1,true) && !policy.barWrite(ch::gpPut,2,true));
    out.report=compute.report();out.denials=io.denials;out.mismatch=io.mismatch;out.closed=mapper.closure()==Closure::OwnedDisabled;
    out.launched=io.launched;out.next=io.next;out.stage=guard.stage();out.index=guard.index();out.live=live.steps;out.aligned=io.alignedSeen;out.image=live.image;out.groups=live.groups;out.barAfterPut=io.barReadsAfterPut;out.windowAfterPut=io.windowAfterPut;
    {const auto base=io.physical(Role::GrContext)+0x80000;out.golden.assign(io.ram.begin()+base/4,io.ram.begin()+(base+gr::imageBytes)/4);} // engine/gr/ctxgf100.c:1436 CB_RESERVED.
    {const auto l=io.physical(Role::GrMmioList)/4;out.list.assign(io.ram.begin()+l,io.ram.begin()+l+gr::patchCount*2);}
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
        if(observes(fault) || faultMode(fault))std::printf("k40_mem: GR_OBSERVE samples=%u get=%u put=%u bar=%u fault_units=%x\n",g.samples,g.windowGet,g.windowPut,g.barRead,g.faultUnits);
        std::printf("k40_mem: GR_IMAGE %x %x %x %x %x %x %x %x\n",g.image[0],g.image[1],g.image[2],g.image[3],g.image[4],g.image[5],g.image[6],g.image[7]);
        std::printf("k40_mem: %s faults=0 upload=0 mapper=0 closure=2 allocations=%u journal_overflow=0\n",
            !passed?"FAIL":fault==NoLaunch?"PASS S3_GOLDEN":fault==PrintImage?"PASS S3_IMAGE":fault==FullList?"PASS S3_FULL_LIST":fault==ShortList?"PASS S3_SHORT_LIST":unlisted(fault)?"PASS S3_NO_LIST":reports(fault)?"PASS S3_REPORT":registers(fault)?"PASS S3_REGISTERS":observes(fault)?"PASS S3_OBSERVE":fault==BindOnly || fault==AlignedBind?"PASS S3_BIND":fault==SetupOnly?"PASS S3_SETUP":"PASS S3_COMPUTE",arena.count());
        std::puts("k40_mem: SUBMIT result=0 state=3\nk40_mem: RETAINED owner=2 state=3\nK40-MEM-END");
    }
    return passed;
}
// work/S3DIAG/FINDINGS.md (s3s): the register list record equals the Linux list for the trace card:
// constants, our record addresses, and the values the golden stage read from 0x17e91c and 0x17e920.
static void listMatches(const std::vector<Access>& trace,const std::vector<uint32_t>& list)
{
    assert(list.size()==gr::patchCount*2);
    for(unsigned i=0;i<gr::patchCount;++i) {
        const auto& p=gr::patchList[i];uint32_t want=p.b;
        assert(list[2*i]==p.addr);
        if(p.slot!=gr::noSlot && p.slot<gr::InputCount) { // run inputs: page pool, bundle, attribute buffer
            const unsigned region=p.slot==gr::PagePool?7:p.slot==gr::Bundle?8:9;
            want=(uint32_t(gr::regions[region].va>>p.shift)&p.a)|p.b;
        } else if(p.slot!=gr::noSlot) { // read by the golden stage: the trace value of that register
            bool found=false;for(auto& a:trace)if(a.op=='R' && a.addr==p.addr){want=(a.value>>p.shift&p.a)|p.b;found=true;break;}
            assert(found && want);
        }
        assert(list[2*i+1]==want);
    }
}
int main(int argc,char** argv)
{
    assert(argc>=2);setvbuf(stdout,nullptr,_IONBF,0);
    const auto trace=load(argv[1]);Result r;
    if(argc>2 && std::string(argv[2])=="--report") {
        const std::string mode=argc>3?argv[3]:"";
        return scenario(trace,mode=="nolaunch"?NoLaunch:mode=="image"?PrintImage:mode=="observe"?Observe:mode=="registers"?Registers:mode=="report"?ReportOnly:mode=="nolist"?NoList:mode=="list34"?ShortList:mode=="full"?FullList:mode=="alignedfull"?AlignedFull:mode=="faultmode"?FaultMode:mode=="bind"?BindOnly:mode=="aligned"?AlignedBind:mode=="setup"?SetupOnly:None,r,false,true)?0:1;
    }
    const bool first=scenario(trace,None,r,argc>2);
    assert(first);
    assert(r.report.golden && r.report.attached && r.report.consumed && r.report.computed && r.report.closed && r.closed);
    assert(r.launched && !r.mismatch && r.denials==0 && r.next==trace.size() && r.stage==6 && r.report.wrong==0);
    listMatches(trace,r.list);
    // Live lines: every step from Route to Done in order, no failure line (step 0), the result poll.
    const auto has=[&](unsigned step){for(auto& e:r.live)if(e.first==step)return true;return false;};
    for(unsigned i=1;i<r.live.size();++i)assert(r.live[i].first>=r.live[i-1].first);
    assert(r.live.front().first==1 && r.live.back().first==15 && !has(0) && has(11) && has(12));
    for(Fault f:{BindOnly,SetupOnly}) { // work/S3DIAG/PLAN.md: a prefix is fetched, no launch, no result read
        assert(scenario(trace,f,r));
        assert(r.report.golden && r.report.attached && r.report.submitted && r.report.consumed && !r.report.computed);
        assert(!r.launched && r.closed && r.denials==0 && !r.mismatch && r.report.resultPolls==0 && has(11) && !has(12) && !has(0));
    }
    assert(scenario(trace,AlignedBind,r)); // s3e: the channel state of the Linux reference run, then the bind
    assert(r.aligned && r.report.consumed && !r.launched && r.closed && r.denials==0 && !r.mismatch && has(11) && !has(0));
    listMatches(trace,r.list);
    assert(scenario(trace,NoLaunch,r)); // rung 4: golden context and teardown, no submission
    assert(r.report.golden && r.report.attached && !r.report.submitted && !r.launched && r.closed && r.denials==0);
    assert(r.image.empty() && r.report.imageLines==0); // no image line without the print mode
    assert(scenario(trace,PrintImage,r)); // s3g: the golden image printed, no submission (work/S3DIAG/REPORT.md)
    assert(r.report.golden && r.report.attached && !r.report.submitted && !r.launched && r.closed && r.denials==0 && !r.mismatch && !has(0) && !has(11));
    {   // The printed lines hold every word of the image that is not zero, and nothing else.
        std::vector<uint32_t> printed(gr::imageBytes/4,0);uint32_t sum=0,count=0;
        for(auto& line:r.image){assert(line.first%32==0 && line.first+32<=gr::imageBytes);bool any=false;
            for(unsigned j=0;j<8;++j){printed[line.first/4+j]=line.second[j];any=any || line.second[j];}assert(any);}
        r.golden[0]=r.golden[1]=0; // the two list words are written after the print (engine/gr/gf100.c:337-338)
        assert(printed==r.golden);
        for(uint32_t word:r.golden){sum+=word;count+=word!=0;}
        assert(count>0 && r.report.imageWords==count && r.report.imageSum==sum && r.report.imageLines==r.image.size());
        bool summary=false;for(auto& e:r.live)summary=summary || (e.first==9 && e.second==count);
        assert(summary);
    }
    assert(r.groups.empty()); // no observe line without the observe mode
    assert(scenario(trace,Observe,r)); // s3o: no BAR1 access after GP_PUT until the last action (work/S3DIAG/REPORT.md, approach B)
    assert(r.aligned && r.report.consumed && r.report.barRead && r.report.samples==2 && r.report.faultUnits==0 && r.closed && r.denials==0 && !r.mismatch && !has(0));
    assert(r.barAfterPut==2 && r.report.windowGet==1 && r.report.windowPut==1); // GP_GET and GP_PUT once, at the end
    {   // Baseline, two samples, then the BAR1 pair: groups 1, 2, 3 for each sample.
        const unsigned wanted[][2]={{0,1},{0,2},{0,3},{1,1},{1,2},{1,3},{2,1},{2,2},{2,3},{2,5},{2,6}};
        assert(r.groups.size()==11);
        for(unsigned i=0;i<11;++i)assert(r.groups[i].sample==wanted[i][0] && r.groups[i].group==wanted[i][1]);
        assert(r.groups[2].values==std::vector<uint32_t>({0,0}) && r.groups[5].values==std::vector<uint32_t>({1,1}));
        assert(r.groups[0].values.size()==7 && r.groups[1].values.size()==3 && r.groups[10].values==std::vector<uint32_t>({1,1}));
    }
    assert(!scenario(trace,ObserveFault,r)); // an MMU fault of unit BAR1: its record is read once, and BAR1 is not read again
    assert(r.report.submitted && !r.report.consumed && !r.report.barRead && r.barAfterPut==0 && r.report.faultUnits==0x10 && r.report.mmuPending==0x10);
    assert(r.report.closed && r.closed && r.denials==0 && r.report.samples==32);
    {   unsigned records=0;
        for(auto& g:r.groups)if(g.group==4){++records;assert(g.sample==1 && g.values==std::vector<uint32_t>({4,r.groups[0].values.empty()?0:g.values[1],0x1000,0,0x82}));}
        assert(records==1);
        for(auto& g:r.groups)assert(g.group!=5 && g.group!=6);
    }
    assert(!scenario(trace,ObserveStall,r)); // entry never fetched, no fault: every sample, then the BAR1 pair
    assert(r.report.submitted && !r.report.consumed && r.report.barRead && r.barAfterPut==2 && r.report.samples==32 && r.report.windowGet==0 && r.closed && r.denials==0);
    assert(scenario(trace,Registers,r)); // s3p: registers only after GP_PUT until the teardown ended (approach F)
    assert(r.aligned && r.report.consumed && !r.report.barRead && r.barAfterPut==0 && r.windowAfterPut==0 && r.report.samples==4);
    assert(r.report.closed && r.closed && r.denials==0 && !r.mismatch && !has(0) && r.report.windowGet==1 && r.report.windowPut==1);
    {   // Baseline with the slow window, four samples of four groups, then group 9 and the last read.
        std::vector<std::pair<unsigned,unsigned>> wanted{{0,1},{0,2},{0,7},{0,8},{0,3}};
        for(unsigned n=1;n<=4;++n)for(unsigned g:{1u,2u,7u,8u})wanted.push_back({n,g});
        wanted.push_back({4,9});wanted.push_back({4,3});
        assert(r.groups.size()==wanted.size());
        for(unsigned i=0;i<wanted.size();++i)assert(r.groups[i].sample==wanted[i].first && r.groups[i].group==wanted[i].second);
        assert(r.groups[2].values.size()==7 && r.groups[3].values.size()==4 && r.groups.back().values==std::vector<uint32_t>({1,1}));
    }
    assert(!scenario(trace,RegistersStall,r)); // the load never ends: every sample, the teardown, then the last read
    assert(r.report.submitted && !r.report.consumed && r.report.samples==32 && r.barAfterPut==0 && r.windowAfterPut==0);
    assert(r.report.closed && r.closed && r.denials==0 && r.report.windowGet==0 && r.groups.back().group==3 && r.groups.back().values==std::vector<uint32_t>({0,1}));
    assert(scenario(trace,ReportOnly,r)); // s3q: no read of VRAM after GP_PUT, also after the teardown (approach G)
    assert(r.aligned && r.report.submitted && !r.report.consumed && !r.report.barRead && r.barAfterPut==0 && r.windowAfterPut==0 && r.report.samples==4);
    assert(r.report.closed && r.closed && r.denials==0 && !r.mismatch && !has(0) && r.groups.size()==5+5*4);
    assert(r.groups.back().sample==5 && r.groups.back().group==8 && r.groups.back().values.size()==7);
    assert(r.groups.back().values[6] && !(r.groups.back().values[6]&0x80000000)); // BAR1 context after the teardown: enable clear (bar/gf100.c:46-49)
    assert(r.groups[8].values[6]&0x80000000); // and set before it (bar/gf100.c:58)
    assert(!scenario(trace,ReportStall,r)); // the engine never idle: every sample, the teardown, one more sample, a report
    assert(r.report.submitted && r.report.samples==32 && r.barAfterPut==0 && r.windowAfterPut==0 && r.report.closed && r.closed && r.denials==0);
    assert(r.groups.back().sample==33 && r.report.engineStatus==0x8001c001);
    assert(scenario(trace,NoList,r)); // s3r: list count 0, then one slow-window read after the teardown (approach H)
    assert(r.aligned && r.report.consumed && r.barAfterPut==0 && r.windowAfterPut==0 && r.report.closed && r.closed && r.denials==0 && !r.mismatch && !has(0));
    assert(r.groups.size()==5+5*4+2 && r.groups.back().group==3 && r.groups.back().values==std::vector<uint32_t>({1,1}) && r.groups[r.groups.size()-2].group==9);
    {bool count=false;for(auto& e:r.live)count=count || (e.first==10 && e.second==2);assert(count);}
    assert(scenario(trace,ShortList,r)); // s3s: the first 34 list entries (all but the LTC pair)
    assert(r.aligned && r.report.consumed && r.barAfterPut==0 && r.windowAfterPut==0 && r.report.closed && r.closed && r.denials==0 && !r.mismatch && !has(0));
    {bool count=false;for(auto& e:r.live)count=count || (e.first==10 && e.second==2);assert(count);}
    assert(scenario(trace,FullList,r)); // s3t: the whole list, its LTC entries written after the golden stage
    assert(r.aligned && r.report.consumed && r.barAfterPut==0 && r.windowAfterPut==0 && r.report.closed && r.closed && r.denials==0 && !r.mismatch && !has(0));
    listMatches(trace,r.list);
    assert(scenario(trace,AlignedFull,r)); // s3u: the channel set-up of s3e, the whole fixed list, then the compute job
    assert(r.aligned && r.launched && r.report.consumed && r.report.computed && r.report.wrong==0 && r.report.closed && r.closed);
    assert(r.denials==0 && !r.mismatch && !has(0) && has(11) && has(12) && r.groups.empty());
    listMatches(trace,r.list);
    assert(scenario(trace,FaultMode,r)); // s3v without a fault: the baseline sample only, then the job as s3u
    assert(r.aligned && r.launched && r.report.computed && r.report.wrong==0 && r.report.samples==0 && r.report.faultUnits==0 && r.closed && r.denials==0 && !r.mismatch && !has(0));
    assert(r.groups.size()==3 && r.groups[2].group==3 && r.groups[2].values==std::vector<uint32_t>({0,0}));
    assert(!scenario(trace,JobFault,r)); // s3v with a fault of GR: one sample with the record, the compare, then the teardown
    assert(r.launched && r.report.consumed && !r.report.computed && r.report.wrong==gr::elements && r.report.samples==1 && r.report.faultUnits==1);
    assert(r.report.resultPolls==0 && r.report.closed && r.closed && r.denials==0 && !has(0));
    {   unsigned records=0;
        for(auto& g:r.groups)if(g.group==4){++records;assert(g.sample==1 && g.values.size()==5 && g.values[0]==0 && g.values[4]==0x102);}
        assert(records==1 && r.groups.back().group==3 && r.groups.back().values==std::vector<uint32_t>({1,1}));
    }
    assert(!scenario(trace,NoListStall,r)); // the engine never idle and the entry never fetched
    assert(r.report.submitted && !r.report.consumed && r.report.samples==32 && r.barAfterPut==0 && r.windowAfterPut==0 && r.report.closed && r.closed && r.denials==0);
    assert(r.groups.back().group==3 && r.groups.back().values==std::vector<uint32_t>({0,1}));
    const bool silent=scenario(trace,FecsSilent,r,argc>2);assert(!silent); // FECS never reports ready: stop, then teardown
    assert(!r.report.started && r.report.runner.error==gr::Error::Poll && r.report.runner.addr==0x409800 && r.report.closed && r.closed && !r.launched);
    assert(has(0) && !has(11)); // the failed step is printed at once (step 0: a = step, b = error)
    assert(!scenario(trace,WrongSum,r)); // one wrong output element
    assert(r.report.consumed && !r.report.computed && r.report.wrong==1 && r.report.firstWrong==777 && r.closed);
    assert(!scenario(trace,Stall,r)); // entry never fetched
    assert(r.report.submitted && !r.report.consumed && r.closed && !r.launched);
    unsigned polls=0;for(auto& e:r.live)if(e.first==11 && e.second==0)++polls;
    assert(polls>=2); // GP_PUT line, then GP_GET 0 each 100 ms of the stall
    std::puts("GR compute stage: golden context, attach, launch and result pass through Policy and Guard; no-launch, image print, bind-only, aligned bind, observed bind (pass, BAR1 fault, stall), register-only bind (pass, stall), report bind (pass, stall), no-list bind (pass, stall), 34-entry list bind, full-list bind, set-up-only, silent FECS, wrong sum and stall cases pass; live lines checked; HOST_ONLY");
}
