// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memstage/Mapper.h"
namespace k40::memnative {
class NativeIo;
class Policy {
public:
    Policy(memory::vram::Arena& arena,memstage::Faults& faults):arena_(arena),faults_(faults){}
    bool read(uint32_t,bool window) const;
    void observed(uint32_t,uint32_t);
    bool write(uint32_t,uint32_t,bool window,bool mmu);
    bool barRead(uint64_t,bool mmu) const;
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
    memory::vram::Arena& arena_;memstage::Faults& faults_;
    uint64_t aperture_=0,selected_=UINT64_MAX;
    uint32_t pending_=0,priv0_=0,priv1_=0,hubs_=0,rops_=0,gpcs_=0,units_=0,disabled_=0;
    uint32_t status_=0,context_=0,expectedContext_=0;
    unsigned commands_=0;bool mode_=false,pdb_=false,queued_=false;
};
}
