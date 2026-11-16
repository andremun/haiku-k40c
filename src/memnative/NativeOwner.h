// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#ifdef _KERNEL_MODE
#include "memnative/NativeIo.h"
#include "memauth/Session.h"
#include "memstage/Experiment.h"
#include "memstage/Channel.h"
#include "gr/Compute.h"
#include "gr/Guard.h"
#include "a7/Module.h"
namespace k40::memnative {
class NativeOwner final:public memauth::Runtime {
public:
    NativeOwner(const uint8_t key[32],const uint8_t nonce[32],const uint8_t plan[32],const uint8_t challenge[16],uint64_t epoch,uint64_t vram,unsigned stage);
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
    // Prints each progress call of the compute stage at once (work/S3DIAG/PLAN.md).
    class Live final:public gr::Progress {
    public:
        void live(gr::Step step,uint64_t microseconds,uint32_t a,uint32_t b) override;
    };
    // Stage of the package (tools/memstage/stage.py): 0 S1, 1 S2 copy, 2 S3 golden context, 3 S3 compute,
    // 4 S2 copy diagnostic (engine busy bit recorded only), 5 S3 object bind, 6 S3 set-up without launch.
    static gr::Launch launchOf(unsigned stage);
    static bool computeStage(unsigned stage){return stage==2 || stage==3 || stage==5 || stage==6;}
    unsigned stage_=0;gr::Guard guard_;Live live_;gr::Compute compute_;
    memauth::Binding binding_;alignas(memauth::Session) uint8_t sessionStorage_[sizeof(memauth::Session)]{};
    memauth::Session* session_=nullptr;k40_a7_module* a7_=nullptr;
    alignas(memstage::Experiment) uint8_t experimentStorage_[sizeof(memstage::Experiment)]{};
    memstage::Experiment* experiment_=nullptr;
    bool opened_=false,failed_=false;unsigned loads_=0;
};
}
#endif
