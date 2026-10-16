// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#include "runtime/Bootstrap.h"
namespace k40::runtime {
namespace {
class Guard {
public:
    explicit Guard(BootstrapPort& port) : port_(port),held_(port.lock()) {}
    ~Guard() { if(held_)port_.unlock(); }
    bool held() const { return held_; }
private: BootstrapPort& port_; bool held_;
};
bool range(OwnedVram owned,uint64_t offset,size_t count)
{
    // Physical PRAMIN address masks span 44 bits in nvkm/subdev/instmem/nv50.c:64-65,84-85.
    const uint64_t limit=1ULL<<44;
    return count && count<=4096 && !(owned.base.value&3) && !(offset&3)
        && owned.base.value<limit && owned.bytes<=limit-owned.base.value
        && offset<=owned.bytes && count<=(owned.bytes-offset)/4;
}
bool poll(BootstrapPort& port,uint32_t reg,uint32_t busy,PollLimit limits)
{
    if(!limits.timeoutUs || !limits.attempts)return false;
    uint64_t start=port.nowUs(),last=start;
    for(uint32_t i=0;i<limits.attempts;++i) {
        uint64_t now=port.nowUs();
        if(now<last || now-start>=limits.timeoutUs)return false;
        last=now; uint32_t status=0;
        if(!port.read32(reg,status))return false;
        now=port.nowUs();
        if(now<last || now-start>=limits.timeoutUs)return false;
        last=now;
        if(!(status&busy))return true;
    }
    return false;
}
}
bool writeSlowWindow(BootstrapPort& port,OwnedVram owned,uint64_t offset,const uint32_t* data,size_t count)
{
    if(!port.hostSimulation() || !data || !range(owned,offset,count))return false;
    Guard guard(port);if(!guard.held())return false;
    uint64_t selected=UINT64_MAX;
    for(size_t i=0;i<count;++i) {
        uint64_t address=owned.base.value+offset+4*i;
        uint64_t window=address&~uint64_t(0xfffff); // nvkm/subdev/instmem/nv50.c:64-65
        if(window!=selected) {
            if(!port.write32(0x001700,uint32_t(window>>16)))return false; // nvkm/subdev/instmem/nv50.c:70
            selected=window;
        }
        if(!port.write32(0x700000+uint32_t(address&0xfffff),data[i]))return false; // nvkm/subdev/instmem/nv50.c:74
    }
    return true; // Publication/flush is a separate mandatory step.
}
bool readSlowWindow(BootstrapPort& port,OwnedVram owned,uint64_t offset,uint32_t* data,size_t count)
{
    if(!port.hostSimulation() || !data || !range(owned,offset,count))return false;
    Guard guard(port);if(!guard.held())return false;
    uint64_t selected=UINT64_MAX;
    for(size_t i=0;i<count;++i) {
        uint64_t address=owned.base.value+offset+4*i;
        uint64_t window=address&~uint64_t(0xfffff); // nvkm/subdev/instmem/nv50.c:84-85
        if(window!=selected) {
            if(!port.write32(0x001700,uint32_t(window>>16)))return false; // nvkm/subdev/instmem/nv50.c:91
            selected=window;
        }
        if(!port.read32(0x700000+uint32_t(address&0xfffff),data[i]))return false; // nvkm/subdev/instmem/nv50.c:94
    }
    return true;
}
bool flushBar(BootstrapPort& port,PollLimit limits)
{
    if(!port.hostSimulation() || !limits.timeoutUs || !limits.attempts)return false;
    Guard guard(port);if(!guard.held())return false;
    return port.write32(0x070000,1) && poll(port,0x070000,2,limits); // subdev/bar/g84.c:29-40
}
bool checkOwnedScratch(BootstrapPort& port,OwnedVram owned,const uint64_t* offsets,size_t samples,PollLimit limits)
{
    if(!port.hostSimulation() || !offsets || samples<2 || samples>64 || !limits.timeoutUs || !limits.attempts)return false;
    uint32_t patterns[64];
    for(size_t i=0;i<samples;++i) {
        if(!range(owned,offsets[i],1))return false;
        const uint64_t address=owned.base.value+offsets[i];
        patterns[i]=uint32_t((address>>2)^(address>>34))*0x9e3779b9u; // no source: software test pattern
        for(size_t j=0;j<i;++j)if(offsets[j]==offsets[i] || patterns[j]==patterns[i])return false;
    }
    uint64_t start=port.nowUs(),last=start;
    auto inTime=[&]() {
        const uint64_t now=port.nowUs();
        bool valid=now>=last && now-start<limits.timeoutUs;
        last=now;return valid;
    };
    for(unsigned pass=0;pass<2;++pass) {
        // All writes precede any reads, so two aliased sample locations cannot
        // both pass merely because each was read directly after its own write.
        for(size_t i=0;i<samples;++i) {
            uint32_t value=pass ? ~patterns[i] : patterns[i];
            if(!inTime() || !writeSlowWindow(port,owned,offsets[i],&value,1))return false;
        }
        if(!flushBar(port,limits))return false;
        for(size_t i=0;i<samples;++i) {
            uint32_t actual=0,expected=pass ? ~patterns[i] : patterns[i];
            if(!inTime() || !readSlowWindow(port,owned,offsets[i],&actual,1) || actual!=expected)return false;
        }
    }
    return inTime();
}

bool commitRunlist(BootstrapPort& port,uint32_t id,uint64_t address,RunlistTarget target,uint32_t entries,PollLimit limits)
{
    // ID width follows channel runlist mask, nvkm/engine/fifo/gk104.c:77; address/count fields
    // follow nvkm/engine/fifo/gk104.c:446-447. This does not infer available TOP routing IDs.
    if(!port.hostSimulation() || id>15 || address>=(1ULL<<40) || (address&0xfff)
        || entries>0xfffff || !limits.timeoutUs || !limits.attempts)return false; // nvkm/engine/fifo/gk104.c:446-447
    if(target!=RunlistTarget::Vram && target!=RunlistTarget::NoncoherentHost)return false;
    uint32_t aperture=target==RunlistTarget::Vram ? 0 : 3; // nvkm/engine/fifo/gk104.c:438-440
    Guard guard(port);if(!guard.held())return false;
    return port.write32(0x002270,(aperture<<28)|uint32_t(address>>12)) // nvkm/engine/fifo/gk104.c:446
        && port.write32(0x002274,(id<<20)|entries) // nvkm/engine/fifo/gk104.c:447
        && poll(port,0x002284+id*8,0x00100000,limits); // nvkm/engine/fifo/gk104.c:422-427
}
} // namespace k40::runtime
