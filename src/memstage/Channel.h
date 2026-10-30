// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memstage/Mapper.h"
#include "memstage/ChannelImage.h"
namespace k40::memstage {
enum class Progress:uint8_t {NotRun,Consumed,Stalled,Failed};
struct ChannelReport {
    uint32_t runlist=0,pbdma=0,pbdmaMask=0,runm=0;
    uint32_t getBefore=0,putBefore=0,getAfter=0,putAfter=0,polls=0;
    uint32_t mc=0,fifoIntr=0,mmuPending=0,pbdmaIntr=0,pbdmaHce=0,state=0;
    uint64_t progressUs=0;
    Progress progress=Progress::NotRun;
    bool bound=false,closed=false;
};
// S1: one host NOP on one CE0-runlist channel, polling only, then teardown.
// Every register write passes the resident Policy. No interrupt is enabled.
class Channel {
public:
    Channel(Io& io,Faults& faults,Journal& journal,memory::vram::Arena& arena,Upload& upload,Mapper& mapper,uint64_t epoch)
        :io_(io),faults_(faults),journal_(journal),arena_(arena),upload_(upload),mapper_(mapper),epoch_(epoch){}
    bool run(); // True only for S1: GP_GET reached GP_PUT, no fault, clean teardown.
    Error error() const{return error_;}
    const ChannelReport& report() const{return report_;}
private:
    bool fail(Error,uint32_t=0,uint32_t=0);
    bool tick();
    bool read(uint32_t,uint32_t&);
    bool write(uint32_t,uint32_t);
    bool waitClear(uint32_t reg,uint32_t mask,Error);
    bool route();
    bool memory();
    bool invalidate();
    bool fifo();
    bool bind();
    bool submit();
    bool teardown();
    bool snapshot();
    void phase(Phase p){phase_=p;upload_.phase_=p;}
    Io& io_;Faults& faults_;Journal& journal_;memory::vram::Arena& arena_;Upload& upload_;Mapper& mapper_;
    uint64_t epoch_=0,start_=0,last_=0;
    memory::vram::Token tokens_[7]{};channel::Addresses addresses_{};
    ChannelReport report_{};Error error_=Error::None;Phase phase_=Phase::ChannelBase;
    bool attempted_=false,exposed_=false,closing_=false;
};
}
