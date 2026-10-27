// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "devinit/BoundPost.h"
namespace k40::devinit {
bool BoundPost::guard()
{
    if (error_ != Error::None) return false;
    if (!running_ || !hostSimulation()) { error_=Error::HardwareDisabled; return false; }
    const auto now=registers_.nowUs();
    if (now<last_) { error_=Error::Clock; return false; }
    last_=now;
    if (now-started_>=timeout_) { error_=Error::Timeout; return false; }
    return true;
}
bool BoundPost::permission(uint32_t reg, unsigned width, bool write)
{
    if (!guard()) return false;
    if (!active_ || !image_.allow(pc_,reg,width,write)) { error_=Error::Denied; return false; }
    return true;
}
bool BoundPost::read32(uint32_t reg, uint32_t& value)
{ return permission(reg,4,false) && (registers_.read32(reg,value) || (error_=Error::Io,false)); }
bool BoundPost::write32(uint32_t reg, uint32_t value)
{ return permission(reg,4,true) && (registers_.write32(reg,value) || (error_=Error::Io,false)); }
bool BoundPost::read8(uint32_t reg, uint8_t& value)
{ return permission(reg,1,false) && (ports_.read8(reg,value) || (error_=Error::Io,false)); }
bool BoundPost::write8(uint32_t reg, uint8_t value)
{ return permission(reg,1,true) && (ports_.write8(reg,value) || (error_=Error::Io,false)); }
bool BoundPost::delayUs(uint64_t us)
{
    if (!guard()) return false;
    const auto* inst=image_.layout_.instruction(pc_);
    bool allowed=false;
    if (inst) {
        const auto* bytes=image_.rom_.data()+pc_;
        if (inst->opcode==0x69) allowed=us==10000; // bios/init.c:1644,1649.
        if (inst->opcode==0x56) allowed=active_ && us==20000; // bios/init.c:1246-1253.
        if (inst->opcode==0x74) { // bios/init.c:1769-1782.
            uint64_t expected=uint32_t(bytes[1])|(uint32_t(bytes[2])<<8);
            if (expected>=1000) expected=((expected+900)/1000)*1000;
            allowed=active_ && us==expected;
        }
    }
    if (!allowed) { error_=Error::Denied; return false; }
    return (registers_.delayUs(us) || (error_=Error::Io,false)) && guard();
}
void BoundPost::trace(uint32_t pc, uint8_t op, bool active)
{
    const auto* inst=image_.layout_.instruction(pc);
    if (!inst || inst->opcode!=op) { error_=Error::Denied; return; }
    pc_=pc; active_=active;
    if (guard()) registers_.trace(pc,op,active);
}
bool BoundPost::board(uint8_t op, uint32_t pc, const uint8_t* bytes, uint32_t length, bool active)
{
    if (!guard()) return false;
    const auto* inst=image_.layout_.instruction(pc);
    if (!inst || pc!=pc_ || op!=inst->opcode || length!=inst->bytes || active!=active_
        || bytes!=image_.rom_.data()+pc || !boardAllowed(approvedRomDigest(),pc,op)) error_=Error::Denied;
    else {
        const auto helper=helpers_.execute({image_.rom_.data(),approvedRomBytes},bytes,length,active);
        if (error_==Error::None) error_=helper;
    }
    ports_.audit(pc,op,active,error_);
    return error_==Error::None;
}
bool BoundPost::i2cWrite(const I2cBus& bus, uint8_t address, uint8_t reg, uint8_t value)
{
    if (!guard() || !active_) return false;
    const auto* inst=image_.layout_.instruction(pc_);
    if (!inst || inst->opcode!=0x4d || !boardAllowed(approvedRomDigest(),pc_,inst->opcode)) { // bios/init.c:2246.
        error_=Error::Denied; return false;
    }
    const auto* bytes=image_.rom_.data()+pc_;
    I2cBus expected;
    bool allowed=BoardHelpers::resolveBus({image_.rom_.data(),approvedRomBytes},bytes[1],expected)
        && bus.index==expected.index && bus.type==expected.type && bus.drive==expected.drive
        && bus.share==expected.share && bus.aux==expected.aux && address==(bytes[2]>>1);
    bool pair=false;
    for (unsigned i=0;i<bytes[3];++i) if (reg==bytes[4+2*i] && value==bytes[5+2*i]) pair=true;
    if (!allowed || !pair) { error_=Error::Denied; return false; }
    return (ports_.i2cWrite(bus,address,reg,value) || (error_=Error::Io,false)) && guard();
}
Result BoundPost::runPost(Limits limits)
{
    if (!hostSimulation()) return {Error::HardwareDisabled,0,0};
    if (!image_.approved_ || !image_.selected_) return {Error::Input,0,0};
    if (image_.attempted_ || !limits.steps || !limits.depth || !limits.timeoutUs) return {Error::Input,0,0};
    image_.attempted_=true;
    running_=true; active_=false; pc_=0; error_=Error::None;
    started_=last_=registers_.nowUs(); timeout_=limits.timeoutUs;
    Result total;
    for (uint32_t i=0;i<image_.roots();++i) {
        if (!guard()) { total.error=error_; break; }
        if (total.steps>=limits.steps) { total.error=Error::Budget; break; }
        Limits remaining{limits.steps-total.steps,limits.depth,timeout_-(last_-started_)};
        auto result=Interpreter(image_.rom_.data(),approvedRomBytes,image_.layout_.tables(image_.group_),*this)
            .run(image_.root(i),remaining,1);
        total.steps+=result.steps; total.offset=result.offset;
        total.error=error_!=Error::None?error_:result.error;
        if (total.error!=Error::None) break;
    }
    running_=false;
    return total;
}
}
