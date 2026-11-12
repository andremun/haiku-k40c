// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#ifdef _KERNEL_MODE
#include "memnative/NativeIo.h"
#include "memauth/Session.h"
#include "memstage/Experiment.h"
#include "memstage/Channel.h"
#include "a7/Module.h"
namespace k40::memnative {
class NativeOwner final:public memauth::Runtime {
public:
    NativeOwner(const uint8_t key[32],const uint8_t nonce[32],const uint8_t plan[32],const uint8_t challenge[16],uint64_t epoch,uint64_t vram,bool copy);
    status_t prepare(uint64*,uint8_t*);
    status_t submit(uint64,const uint8_t*,size_t);
    status_t detach(uint64);
    status_t observeLoad();
    bool execute() override;
private:
    bool work();
    void drain();
    memory::vram::Arena arena_;memstage::Journal journal_;NativeIo io_;
    memstage::Faults faults_;Policy policy_;memstage::Upload upload_;memstage::Mapper mapper_;
    memstage::Channel channel_;
    memauth::Binding binding_;alignas(memauth::Session) uint8_t sessionStorage_[sizeof(memauth::Session)]{};
    memauth::Session* session_=nullptr;k40_a7_module* a7_=nullptr;
    alignas(memstage::Experiment) uint8_t experimentStorage_[sizeof(memstage::Experiment)]{};
    memstage::Experiment* experiment_=nullptr;
    bool opened_=false,failed_=false;unsigned loads_=0;
};
}
#endif
