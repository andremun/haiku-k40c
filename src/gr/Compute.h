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
    uint32_t imageWords=0,imageSum=0,imageLines=0; // Print mode: words not zero, sum of all words, printed lines.
    // Observe mode (work/S3DIAG/REPORT.md, approach B): samples after GP_PUT, GP_GET and GP_PUT of the last
    // slow-window read, MMU fault units whose record was read, and whether the last BAR1 read was made.
    uint32_t samples=0,windowGet=0,windowPut=0,faultUnits=0;bool barRead=false;
};
// What the one GPFIFO entry fetches (work/S3DIAG/PLAN.md): nothing (no submit),
// the object bind, the set-up without the launch, or the whole job with its result.
// The push buffer page holds the same words in every mode; only the entry length differs.
enum class Launch:uint8_t {None,Bind,Setup,Full};
// Differences from the Linux reference run that the aligned stages remove
// (work/S3DIAG/FINDINGS.md, trace comparison): a copy of the golden image as the
// channel's context, PRIV and writable PTEs for the page pool, bundle and register
// list, and a channel that is not privileged (RAMFC 0xe4 = 0).
// list: the list count in word 0 of the copy when it is below patchCount. FECS runs that
// prefix of the register list at the load; 0 runs none (fuc/hub.fuc:686-690; work/S3DIAG/REPORT.md,
// approaches H and the bisection after it). allList: the whole list, as Linux.
constexpr uint32_t allList=0xffffffff; // no source: software marker for "the whole list".
struct Align {bool copy=false,priv=false,user=false;uint32_t list=allList;};
// How the progress after GP_PUT is read (work/S3DIAG/REPORT.md): the BAR1 poll; approach B, BAR0
// status registers and the slow window, BAR1 last; or approach F, registers only until the
// teardown ended, then one slow-window read of USERD as the last action.
// Report (approach G): as Registers, with the FECS trace word, the window selector and the BAR1
// context in group 8, one more sample after the teardown, and no read of VRAM after GP_PUT at
// all. GP_GET is then not known: the stage passes on a clean state and a clean teardown.
// Last (approach H): as Report, then one slow-window read of USERD as the last action.
enum class Observe:uint8_t {None,Window,Registers,Report,Last};
// Host-side progress sink: the owner prints each call at once (no card access).
class Progress {
public:
    virtual void live(Step step,uint64_t microseconds,uint32_t a,uint32_t b)=0;
    // Eight words of the golden image at a byte offset (print mode, work/S3DIAG/REPORT.md).
    virtual void words(uint32_t offset,const uint32_t values[8])=0;
    // Observe mode: one group of status values of sample n (work/S3DIAG/REPORT.md, approach B).
    virtual void observed(uint32_t sample,uint32_t group,uint64_t microseconds,const uint32_t* values,unsigned count)=0;
protected:
    ~Progress()=default;
};
// With print, the golden image is read after its generation and given to the progress
// sink in lines of eight words; lines of zeros are left out (work/S3DIAG/REPORT.md, approach A).
// With observe, no BAR1 access follows GP_PUT until the last action: the progress is read through
// BAR0 status registers and the slow window, each group printed at once (approach B).
// S3: the GR engine start, the golden context and, with launch, one compute
// job on one channel of the GR runlist (work/S3LAUNCH/PLAN.md). Polling only.
// Every register write is an op of the generated program (gr/Program.h) or one
// of the reviewed S1 mapping writes; the resident Policy checks each with gr::Guard.
class Compute final:private Port {
public:
    Compute(memstage::Io& io,memstage::Faults& faults,memstage::Journal& journal,memory::vram::Arena& arena,
        memstage::Upload& upload,memstage::Mapper& mapper,uint64_t epoch,Launch launch,Progress* progress=nullptr,Align align={},bool print=false,Observe observe=Observe::None)
        :io_(io),faults_(faults),journal_(journal),arena_(arena),upload_(upload),mapper_(mapper),epoch_(epoch),launch_(launch),progress_(progress),align_(align),print_(print),observe_(observe),
         runner_(*this),closer_(*this){}
    // True only when every step passed: without launch, the golden context and a
    // clean teardown; with a submit, also GP_GET 1; with the full job, also every
    // output element equal to input + 1.
    bool run();
    Launch launch() const{return launch_;}
    const Align& align() const{return align_;}
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
    void live(Step step,uint32_t a=0,uint32_t b=0){if(progress_)progress_->live(step,last_-start_,a,b);}
    bool begin(Step step){report_.step=step;live(step);return true;}
    bool token(memory::vram::Role,memory::vram::Token&) const;
    bool physical(memory::vram::Role,uint64_t&) const;
    bool route();
    bool memory();
    bool invalidate();
    bool stage(const Stage& ops,Step step,unsigned number);
    bool contextPointer();
    bool copyContext();
    bool listReads();
    bool printImage();
    bool submit();
    bool sample(uint32_t number);
    bool observe();
    bool lastRead();
    bool registersOnly() const{return observe_==Observe::Registers || observe_==Observe::Report || observe_==Observe::Last;}
    bool wide() const{return observe_==Observe::Report || observe_==Observe::Last;}
    bool result();
    bool snapshot();
    bool teardown();
    memstage::Io& io_;memstage::Faults& faults_;memstage::Journal& journal_;memory::vram::Arena& arena_;
    memstage::Upload& upload_;memstage::Mapper& mapper_;uint64_t epoch_=0;Launch launch_=Launch::None;Progress* progress_=nullptr;Align align_{};bool print_=false;Observe observe_=Observe::None;
    Runner runner_,closer_;Report report_{};
    uint64_t start_=0,last_=0;memstage::Phase phase_=memstage::Phase::ChannelBase;
    memstage::channel::Addresses addresses_{};
    bool attempted_=false,exposed_=false;
    uint32_t copy_[4096]{}; // no source: software block of the golden-image copy (aligned stages).
};
}
