// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "a7/Owner.h"
#include <cstring>
namespace k40::a7 {
Owner::Owner(Platform& platform,memory::ArmStorage& storage,const uint8_t key[32],const uint8_t nonce[32],const uint8_t challenge[16],
             const uint8_t* rom,uint32_t bytes,uint64_t expectedVram)
    :platform_(platform),arm_(storage),authority_(key,nonce,challenge),image_(rom,bytes),expectedVram_(expectedVram) {platform_.bindPermit(permit_);}
void Owner::failed()
{
    permit_.active_=false;arm_.fail();
    if(once_.state()==runtime::startup::BootState::Fresh)once_.begin();
    if(once_.state()==runtime::startup::BootState::Running)once_.finish(false);
}
bool Owner::observeClientLoad()
{
    Guard guard(lock_);if(!guard.held)return false;
    platform_.log("CLIENT_LOAD",++clientLoads_,unsigned(once_.state()));return true;
}
Status Owner::prepare(uint64_t& lease,uint8_t request[requestBytes])
{
    lease=0;Guard guard(lock_);if(!guard.held)return Status::Busy;
    platform_.log("PREPARE_CALL",prepared_?2:1,unsigned(once_.state()));
    if(prepared_ || once_.state()!=runtime::startup::BootState::Fresh)return Status::Retained;
    prepared_=true;
    uint32_t identity=0;
    if(!request || !image_.approved() || !expectedVram_ || !platform_.initialize()
        || !platform_.pciCommand(outcome_.pciBefore) || !(outcome_.pciBefore&2) || !platform_.read32(0,identity)
        || identity!=0x0f1240a1 || !arm_.prepare()) { // no source: software identity comparison; KNOWN capture hardware/record.json:37.
        failed();platform_.log("FAIL prepare",uint32_t(Status::Input));return Status::Input;
    }
    attached_=true;lease=1;authority_.request(arm_,request);
    const auto owned=arm_.allocation();platform_.log("PREPARED",owned.token,owned.physical.value);
    return Status::Ok;
}
Status Owner::submit(uint64_t lease,const uint8_t* grant,size_t bytes)
{
    Guard guard(lock_);if(!guard.held)return Status::Busy;
    if(lease!=1 || !attached_ || !prepared_ || submitted_ || once_.state()!=runtime::startup::BootState::Fresh)return Status::Retained;
    submitted_=true;
    uint8_t snapshot[grantBytes];
    if(!grant || bytes!=sizeof(snapshot)) {failed();return Status::Input;}
    std::memcpy(snapshot,grant,sizeof(snapshot));
    if(!authority_.accept(arm_,snapshot,sizeof(snapshot))) {failed();platform_.log("FAIL authentication",0);return Status::Authentication;}
    permit_.active_=true;
    struct End {Owner& owner;~End(){owner.permit_.active_=false;}} end{*this};
    outcome_.startup=controller_.run(io_,arm_,15000000); // no source: fixed software execution budget.
    permit_.active_=false;
    if(diagnostics_.recording()) {
        const auto before=platform_.nowUs();diagnostics_.flush(platform_);
        platform_.log("TRACE_DUMP_US",platform_.nowUs()-before);
    }
    if(!diagnostics_.healthy()) {
        failed();platform_.log("FAIL diagnostics",unsigned(devinit::Error::Budget));return Status::Post;
    }
    if(outcome_.startup.error!=runtime::startup::Error::None) {
        failed();platform_.log("FAIL startup",unsigned(outcome_.startup.error),unsigned(outcome_.startup.step));return Status::Post;
    }
    platform_.log("PASS ARM_ONLY_POST",outcome_.vramBytes,outcome_.startup.armAttempts);
    return Status::Ok;
}
Status Owner::detach(uint64_t lease)
{
    Guard guard(lock_);if(!guard.held)return Status::Busy;
    if(lease!=1 || !attached_)return Status::Input;
    attached_=false;
    if(once_.state()!=runtime::startup::BootState::Complete)failed();
    platform_.log("RETAINED",arm_.allocation().token,unsigned(once_.state()));
    return Status::Retained;
}
bool Owner::Transport::active() const
{ return owner_.diagnostics_.healthy() && owner_.permit_.active() && owner_.once_.state()==runtime::startup::BootState::Running; }
bool Owner::Transport::allowed(uint32_t reg,unsigned width,bool write) const
{
    if(!active())return false;
    if(phase_==Phase::Post)return owner_.image_.allow(pc_,reg,width,write);
    if(width==1)return phase_==Phase::Crtc && (reg==0x6013d4 || reg==0x6013d5); // disp/vga.c:97-107.
    if(width!=4 || (reg&3))return false;
    switch(phase_) {
    case Phase::Identity:return !write && (reg==0 || reg==0x101000); // bios/ramcfg.c:29-33; hardware/record.json.
    case Phase::Interrupts:return (reg==0x140 || reg==0x144) && (write || reg==0x140); // mc/nv04.c:87-90.
    case Phase::Decision:return !write && reg==0x02240c; // devinit/gf100.c:101.
    case Phase::Ring:return reg==0x122318 || reg==0x12231c || reg==0x122310 || reg==0x122348 || reg==0x1223b0 || reg==0x122358; // privring/gk104.c:103-109.
    case Phase::I2c:return write && i2cPin_ && reg==i2cPin_; // i2c/busgf119.c:69,93; bios/i2c.h:12.
    case Phase::Arm:return write && reg==0x100c10; // fb/gf100.c:83.
    case Phase::Fifo:return reg==0x200; // mc/nv04.c:39,47,49; mc/gk104.c:28.
    case Phase::Readback:return !write && reg==0x100c10; // fb/gf100.c:83; ESC-002 adds readback.
    case Phase::Readiness:
        if(!write && (reg==0 || reg==0x100 || reg==0x9400 || reg==0x9410 || reg==0x22438 || reg==0x2243c || reg==0x22554))return true; // timer/regsnv04.h:6-7; fb/ramgf100.c:477,502; fb/ramgf108.c:30-41; fb/gf100.c:37.
        // timer/regsnv04.h:6-7; fb/ramgf100.c:477,502; fb/ramgf108.c:30-41; fb/gf100.c:37.
        if(!write && reg>=0x11020c && reg<=0x12f20c && (reg-0x11020c)%0x1000==0)return true; // fb/ramgf100.c:467.
        if(reg==0x070000)return true; // bar/g84.c:29-40.
        if(scratchOwned_ && windowLocked_ && reg==0x1700)return write; // instmem/nv50.c:68,88.
        if(scratchOwned_ && windowLocked_ && selector_==0 && reg>=0x740000 && reg<0x741000)return true; // instmem/nv50.c:62-91; fb/ramgf100.c:497,555-558.
        return false;
    default:return false;
    }
}
bool Owner::Transport::read32(uint32_t reg,uint32_t& value)
{
    if(!allowed(reg,4,false))return false;
    const auto before=nowUs();const bool ok=owner_.platform_.read32(reg,value);
    owner_.diagnostics_.mmio(before,nowUs());if(!ok)return false;
    if(phase_==Phase::Fifo) {fifoReadValue_=value;fifoRead_=true;}
    return true;
}
bool Owner::Transport::write32(uint32_t reg,uint32_t value)
{
    if(!allowed(reg,4,true))return false;
    if(phase_==Phase::Interrupts && value)return false;
    if(phase_==Phase::I2c && value!=7)return false;
    if(phase_==Phase::Readiness && ((reg==0x1700 && value!=0) || (reg==0x70000 && value!=1)))return false; // instmem/nv50.c:68; bar/g84.c:29-40.
    if(phase_==Phase::Fifo) {
        // mc/nv04.c:39,47; mc/gk104.c:28. Only the paired FIFO bit may change.
        if(!fifoRead_ || fifoWrites_>=2 || value!=((fifoReadValue_&~0x100u)|(fifoWrites_?0x100u:0)))return false;
    }
    const auto before=nowUs();const bool ok=owner_.platform_.write32(reg,value);
    owner_.diagnostics_.mmio(before,nowUs());if(!ok)return false;
    if(phase_==Phase::Fifo) {fifoRead_=false;++fifoWrites_;}
    if(phase_==Phase::Readiness && reg==0x1700)selector_=value; // instmem/nv50.c:68.
    return true;
}
bool Owner::Transport::read8(uint32_t reg,uint8_t& value)
{
    if(!allowed(reg,1,false))return false;
    const auto before=nowUs();const bool ok=owner_.platform_.read8(reg,value);
    owner_.diagnostics_.mmio(before,nowUs());return ok;
}
bool Owner::Transport::write8(uint32_t reg,uint8_t value)
{
    if(!allowed(reg,1,true))return false;
    const auto before=nowUs();const bool ok=owner_.platform_.write8(reg,value);
    owner_.diagnostics_.mmio(before,nowUs());return ok;
}
bool Owner::Transport::delayUs(uint64_t us)
{
    if(!active() || us>1000000)return false;
    const auto before=nowUs();const bool ok=owner_.platform_.delayUs(us);
    owner_.diagnostics_.delay(us,before,nowUs());return ok;
}
void Owner::Transport::trace(uint32_t pc,uint8_t opcode,bool activeInstruction)
{pc_=pc;emit(activeInstruction?"SCRIPT_ACTIVE":"SCRIPT_SKIPPED",pc,opcode);}
void Owner::Transport::emit(const char* name,uint64_t first,uint64_t second)
{
    if(owner_.diagnostics_.recording())owner_.diagnostics_.record(name,first,second,nowUs());
    else owner_.platform_.log(name,first,second);
}
void Owner::Transport::pollSample(uint32_t pc,uint8_t index,uint32_t value,bool met)
{owner_.diagnostics_.poll(pc,index,value,met,nowUs());}
bool Owner::Transport::identity()
{
    phase_=Phase::Identity;uint32_t value=0;
    emit("PCI_COMMAND",owner_.outcome_.pciBefore);
    if(!read32(0,value) || value!=0x0f1240a1)return false; // no source: software identity comparison; KNOWN capture hardware/record.json:37.
    emit("IDENTITY",value);
    return owner_.image_.selectRam(*this)==devinit::Error::None;
}
bool Owner::Transport::unarmInterrupts(){phase_=Phase::Interrupts;return helpers_.unarmInterrupts();}
bool Owner::Transport::postRequired(bool& required){phase_=Phase::Decision;return helpers_.postRequired(required);}
bool Owner::Transport::unlockCrtc(){phase_=Phase::Crtc;return helpers_.unlockCrtc();}
bool Owner::Transport::privateRing(){phase_=Phase::Ring;return helpers_.privateRing();}
void Owner::Transport::i2cAudit(uint32_t pc,uint8_t address,uint8_t reg,uint8_t value,const devinit::I2cResult& result)
{
    emit("I2C_REQUEST",pc,(uint32_t(address)<<16)|(uint32_t(reg)<<8)|value);
    emit("I2C_DISPOSITION",result.attempt,unsigned(result.disposition));
    emit("I2C_RESULT",unsigned(result.primary),unsigned(result.cleanup));
    emit("I2C_PHASE",unsigned(result.phase),result.bit);
    emit("I2C_TIME",result.transferUs,result.cleanupUs);
    emit("I2C_WORK",result.operations,result.levels);
}
bool Owner::Transport::initializeI2c()
{
    devinit::I2cBus bus{};
    if(!owner_.post_.dedicatedBus(bus))return false;
    i2cPin_=0x00d014+uint32_t(bus.drive)*0x20; // i2c/busgf119.c:93.
    phase_=Phase::I2c;return owner_.post_.prepareI2c()==devinit::Error::None;
}
bool Owner::Transport::programFlushPage(memory::DeviceIova address)
{
    if(armWrites_>=2 || (armWrites_==1 && (!romDone_ || !readback_)))return false;
    phase_=Phase::Arm;emit(armWrites_?"ARM_AFTER":"ARM_BEFORE",address.value,address.value>>8);
    ++armWrites_;return helpers_.programFlushPage(address);
}
bool Owner::Transport::resetFifoBeforePost()
{
    phase_=Phase::Fifo;fifoWrites_=0;fifoRead_=false;
    return helpers_.resetFifoBeforePost() && fifoWrites_==2;
}
bool Owner::Transport::executeRom()
{
    phase_=Phase::Post;owner_.diagnostics_.begin(nowUs());
    const auto result=owner_.post_.runPost();owner_.diagnostics_.finishPost(nowUs());
    emit("POST_RESULT",unsigned(result.error),result.offset);
    romDone_=result.error==devinit::Error::None && diagnosticsHealthy();return romDone_;
}
bool Owner::Transport::readFlushPage(uint32_t& value)
{
    if(!romDone_ || armWrites_!=1)return false;
    phase_=Phase::Readback;readback_=read32(0x100c10,value); // fb/gf100.c:83; ESC-002 adds readback.
    if(readback_)emit("ARM_READBACK",value);
    return readback_ && diagnosticsHealthy();
}
bool Owner::Transport::timer(uint64_t& value)
{
    // timer/nv04.c:43-55; timer/regsnv04.h:6-7. Bound the rollover loop.
    for(unsigned attempt=0;attempt<32;++attempt) {
        uint32_t high=0,low=0,again=0;
        if(!read32(0x9410,high) || !read32(0x9400,low) || !read32(0x9410,again))return false; // timer/regsnv04.h:6-7; timer/nv04.c:43-55.
        if(high==again){value=(uint64_t(high)<<32)|low;return true;}
    }
    return false;
}
bool Owner::Transport::memorySize(uint64_t& bytes)
{
    // gk104 ram hook: ramgk104.c:1701-1704 -> gf108 probe -> gf100 ctor.
    uint32_t parts=0,units=0,disabled=0;
    if(!read32(0x22438,parts) || !read32(0x2243c,units) || !read32(0x22554,disabled) // fb/ramgf100.c:477,502; fb/ramgf108.c:30-41.
        || !parts || parts>32 || !units || units>32 || units%parts)return false;
    uint64_t total=0,common=0;unsigned activeParts=0;
    for(uint32_t part=0;part<parts;++part) {
        uint64_t amount=0;
        for(uint32_t sub=0;sub<units/parts;++sub) {
            const auto unit=part*(units/parts)+sub;
            if(!(disabled&(uint32_t(1)<<unit))) {
                uint32_t mib=0;
                if(!read32(0x11020c+unit*0x1000,mib) || !mib)return false; // ramgf100.c:467.
                amount+=uint64_t(mib)<<20;
            }
        }
        if(amount) {
            if(common && amount!=common)return false; // Reject mixed memory in this fixed A7 stage.
            common=amount;total+=amount;++activeParts;
        }
    }
    bytes=total;
    return activeParts && total==owner_.expectedVram_ && total>0x40000+0x100000+4096; // ramgf100.c:497-498,555-558.
}
bool Owner::Transport::independentReadiness()
{
    phase_=Phase::Readiness;auto& result=owner_.outcome_;uint32_t identity=0;
    if(!read32(0,identity) || identity!=0x0f1240a1 || !timer(result.timerBefore) // no source: software identity comparison; KNOWN capture hardware/record.json:37.
        || !delayUs(1000) || !timer(result.timerAfter) || result.timerAfter<=result.timerBefore
        || !memorySize(result.vramBytes) || !read32(0x100,result.pending) || result.pending)return false; // fb/gf100.c:37.
    emit("TIMER",result.timerBefore,result.timerAfter);
    emit("VRAM_BYTES",result.vramBytes);
    // Sole driver reservation: first page of the source-derived normal heap.
    // ramgf100.c:497-498,555-558 excludes VGA head and VBIOS tail. No other A7
    // VRAM consumer exists. Keep this reservation for the whole module lifetime.
    scratchOwned_=true;
    const uint64_t offsets[]={0,0x100,0xffc}; // no source: software scratch sample offsets within our owned page.
    result.scratch=runtime::checkOwnedScratch(*this,{{0x40000},4096},offsets,3,{2000000,100000}); // fb/ramgf100.c:497,555-558; software page size and time budgets.
    if(!result.scratch || !read32(0x100,result.pending) || result.pending)return false; // fb/gf100.c:37.
    emit("SCRATCH_PASS",0x40000,4096);return diagnosticsHealthy(); // fb/ramgf100.c:497,555-558; software scratch page reservation.
}
}
