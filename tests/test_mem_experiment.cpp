// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memstage/Experiment.h"
#include "memstage_device.h"
#include <cstdio>
struct Injection:Device {
    k40::memstage::Experiment* experiment=nullptr;k40::memstage::Step fail=k40::memstage::Step::None;
    unsigned denied=0;bool reads=true;
    bool read32(uint32_t reg,uint32_t& value) override {
        if(reads && experiment->step()==fail){++denied;return false;}
        return Device::read32(reg,value);
    }
    bool write32(uint32_t reg,uint32_t value) override {
        if(!reads && experiment->step()==fail){++denied;return false;}
        return Device::write32(reg,value);
    }
};
int main()
{
    using namespace k40::memstage;unsigned cases=0;
    for(unsigned failure=0;failure<=unsigned(Step::Tables);++failure) {
        for(bool onRead:{true,false}) {
            if(!onRead && failure<unsigned(Step::Debug))continue;
            Injection io;Journal journal;Arena arena;Faults faults(io,journal,8);Upload upload(io,faults,journal,arena);Mapper mapper(io,faults,journal,arena,upload,8);
            Experiment experiment(io,faults,arena,upload,mapper,2,8,11520ULL*1048576,256*1048576);io.experiment=&experiment;
            io.fail=Step(failure);io.reads=onRead;
            const bool passed=experiment.run();assert(passed==(failure==0 || failure==unsigned(Step::Arena)));
            if(!passed){assert(!arena.healthy() && io.denied==1);assert(experiment.step()==Step(failure));}
            const auto writes=io.writes.size();assert(!experiment.run() && io.writes.size()==writes);++cases;
        }
    }
    {Injection io;Journal journal;Arena arena;Faults faults(io,journal,8);Upload upload(io,faults,journal,arena);Mapper mapper(io,faults,journal,arena,upload,8);
     Experiment experiment(io,faults,arena,upload,mapper,2,8,11521ULL*1048576,256*1048576);io.experiment=&experiment;
     assert(!experiment.run() && experiment.step()==Step::Arena && io.writes.empty());++cases;}
    std::printf("memory experiment: %u production-controller stop/replay cases pass; HOST_ONLY\n",cases);
}
