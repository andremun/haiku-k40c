// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memstage/Tables.h"
#include "memstage/Upload.h"
namespace k40::memstage {
enum class Closure:uint8_t {NotEnabled,RetainedUnknown,OwnedDisabled};
class Mapper {
public:
    Mapper(Io& io,Faults& faults,Journal& journal,memory::vram::Arena& arena,Upload& upload,uint64_t epoch)
        :io_(io),faults_(faults),journal_(journal),arena_(arena),upload_(upload),epoch_(epoch){}
    bool preflight(); // Required before any memory-stage VRAM write.
    bool run(uint64_t bar1Bytes,memory::vram::Token a,memory::vram::Token b);
    // Channel phase: map the USERD page at BAR1 VA 0, writable, and enable the
    // owned context again (fifo/gk104.c:745-746 USERD in BAR1). Then disable it.
    bool exposeUserd(memory::vram::Token userd,Phase phase);
    bool closeUserd(Phase phase);
    Error error() const{return error_;}
    Closure closure() const{return closure_;}
private:
    bool fail(Error,uint32_t=0,uint32_t=0);
    bool tick();
    bool read(uint32_t,uint32_t&);
    bool write(uint32_t,uint32_t);
    bool poll(uint32_t mask);
    bool invalidate(); // Caller holds the complete MMU transaction lock.
    bool witness(memory::vram::Token first,memory::vram::Token second);
    bool update(memory::vram::Token);
    bool stage(Phase);
    Io& io_;Faults& faults_;Journal& journal_;memory::vram::Arena& arena_;Upload& upload_;
    uint64_t epoch_=0,start_=0,last_=0;uint32_t enabled_=0;
    memory::vram::Token directory_{},small_{},instance_{},a_{},b_{};
    bool prepared_=false,attempted_=false;Error error_=Error::None;
    Closure closure_=Closure::NotEnabled;Phase phase_=Phase::Post;
};
}
