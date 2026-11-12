// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memstage/Mapper.h"
namespace k40::memnative {
// The whole K40c BAR0 (16 MiB; mmiotrace MAP 0xc1000000 size 0x1000000). The
// channel registers start at 0x800000 (fifo/gk104.c:44-77), beyond 8 MiB.
constexpr uint32_t bar0View=16777216; // no source: PCI resource size, captured in reference/linux-run-debug.
class NativeIo;
class Policy {
public:
    Policy(memory::vram::Arena& arena,memstage::Faults& faults):arena_(arena),faults_(faults){}
    bool read(uint32_t,bool window) const;
    void observed(uint32_t,uint32_t);
    bool write(uint32_t,uint32_t,bool window,bool mmu);
    bool barRead(uint64_t,bool mmu) const;
    bool barWrite(uint64_t,uint32_t,bool mmu);
    unsigned channelStep() const{return step_;}
private:
    friend class NativeIo;
#ifndef _KERNEL_MODE
    friend struct PolicyProbe;
#endif
    void aperture(uint64_t bytes){aperture_=bytes;}
    bool record(memory::vram::Role,memory::vram::Record&) const;
    bool physical(uint32_t,memory::vram::Record&,uint64_t&) const;
    bool dataValue(const memory::vram::Record&,uint64_t,uint32_t) const;
    unsigned commandPhase() const;
    // S1 channel script (memstage/Channel.cpp), checked step by step.
    bool channelActive() const;
    bool channelRead(uint32_t) const;
    bool channelWrite(uint32_t,uint32_t);
    bool channelData(const memory::vram::Record&,uint64_t,uint32_t);
    bool channelAddresses(memory::vram::Record roles[9],bool& copy) const;
    bool engine(uint32_t&) const;
    bool runlist(uint32_t&) const;
    bool pbdma(uint32_t&) const;
    memory::vram::Arena& arena_;memstage::Faults& faults_;
    uint64_t aperture_=0,selected_=UINT64_MAX;
    uint32_t pending_=0,priv0_=0,priv1_=0,hubs_=0,rops_=0,gpcs_=0,units_=0,disabled_=0;
    uint32_t status_=0,context_=0,expectedContext_=0;
    unsigned commands_=0;bool mode_=false,pdb_=false,queued_=false;
    unsigned step_=0,sptWords_=0;
    uint32_t mask_=0,runm_[8]{},value2a04_=0,control_=0,state_=0,inst_=0;
    bool probed_=false,read2a04_=false,readControl_=false,readState_=false,readInst_=false;
    bool waitQueued_=false,chanQueued_=false,runlistClear_=false,preemptClear_=false,put2_=false;
};
}
