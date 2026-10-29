// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memstage/Mapper.h"
namespace k40::memstage {
enum class Step:uint8_t {None,Discovery,Arena,Baselines,Preflight,Debug,Data,Tables};
class Experiment {
public:
    Experiment(Io& io,Faults& faults,memory::vram::Arena& arena,Upload& upload,Mapper& mapper,uint64_t owner,uint64_t epoch,uint64_t vram,uint64_t aperture)
        :io_(io),faults_(faults),arena_(arena),upload_(upload),mapper_(mapper),owner_(owner),epoch_(epoch),vram_(vram),aperture_(aperture){}
    bool run();
    Step step() const{return step_;}
    const memory::vram::Probe& probe() const{return probe_;}
    uint64_t known() const{return known_;}
private:
    bool work();bool discover();
    Io& io_;Faults& faults_;memory::vram::Arena& arena_;Upload& upload_;Mapper& mapper_;
    uint64_t owner_,epoch_,vram_,aperture_,known_=0;memory::vram::Probe probe_{};
    Step step_=Step::None;bool attempted_=false;
};
}
