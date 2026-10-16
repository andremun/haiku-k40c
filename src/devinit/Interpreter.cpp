// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#include "devinit/Interpreter.h"

namespace k40::devinit {
bool Interpreter::span(uint64_t offset, uint64_t bytes)
{
    if (offset > size_ || bytes > size_ - offset) { result_.error=Error::Bounds; return false; }
    return true;
}
uint32_t Interpreter::word(uint64_t offset, uint32_t bytes)
{
    if (!span(offset,bytes)) return 0;
    uint32_t value=0;
    for (uint32_t i=0;i<bytes;++i) value |= uint32_t(rom_[offset+i]) << (i*8);
    return value;
}
bool Interpreter::read(uint32_t reg,uint32_t& value)
{
    value=0;
    if (!active()) return true;
    if (!backend_.read32(reg,value)) { result_.error=Error::Io; return false; }
    return true;
}
bool Interpreter::write(uint32_t reg,uint32_t value)
{
    if (!active()) return true;
    if (!backend_.write32(reg,value)) { result_.error=Error::Io; return false; }
    return true;
}
bool Interpreter::masked(uint32_t reg,uint32_t keep,uint32_t value)
{
    uint32_t old=0;
    return read(reg,old) && write(reg,(old & keep) | value);
}
bool Interpreter::condition(uint8_t index,bool& met)
{
    met=false;
    if (!tables_.conditions) return true;
    const uint64_t entry=uint64_t(tables_.conditions)+uint64_t(index)*12;
    if (!span(entry,12)) return false;
    uint32_t value=0;
    if (!read(word(entry,4),value)) return false;
    met=(value & word(entry+4,4))==word(entry+8,4);
    return true;
}
bool Interpreter::deadline()
{
    uint64_t now=backend_.nowUs();
    if (now<last_) { result_.error=Error::Clock; return false; }
    last_=now;
    if (now-started_>=limits_.timeoutUs) { result_.error=Error::Timeout; return false; }
    return true;
}
Result Interpreter::run(uint32_t start,Limits limits,uint8_t flags)
{
    result_={}; limits_=limits; flags_=flags;
    if (!rom_ || !size_ || !start || !limits.steps || !limits.depth || !limits.timeoutUs || (flags & ~7)) {
        result_.error=Error::Input; return result_;
    }
    if (!backend_.hostSimulation()) { result_.error=Error::HardwareDisabled; return result_; }
    started_=last_=backend_.nowUs();
    execute(start,1,false);
    return result_;
}
Interpreter::Stop Interpreter::execute(uint32_t& pc,uint32_t depth,bool repeatBody)
{
    if (depth>limits_.depth) { result_.error=Error::Depth; return Stop::Failed; }
    for (;;) {
        result_.offset=pc;
        if (result_.steps>=limits_.steps) { result_.error=Error::Budget; return Stop::Failed; }
        ++result_.steps;
        if (!deadline() || !span(pc,1)) return Stop::Failed;
        const uint8_t op=rom_[pc];
        backend_.trace(pc,op,active());
        uint32_t length=0;
        // Lengths/operands from selected Nouveau handlers; no generated or
        // firmware instruction data is embedded in this implementation.
        switch(op) {
        case 0x36: case 0x38: case 0x71: case 0x72: case 0x8c: case 0x8d: case 0x8e: length=1; break; // nvkm/subdev/bios/init.c:2233, nvkm/subdev/bios/init.c:2235, nvkm/subdev/bios/init.c:2274, nvkm/subdev/bios/init.c:2275, nvkm/subdev/bios/init.c:2285, nvkm/subdev/bios/init.c:2286, nvkm/subdev/bios/init.c:2287
        case 0x33: case 0x6f: case 0x75: length=2; break; // nvkm/subdev/bios/init.c:2231, nvkm/subdev/bios/init.c:2273, nvkm/subdev/bios/init.c:2278
        case 0x53: case 0x56: case 0x5b: case 0x74: length=3; break; // nvkm/subdev/bios/init.c:2252, nvkm/subdev/bios/init.c:2254, nvkm/subdev/bios/init.c:2259, nvkm/subdev/bios/init.c:2277
        case 0x69: length=5; break; // nvkm/subdev/bios/init.c:2269
        case 0x7a: case 0x90: length=9; break; // nvkm/subdev/bios/init.c:2283, nvkm/subdev/bios/init.c:2289
        case 0x6e: case 0x97: length=13; break; // nvkm/subdev/bios/init.c:2272, nvkm/subdev/bios/init.c:2293
        case 0x5f: length=22; break; // nvkm/subdev/bios/init.c:2262
        case 0x4d: // nvkm/subdev/bios/init.c:2246
            if (!span(pc,4)) return Stop::Failed;
            length=4+2*rom_[pc+3]; break;
        case 0x58: case 0x91: // nvkm/subdev/bios/init.c:2256,2289
            if (!span(pc,6)) return Stop::Failed;
            length=6+4*rom_[pc+5]; break;
        case 0x8f: // nvkm/subdev/bios/init.c:2288
            if (!span(pc,7)) return Stop::Failed;
            if (!tables_.ramGroups || tables_.ramIndex>=tables_.ramGroups) { result_.error=Error::Input; return Stop::Failed; }
            length=7+4*uint32_t(rom_[pc+6])*tables_.ramGroups; break;
        case 0xa9: // nvkm/subdev/bios/init.c:2297
            if (!span(pc,2)) return Stop::Failed;
            length=2+rom_[pc+1]; break;
        default: result_.error=Error::Unsupported; return Stop::Failed;
        }
        if (!span(pc,length)) return Stop::Failed;
        const uint32_t next=pc+length;
        const uint32_t reg=(length>=5) ? word(uint64_t(pc)+1,4) : 0;
        bool ok=true;
        switch(op) {
        case 0x71: return Stop::Done; // nvkm/subdev/bios/init.c:2274
        case 0x36: // nvkm/subdev/bios/init.c:2233
            pc=next;
            if (!repeatBody) { result_.error=Error::Malformed; return Stop::Failed; }
            return Stop::EndRepeat;
        case 0x33: { // nvkm/subdev/bios/init.c:2231
            const uint32_t count=rom_[pc+1];
            // Fail closed on zero-count/unstructured loops; see design limits.
            if (!count) { result_.error=Error::Malformed; return Stop::Failed; }
            uint32_t after=next;
            for (uint32_t i=0;i<count;++i) {
                uint32_t body=next;
                Stop stop=execute(body,depth+1,true);
                if (stop==Stop::Failed) return stop;
                if (stop!=Stop::EndRepeat) { result_.error=Error::Malformed; return Stop::Failed; }
                after=body;
            }
            pc=after; continue;
        }
        case 0x5b: // nvkm/subdev/bios/init.c:2259
            if (active()) {
                uint32_t target=word(uint64_t(pc)+1,2);
                Stop stop=execute(target,depth+1,false);
                if (stop==Stop::Failed) return stop;
            }
            break;
        case 0x38: flags_^=2; break; // nvkm/subdev/bios/init.c:2235
        case 0x72: flags_ &= ~uint8_t(2); break; // nvkm/subdev/bios/init.c:2275
        case 0x75: { // nvkm/subdev/bios/init.c:2278
            bool met=false; ok=condition(rom_[pc+1],met); conditionFlag(met); break;
        }
        case 0x56: // nvkm/subdev/bios/init.c:2254
            if (active()) {
                uint32_t attempts=uint32_t(rom_[pc+2])*50;
                if (attempts>100) attempts=100;
                bool met=false;
                for (uint32_t i=0;i<attempts;++i) {
                    if (!deadline() || !condition(rom_[pc+1],met)) return Stop::Failed;
                    if (met) break;
                    if (!backend_.delayUs(20000)) { result_.error=Error::Io; return Stop::Failed; }
                }
                conditionFlag(met);
            }
            break;
        case 0x74: // nvkm/subdev/bios/init.c:2277
            if (active()) {
                uint64_t us=word(uint64_t(pc)+1,2);
                if (us>=1000) us=((us+900)/1000)*1000;
                ok=backend_.delayUs(us);
            }
            break;
        case 0x6e: ok=masked(reg,word(uint64_t(pc)+5,4),word(uint64_t(pc)+9,4)); break; // nvkm/subdev/bios/init.c:2272
        case 0x7a: ok=write(reg,word(uint64_t(pc)+5,4)); break; // nvkm/subdev/bios/init.c:2283
        case 0x90: { uint32_t value=0; ok=read(reg,value) && write(word(uint64_t(pc)+5,4),value); break; } // nvkm/subdev/bios/init.c:2289
        case 0x97: { // nvkm/subdev/bios/init.c:2293
            uint32_t value=0, mask=word(uint64_t(pc)+5,4);
            ok=read(reg,value) && write(reg,(value & mask) | ((value+word(uint64_t(pc)+9,4)) & ~mask)); break;
        }
        case 0x5f: { // nvkm/subdev/bios/init.c:2262
            const uint8_t shift=rom_[pc+5];
            const uint32_t bits=shift<0x80 ? shift : 0x100-shift; // nvkm/subdev/bios/init.c:531-536
            if (bits>=32) { result_.error=Error::Input; return Stop::Failed; }
            uint32_t value=0; ok=read(reg,value);
            value=shift<0x80 ? value>>bits : value<<bits; // nvkm/subdev/bios/init.c:531-536
            value=(value & word(uint64_t(pc)+6,4)) ^ word(uint64_t(pc)+10,4);
            ok=ok && masked(word(uint64_t(pc)+14,4),word(uint64_t(pc)+18,4),value); break;
        }
        case 0x58: case 0x91: // nvkm/subdev/bios/init.c:2256,2289
            for (uint32_t i=0;ok && i<rom_[pc+5];++i) {
                if (reg>UINT32_MAX-4*i) { result_.error=Error::Input; return Stop::Failed; }
                ok=write(reg+(op==0x58 ? 4*i : 0),word(uint64_t(pc)+6+4*i,4)); // nvkm/subdev/bios/init.c:1281-1300,2034-2052
            }
            break;
        case 0x8f: // nvkm/subdev/bios/init.c:2288
            for (uint32_t i=0;ok && i<rom_[pc+6];++i) {
                const uint32_t increment=rom_[pc+5]*i;
                if (reg>UINT32_MAX-increment) { result_.error=Error::Input; return Stop::Failed; }
                ok=write(reg+increment,word(uint64_t(pc)+7+4*(i*tables_.ramGroups+tables_.ramIndex),4));
            }
            break;
        case 0x6f: // nvkm/subdev/bios/init.c:2273
            if (tables_.macros) {
                uint64_t entry=uint64_t(tables_.macros)+8*rom_[pc+1];
                if (!span(entry,8)) return Stop::Failed;
                ok=write(word(entry,4),word(entry+4,4));
            }
            break;
        case 0x8c: case 0x8d: break; // Markers, not a physical reset. // nvkm/subdev/bios/init.c:2285, nvkm/subdev/bios/init.c:2286
        case 0x4d: case 0x53: case 0x69: case 0x8e: case 0xa9: // nvkm/subdev/bios/init.c:2246, nvkm/subdev/bios/init.c:2252, nvkm/subdev/bios/init.c:2269, nvkm/subdev/bios/init.c:2287, nvkm/subdev/bios/init.c:2297
            // IO helper has chip side effects: do not silently omit it, even
            // when a caller believes legacy VGA ports are irrelevant.
            if (active() || op==0x69) { // nvkm/subdev/bios/init.c:1623-1660
                if (!backend_.board(op,pc,rom_+pc,length,active())) { result_.error=Error::Denied; return Stop::Failed; }
            }
            break;
        default: break;
        }
        if (!ok) { if (result_.error==Error::None) result_.error=Error::Io; return Stop::Failed; }
        if (!deadline()) return Stop::Failed;
        pc=next;
    }
}
} // namespace k40::devinit
