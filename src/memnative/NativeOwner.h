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
        void words(uint32_t offset,const uint32_t values[8]) override;
        void observed(uint32_t sample,uint32_t group,uint64_t microseconds,const uint32_t* values,unsigned count) override;
    };
    // Stage of the package (tools/memstage/stage.py): 0 S1, 1 S2 copy, 2 S3 golden context, 3 S3 compute,
    // 4 S2 copy diagnostic (engine busy bit recorded only), 5 S3 object bind, 6 S3 set-up without launch,
    // 7 S3 object bind aligned with the Linux reference run (work/S3DIAG/FINDINGS.md),
    // 8 S3 golden context with the image printed (work/S3DIAG/REPORT.md),
    // 9 as 7, and after GP_PUT the progress observed without BAR1 access (work/S3DIAG/REPORT.md, approach B),
    // 10 as 7, and after GP_PUT registers only until the teardown ended (work/S3DIAG/REPORT.md, approach F),
    // 11 as 10 without any read of VRAM after GP_PUT, so that the report is printed (approach G),
    // 12 as 11 with no register list at the load, then one slow-window read as the last action (approach H),
    // 13 as 12 with the first 34 list entries, all but the LTC pair (work/S3DIAG/FINDINGS.md),
    // 14 as 12 with the whole list, after the fix of its LTC entries (work/S3DIAG/FINDINGS.md).
    static gr::Launch launchOf(unsigned stage);
    static gr::Align alignOf(unsigned stage){return stage==7 || (stage>=9 && stage<=16)?gr::Align{true,true,true,stage==12?0u:stage==13?34u:gr::allList}:gr::Align{};}
    static bool computeStage(unsigned stage){return stage==2 || stage==3 || stage==5 || stage==6 || stage==7 || stage==8 || stage==9 || stage==10 || stage==11 || stage==12 || stage==13 || stage==14 || stage==15 || stage==16;}
    unsigned stage_=0;gr::Guard guard_;Live live_;gr::Compute compute_;
    memauth::Binding binding_;alignas(memauth::Session) uint8_t sessionStorage_[sizeof(memauth::Session)]{};
    memauth::Session* session_=nullptr;k40_a7_module* a7_=nullptr;
    alignas(memstage::Experiment) uint8_t experimentStorage_[sizeof(memstage::Experiment)]{};
    memstage::Experiment* experiment_=nullptr;
    bool opened_=false,failed_=false;unsigned loads_=0;
};
}
#endif
