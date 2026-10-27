// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "devinit/PostImage.h"
namespace k40::devinit {
bool PostLayout::span(uint32_t at, uint32_t bytes) const { return at <= size_ && bytes <= size_ - at; }
uint32_t PostLayout::get(uint32_t at, unsigned bytes) const
{
    uint32_t value = 0;
    for (unsigned i = 0; i < bytes; ++i) value |= uint32_t(rom_[at+i]) << (i*8);
    return value;
}
bool PostLayout::normal(uint32_t reg) const
{
    return !(reg & ~0x00fffffc); // bios/init.c:144-178: this subset rejects contextual/unaligned encodings.
}
const PostInstruction* PostLayout::instruction(uint32_t pc) const
{
    for (uint32_t i = 0; i < count_; ++i) if (code_[i].offset == pc) return &code_[i];
    return nullptr;
}
bool PostLayout::table(uint32_t field, uint32_t& pointer) const
{
    if (!span(0x36,2)) return false; // bios/dcb.c:35.
    const auto dcb = get(0x36,2); // bios/dcb.c:35.
    if (!dcb || !span(dcb,12) || get(dcb,1) < 0x30 || get(dcb,1) > 0x41 // bios/dcb.c:43-48.
        || get(dcb+1,1) < 12 || get(dcb+6,4) != 0x4edcbdcb) return false; // bios/dcb.c:48.
    pointer = get(dcb+field,2);
    return pointer && span(pointer,4);
}
Error PostLayout::inspect(const uint8_t* rom, uint32_t size)
{
    rom_ = rom; size_ = size; roots_ = count_ = conditions_ = macros_ = groups_ = gpio_ = 0;
    ram_.fill(0);
    if (!rom || !size) return Error::Input;
    const auto error = parse();
    if (error != Error::None) { roots_ = count_ = 0; rom_ = nullptr; size_ = 0; }
    return error;
}
Error PostLayout::parse()
{
    uint32_t bit = 0, found = 0;
    for (uint32_t i = 0; span(i,5); ++i) {
        if (get(i,1)==0xff && get(i+1,1)==0xb8 && get(i+2,1)=='B' // bios/base.c:189-190.
            && get(i+3,1)=='I' && get(i+4,1)=='T') { bit=i; ++found; }
    }
    if (found != 1 || !span(bit,12)) return Error::Malformed;
    const auto stride=get(bit+9,1), entries=get(bit+10,1);
    if (stride<6 || !span(bit+12,stride*entries)) return Error::Bounds;
    std::array<bool,256> seen{};
    uint32_t ip=0, il=0, mp=0, ml=0, mv=0;
    for (uint32_t i=0;i<entries;++i) {
        const auto at=bit+12+i*stride, key=get(at,1), ver=get(at+1,1), len=get(at+2,2), ptr=get(at+4,2);
        if (seen[key] || !span(ptr,len)) return Error::Malformed;
        seen[key]=true;
        if (key=='I') { if (ver!=1 || len<14 || !ptr) return Error::Unsupported; ip=ptr; il=len; }
        if (key=='M') { mp=ptr; ml=len; mv=ver; }
    }
    if (!ip || !mp || !((mv==1 && ml>=5)||(mv==2 && ml>=3))) return Error::Unsupported;
    conditions_=get(ip+6,2); macros_=get(ip+4,2); // bios/init.c:399-403.
    groups_=get(mp+(mv==1?2:0),1); // bios/ramcfg.c:38-46.
    if (!groups_) return Error::Input;
    const auto xlat=get(mp+(mv==1?3:1),2); // bios/ramcfg.c:64-80.
    for (unsigned s=0;s<ram_.size();++s) {
        if (xlat && !span(xlat+s,1)) return Error::Bounds;
        ram_[s]=uint8_t(xlat?get(xlat+s,1):s);
    }
    const auto mt=mv==2 && ml>=7?get(mp+3,2):0; // bios/ramcfg.c:72-77; bios/M0203.c:36-37.
    if (mt) {
        if (!span(mt,1)) return Error::Bounds;
        if (get(mt,1)==0x10) { // bios/M0203.c:41-45.
            if (!span(mt,7)) return Error::Bounds;
            const auto header=get(mt+1,1), step=get(mt+2,1), count=get(mt+3,1);
            if (header<7 || step<2 || get(mt+4,1)!=0 || !span(mt,header+step*count)) return Error::Unsupported;
            std::array<bool,16> matched{};
            for (uint32_t i=0;i<count;++i) {
                const auto entry=mt+header+i*step, strap=get(entry,1)>>4;
                if (!matched[strap]) { ram_[strap]=get(entry+1,1)&0x0f; matched[strap]=true; } // bios/M0203.c:96-99,122-138.
            }
        }
    }
    const auto scripts=get(ip,2);
    if (!scripts) return Error::Input;
    bool terminated=false;
    for (uint32_t i=0;i<rootsList_.size()-1;++i) {
        if (!span(scripts+2*i,2)) return Error::Bounds;
        const auto pc=get(scripts+2*i,2);
        if (!pc) { terminated=true; break; }
        rootsList_[roots_++]=pc;
    }
    if (!terminated || !roots_) return Error::Malformed;
    if (il>=16 && get(ip+14,2)) rootsList_[roots_++]=get(ip+14,2); // bios/init.c:432-436,2331-2344.
    std::array<uint32_t,256> pending{};
    uint32_t pendingCount=roots_;
    for (uint32_t i=0;i<roots_;++i) pending[i]=rootsList_[i];
    while (pendingCount) {
        auto pc=pending[--pendingCount];
        unsigned loops=0;
        while (!instruction(pc)) {
            if (!span(pc,1)) return Error::Bounds;
            const auto op=get(pc,1);
            uint32_t length=0;
            switch(op) {
            case 0x36: case 0x38: case 0x71: case 0x72: case 0x8c: case 0x8d: case 0x8e: length=1; break; // bios/init.c:2233,2235,2274,2275,2285-2287.
            case 0x33: case 0x6f: case 0x75: length=2; break; // bios/init.c:2231,2273,2278.
            case 0x53: case 0x56: case 0x5b: case 0x74: length=3; break; // bios/init.c:2252,2254,2259,2277.
            case 0x69: length=5; break; // bios/init.c:2269.
            case 0x7a: case 0x90: length=9; break; // bios/init.c:2283,2289.
            case 0x6e: case 0x97: length=13; break; // bios/init.c:2272,2293.
            case 0x5f: length=22; break; // bios/init.c:2262.
            case 0x4d: if (!span(pc,4)) return Error::Bounds; length=4+2*get(pc+3,1); break; // bios/init.c:2246.
            case 0x58: case 0x91: if (!span(pc,6)) return Error::Bounds; length=6+4*get(pc+5,1); break; // bios/init.c:2256,2290.
            case 0x8f: if (!span(pc,7)) return Error::Bounds; length=7+4*get(pc+6,1)*groups_; break; // bios/init.c:2288.
            case 0xa9: if (!span(pc,2)) return Error::Bounds; length=2+get(pc+1,1); break; // bios/init.c:2297.
            default: return Error::Unsupported;
            }
            if (!span(pc,length)) return Error::Bounds;
            if (count_==code_.size()) return Error::Budget;
            for (uint32_t i=0;i<count_;++i)
                if (pc<code_[i].offset+code_[i].bytes && code_[i].offset<pc+length) return Error::Malformed;
            code_[count_++]={pc,length,uint8_t(op)};
            if (op==0x33) { if (!get(pc+1,1)) return Error::Unsupported; ++loops; } // bios/init.c:2231.
            if (op==0x36) { if (!loops) return Error::Malformed; --loops; } // bios/init.c:2233.
            if (op==0x5b) { // bios/init.c:2259.
                const auto target=get(pc+1,2);
                if (!target || pendingCount==pending.size()) return Error::Malformed;
                pending[pendingCount++]=target;
            }
            if (op==0x71) { if (loops) return Error::Unsupported; break; } // bios/init.c:2274.
            pc+=length;
        }
        if (loops) return Error::Malformed;
    }
    // Validate all register/table inputs before any effect. The image is fixed;
    // conditions do not remove their skipped alternatives from preflight.
    for (uint32_t i=0;i<count_;++i) {
        const auto pc=code_[i].offset; const uint32_t op=code_[i].opcode;
        auto reg=[&](uint32_t at) { return span(at,4) && normal(get(at,4)); };
        if (op==0x56 || op==0x75) { // bios/init.c:1250-1256,1785-1795.
            if (conditions_) {
                const auto entry=conditions_+12*get(pc+1,1);
                if (!span(entry,12) || !reg(entry)) return Error::Bounds;
            }
        }
        if (op==0x6f && macros_) { // bios/init.c:1734-1748.
            const auto entry=macros_+8*get(pc+1,1);
            if (!span(entry,8) || !reg(entry)) return Error::Bounds;
        }
        switch(op) {
        case 0x6e: case 0x7a: case 0x97: case 0x90: case 0x5f: case 0x58: case 0x91: case 0x8f: // bios/init.c:2272,2283,2293,2289,2262,2256,2290,2288.
            if (!reg(pc+1)) return Error::Unsupported;
        }
        if (op==0x90 && !reg(pc+5)) return Error::Unsupported; // bios/init.c:2289.
        if (op==0x5f) { // bios/init.c:2262.
            const auto shift=get(pc+5,1), bits=shift<128?shift:256-shift;
            if (!reg(pc+14) || bits>=32) return Error::Unsupported;
        }
        if (op==0x58 || op==0x8f) { // bios/init.c:2256,2288.
            const auto base=get(pc+1,4), step=op==0x58?4:get(pc+5,1), count=get(pc+(op==0x58?5:6),1); // bios/init.c:1281-1300,1995-2010.
            if (count && (base>UINT32_MAX-step*(count-1) || !normal(base+step*(count-1)))) return Error::Unsupported;
        }
        if (op==0xa9) { // bios/init.c:2297.
            if (!table(10,gpio_)) return Error::Input;
            const auto header=get(gpio_+1,1), count=get(gpio_+2,1), stride=get(gpio_+3,1);
            if (get(gpio_,1)!=0x41 || header<4 || stride<5 || !span(gpio_,header+count*stride)) return Error::Unsupported; // bios/gpio.c:103-110.
            for (uint32_t j=0;j<count;++j) {
                const auto raw=get(gpio_+header+j*stride,4);
                if (((raw>>8)&255)!=255 && (raw&63)>=32) return Error::Unsupported;
            }
        }
        if (op==0x4d) { // bios/init.c:2246.
            uint32_t ccb=0;
            if (!table(4,ccb) || !span(ccb,5)) return Error::Input;
            const auto header=get(ccb+1,1), count=get(ccb+2,1), stride=get(ccb+3,1);
            if (get(ccb,1)!=0x40 || header<5 || stride<4 || !span(ccb,header+count*stride)) return Error::Unsupported; // bios/i2c.c:32-62,79-112.
            auto index=get(pc+1,1);
            if (index==0x80) index=get(ccb+4,1)&15; // subdev/i2c/base.c:53-64.
            else if (index==0x81) index=get(ccb+4,1)>>4; // subdev/i2c/base.c:53-64.
            if (index>=count) return Error::Input;
            const auto raw=get(ccb+header+index*stride,4);
            if ((raw>>24)!=5 || (raw&0x100)) return Error::Unsupported; // bios/i2c.c:107-112, dedicated NVIO only.
        }
    }
    // Referenced tables may not overlap executable instruction bytes.
    for (uint32_t i=0;i<count_;++i) {
        const auto pc=code_[i].offset; const uint32_t op=code_[i].opcode;
        uint32_t at=0, length=0;
        if ((op==0x56 || op==0x75) && conditions_) { at=conditions_+12*get(pc+1,1); length=12; } // bios/init.c:479-491.
        if (op==0x6f && macros_) { at=macros_+8*get(pc+1,1); length=8; } // bios/init.c:1734-1748.
        for (uint32_t j=0;length && j<count_;++j)
            if (at<code_[j].offset+code_[j].bytes && code_[j].offset<at+length) return Error::Malformed;
    }
    return Error::None;
}
bool PostLayout::group(uint8_t strap, uint8_t& result) const
{
    result=0;
    if (!count_ || strap>=ram_.size() || ram_[strap]>=groups_) return false;
    result=ram_[strap]; return true;
}
bool PostLayout::allow(uint32_t pc, uint32_t reg, unsigned width, bool write) const
{
    const auto* inst=instruction(pc);
    if (!inst) return false;
    const auto op=inst->opcode;
    if (width==4 && normal(reg)) {
        switch(op) {
        case 0x6e: case 0x97: return reg==get(pc+1,4); // bios/init.c:2272,2293.
        case 0x7a: return write && reg==get(pc+1,4); // bios/init.c:2283.
        case 0x90: return reg==get(pc+(write?5:1),4); // bios/init.c:2289.
        case 0x5f: return (reg==get(pc+14,4)) || (!write && reg==get(pc+1,4)); // bios/init.c:2262.
        case 0x58: case 0x8f: { // bios/init.c:2256,2288.
            if (!write) return false;
            const auto base=get(pc+1,4), step=op==0x58?4:get(pc+5,1), count=get(pc+(op==0x58?5:6),1); // bios/init.c:1281-1300,1995-2010.
            for (uint32_t i=0;i<count;++i) if (reg==base+i*step) return true;
            return false;
        }
        case 0x91: return write && get(pc+5,1) && reg==get(pc+1,4); // bios/init.c:2034-2052.
        case 0x6f: return write && macros_ && reg==get(macros_+8*get(pc+1,1),4); // bios/init.c:1734-1748.
        case 0x56: case 0x75: return !write && conditions_ && reg==get(conditions_+12*get(pc+1,1),4); // bios/init.c:479-491.
        }
    }
    if (!boardAllowed(approvedRomDigest(),pc,op)) return false;
    if (op==0x4d && width==4) { // bios/init.c:1037-1050.
        uint32_t ccb=0;
        if (!table(4,ccb)) return false;
        auto index=get(pc+1,1);
        if (index==0x80) index=get(ccb+4,1)&15; // subdev/i2c/base.c:53-64.
        else if (index==0x81) index=get(ccb+4,1)>>4; // subdev/i2c/base.c:53-64.
        const auto raw=get(ccb+get(ccb+1,1)+index*get(ccb+3,1),4);
        return reg==0x00d014+(raw&15)*0x20; // subdev/i2c/busgf119.c:93.
    }
    if (op==0x53) return width==1 && write && (reg==0x6013d4 || reg==0x6013d5); // engine/disp/vga.c:104-108.
    if (op==0x69) { // bios/init.c:1636-1655.
        if (width==1) return reg==0x601000+get(pc+1,2); // engine/disp/vga.c:49-52.
        if (width!=4) return false;
        if (reg==0x000200 || reg==0x00e18c) return true; // bios/init.c:1641-1654.
        return (reg==0x614100 || reg==0x614900); // bios/init.c:1640-1655.
    }
    if (op==0xa9 && width==4) { // bios/init.c:2193-2220.
        const auto header=get(gpio_+1,1), count=get(gpio_+2,1), stride=get(gpio_+3,1);
        for (uint32_t i=0;i<count;++i) {
            const auto raw=get(gpio_+header+i*stride,4), function=(raw>>8)&255, line=raw&63, selector=(raw>>24)&31;
            if (function==255) continue;
            bool excluded=false;
            for (uint32_t j=2;j<inst->bytes;++j) if (get(pc+j,1)==function) excluded=true;
            if (!excluded && (reg==0x00d610+line*4 || reg==0x00d604 // subdev/gpio/gf119.c:49,60-61.
                || (selector && reg==0x00d740+(selector-1)*4))) return true; // subdev/gpio/gf119.c:51.
        }
    }
    return false;
}
PostImage::PostImage(const uint8_t* rom, uint32_t size)
{
    if (!rom || size!=rom_.size()) return;
    for (uint32_t i=0;i<size;++i) rom_[i]=rom[i];
    if (sha256(rom_.data(),size)!=approvedRomDigest()) return;
    layoutError_=layout_.inspect(rom_.data(),size);
    approved_=layoutError_==Error::None;
}
Error PostImage::selectRam(Backend& backend)
{
    if (!backend.hostSimulation()) return Error::HardwareDisabled;
    if (!approved_) return Error::Denied;
    if (selectionAttempted_) return Error::Input;
    selectionAttempted_=true;
    uint32_t strap=0;
    if (!backend.read32(0x101000,strap)) return Error::Io; // bios/ramcfg.c:29-33.
    if (!layout_.group(uint8_t((strap&0x3c)>>2),group_)) return Error::Input; // bios/ramcfg.c:31.
    selected_=true; return Error::None;
}
}
