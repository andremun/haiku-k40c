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
    if (preparing_) {
        if (write && width==4 && reg==pin_) return true;
        error_=Error::Denied; return false;
    }
    if (!active_ || !image_.allow(pc_,reg,width,write)) { error_=Error::Denied; return false; }
    return true;
}
bool BoundPost::read32(uint32_t reg, uint32_t& value)
{ return permission(reg,4,false) && (registers_.read32(reg,value) || (error_=Error::Io,false)); }
bool BoundPost::write32(uint32_t reg, uint32_t value)
{
    if (preparing_ && value!=7) { error_=Error::Denied; return false; } // nvkm/subdev/i2c/busgf119.c:69.
    return permission(reg,4,true) && (registers_.write32(reg,value) || (error_=Error::Io,false));
}
bool BoundPost::read8(uint32_t reg, uint8_t& value)
{ return permission(reg,1,false) && (ports_.read8(reg,value) || (error_=Error::Io,false)); }
bool BoundPost::write8(uint32_t reg, uint8_t value)
{ return permission(reg,1,true) && (ports_.write8(reg,value) || (error_=Error::Io,false)); }
bool BoundPost::delayUs(uint64_t us)
{
    if (!guard()) return false;
    const auto* inst=image_.layout_.instruction(pc_);
    // Dedicated bit timing is separate from script TIME/IO delays.
    bool allowed=inI2c_ && active_ && inst && inst->opcode==0x4d && (us==1 || us==5); // nvkm/subdev/i2c/bit.c:91-150.
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
    bool transferred = false;
    if (mode_==PostI2c::DedicatedPins) {
        if (!prepared_) { error_=Error::Input; return false; }
        inI2c_=true;
        transferred=i2c_.i2cWrite(bus,address,reg,value);
        inI2c_=false;
    } else transferred=ports_.i2cWrite(bus,address,reg,value);
    if (!transferred && error_==Error::None) {
        const auto result=i2c_.result();
        const auto cause=result.primary==I2cError::None?result.cleanup:result.primary;
        if (mode_==PostI2c::DedicatedPins && cause==I2cError::Clock) error_=Error::Clock;
        else if (mode_==PostI2c::DedicatedPins && cause==I2cError::Timeout) error_=Error::Timeout;
        else if (mode_==PostI2c::DedicatedPins && cause==I2cError::Budget) error_=Error::Budget;
        else error_=Error::Io;
    }
    return transferred && guard();
}
Error BoundPost::prepareI2c()
{
    if (!hostSimulation()) return Error::HardwareDisabled;
    if (mode_!=PostI2c::DedicatedPins || !image_.approved_ || image_.attempted_
        || image_.i2cPreparationAttempted_) return Error::Input;
    image_.i2cPreparationAttempted_=true;
    I2cBus bus{}; bool found=false;
    for (uint32_t i=0;i<image_.layout_.count();++i) {
        const auto* inst=image_.layout_.at(i);
        if (inst->opcode!=0x4d || !boardAllowed(approvedRomDigest(),inst->offset,inst->opcode)) continue; // bios/init.c:2246.
        I2cBus candidate;
        if (!BoardHelpers::resolveBus({image_.rom_.data(),approvedRomBytes},image_.rom_[inst->offset+1],candidate)) return Error::Input;
        if (found && (bus.index!=candidate.index || bus.type!=candidate.type || bus.drive!=candidate.drive
            || bus.share!=candidate.share || bus.aux!=candidate.aux)) return Error::Input;
        bus=candidate; found=true;
    }
    if (!found || bus.type!=0x05 || bus.share!=0xff || bus.drive>15) return Error::Input; // include/nvkm/subdev/bios/i2c.h:8,12.
    pin_=0x00d014+uint32_t(bus.drive)*0x20; // nvkm/subdev/i2c/busgf119.c:93.
    error_=Error::None; running_=preparing_=true; active_=false;
    started_=last_=registers_.nowUs();
    timeout_=100000; // no source: software preinit deadline, not a hardware timing guarantee.
    const bool initialized=i2c_.initialize(bus);
    prepared_=initialized && guard();
    preparing_=running_=false;
    return prepared_?Error::None:(error_==Error::None?Error::Io:error_);
}
Result BoundPost::runPost(Limits limits)
{
    if (!hostSimulation()) return {Error::HardwareDisabled,0,0};
    if (mode_==PostI2c::DedicatedPins && !prepared_) return {Error::Input,0,0};
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
