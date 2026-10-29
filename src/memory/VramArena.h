// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memory/Memory.h"
namespace k40::memstage { class Mapper; }
namespace k40::memory::vram {
struct BarVirtual {uint64_t value=0;};
// Raw FB probe inputs; software bounds, not a discovered hardware unit count.
struct Probe {uint32_t parts=0,units=0,disabled=0,mib[32]{};};
struct Layout {uint64_t bytes=0;uint32_t activeParts=0;};
bool normalLayout(const Probe&,uint64_t expectedBytes,Layout&);
enum class Role:uint8_t {None,DebugRead,DebugWrite,Directory,SmallTable,Instance,DataA,DataB};
struct Token {uint64_t owner=0,epoch=0,id=0;};
struct Record {
    Token token{};Role role=Role::None;VramPhysical physical{0};uint64_t bytes=0,alignment=0;
    uint64_t writeGeneration=0;bool staged=false,referenced=false,retained=false;
    bool candidateBar=false;BarVirtual bar{};GpuVirtual channel{};bool channelKnown=false;
    // No publication, DMA visibility or mapping-verification field exists.
};
class Arena {
public:
    static constexpr unsigned capacity=16; // no source: software ledger capacity.
    Arena()=default;Arena(const Arena&)=delete;Arena& operator=(const Arena&)=delete;
    bool configure(const Probe&,uint64_t expectedBytes,uint64_t owner,uint64_t epoch,unsigned limit=capacity);
    bool allocate(Role,uint64_t bytes,uint64_t alignment,Token&);
    bool span(Token,uint64_t offset,uint64_t bytes,VramPhysical&) const;
    bool describe(Token,Record&) const;
    bool at(unsigned,Record&) const;
    bool dirty(Token); // Before attempting any write, including a possibly partial write.
    bool staged(Token); // Only the scoped upload/readback/flush protocol, never visibility.
    bool reference(Token);
    bool candidateBar(Token,BarVirtual); // Metadata only; never a translation proof.
    void fail();
    bool healthy() const {return configured_ && !failed_;}
    unsigned count() const {return count_;}
    uint64_t totalBytes() const {return total_;}
    uint64_t begin() const {return begin_;}
    uint64_t end() const {return end_;}
    static uint64_t requiredBytes(Role);
private:
    friend class k40::memstage::Mapper;
#ifndef _KERNEL_MODE
    friend struct ArenaProbe;
#endif
    bool tableDirty(Token); // Mapper uses only while holding its MMU transaction lock.
    Record* find(Token);
    const Record* find(Token) const;
    Record records_[capacity]{};
    uint64_t owner_=0,epoch_=0,total_=0,begin_=0,end_=0,cursor_=0;
    unsigned count_=0,limit_=0;
    bool attempted_=false,configured_=false,failed_=false;
};
}
