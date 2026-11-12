// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "gr/Program.h"
#include "memnative/Policy.h"
namespace k40::gr {
// The channel-phase write rules of the compute stage (S3). The op program is
// the allow-list: a register write is accepted only when it is the next
// writing op of the program, at that address, with the value that this class
// computes on its own from the owned ledger and from the values the card
// returned. It shares the op tables with the Runner and nothing else.
class Guard final:public memnative::Extension {
public:
    Guard(memory::vram::Arena& arena,const memnative::Policy& policy):arena_(arena),policy_(policy){}
    bool read(uint32_t reg) const override;
    void observed(uint32_t reg,uint32_t value) override;
    bool write(uint32_t reg,uint32_t value) override;
    bool data(const memory::vram::Record&,uint64_t offset,uint32_t value) override;
    bool barRead(uint64_t offset) const override;
    bool barWrite(uint64_t offset,uint32_t value) override;
    unsigned stage() const{return stage_;}
    unsigned index() const{return index_;}
    static constexpr unsigned stages=7; // no source: fifo, bind, gating, start, golden, attach, teardown.
private:
    bool record(memory::vram::Role,memory::vram::Record&) const;
    bool inputs();
    bool next(unsigned& stage,unsigned& index) const;
    bool matches(const Op&,uint32_t reg,uint32_t value) const;
    bool special(uint32_t reg,uint32_t value);
    memory::vram::Arena& arena_;const memnative::Policy& policy_;
    uint64_t slots_[maxSlots]{};uint32_t pendingOld_=0,pendingReg_=0;
    unsigned stage_=0,index_=0,exposeStep_=0,closeStep_=0,invalidations_=0;
    bool known_=false,put_=false,vmmQueued_=false;
};
}
