// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "gr/Runner.h"
#include "memstage/ChannelImage.h"
#include "memstage/Mapper.h"
namespace k40::gr {
enum class Step:uint8_t {None,Route,Memory,Tables,Expose,Fifo,Bind,Gating,Start,Golden,Attach,Submit,Result,Status,Teardown,Done};
struct Report {
    Step step=Step::None;memstage::Error error=memstage::Error::None;Failure runner{},closing{};
    bool bound=false,started=false,golden=false,attached=false,submitted=false,consumed=false,computed=false,closed=false;
    uint32_t reads=0,writes=0,ops=0;
    uint32_t getAfter=0,putAfter=0,polls=0,wrong=0,firstWrong=0,firstValue=0,resultPolls=0;
    uint64_t progressUs=0,resultUs=0,totalUs=0;
    uint32_t mc=0,fifoIntr=0,mmuPending=0,pbdmaIntr=0,pbdmaHce=0,state=0,grIntr=0,grTrap=0,fecsIntr=0,engineStatus=0;
    uint32_t image[8]{}; // First words of the golden context image.
};
// S3: the GR engine start, the golden context and, with launch, one compute
// job on one channel of the GR runlist (work/S3LAUNCH/PLAN.md). Polling only.
// Every register write is an op of the generated program (gr/Program.h) or one
// of the reviewed S1 mapping writes; the resident Policy checks each with gr::Guard.
class Compute final:private Port {
public:
    Compute(memstage::Io& io,memstage::Faults& faults,memstage::Journal& journal,memory::vram::Arena& arena,
        memstage::Upload& upload,memstage::Mapper& mapper,uint64_t epoch,bool launch)
        :io_(io),faults_(faults),journal_(journal),arena_(arena),upload_(upload),mapper_(mapper),epoch_(epoch),launch_(launch),
         runner_(*this),closer_(*this){}
    // True only when every step passed: without launch, the golden context and a
    // clean teardown; with launch, also every output element equal to input + 1.
    bool run();
    bool launch() const{return launch_;}
    const Report& report() const{return report_;}
private:
    bool read32(uint32_t addr,uint32_t& value) override;
    bool write32(uint32_t addr,uint32_t value) override;
    bool now(uint64_t& microseconds) override;
    bool delay(uint32_t microseconds) override;
    bool hook(uint32_t number) override;
    bool fail(memstage::Error);
    bool tick();
    void phase(memstage::Phase p){phase_=p;upload_.phase(p);}
    bool token(memory::vram::Role,memory::vram::Token&) const;
    bool physical(memory::vram::Role,uint64_t&) const;
    bool route();
    bool memory();
    bool invalidate();
    bool stage(const Stage& ops,Step step,unsigned number);
    bool contextPointer();
    bool submit();
    bool result();
    bool snapshot();
    bool teardown();
    memstage::Io& io_;memstage::Faults& faults_;memstage::Journal& journal_;memory::vram::Arena& arena_;
    memstage::Upload& upload_;memstage::Mapper& mapper_;uint64_t epoch_=0;bool launch_=false;
    Runner runner_,closer_;Report report_{};
    uint64_t start_=0,last_=0;memstage::Phase phase_=memstage::Phase::ChannelBase;
    memstage::channel::Addresses addresses_{};
    bool attempted_=false,exposed_=false;
};
}
