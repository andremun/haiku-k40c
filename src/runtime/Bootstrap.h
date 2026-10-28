// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "a7/ExecutionPermit.h"
#include <cstddef>
#include <cstdint>
#include "memory/Memory.h"
namespace k40::runtime {
struct PollLimit { uint64_t timeoutUs; uint32_t attempts; };
class BootstrapPort {
public:
    virtual ~BootstrapPort() = default;
    virtual bool hostSimulation() const = 0;
    virtual const a7::ExecutionPermit* a7Permit() const { return nullptr; }
    bool executionAllowed() const { return a7::permitted(hostSimulation(),a7Permit()); }
    virtual bool lock() = 0; // Must itself have a deadline; serializes selector+data.
    virtual void unlock() = 0;
    virtual uint64_t nowUs() = 0;
    virtual bool read32(uint32_t,uint32_t&) = 0;
    virtual bool write32(uint32_t,uint32_t) = 0;
};
struct OwnedVram { memory::VramPhysical base; uint64_t bytes; };
enum class RunlistTarget { Vram, NoncoherentHost };
// These SOURCE_ONLY chip operations are intentionally simulation-only until
// address ownership, stage policy, prerequisites and faults are integrated.
bool writeSlowWindow(BootstrapPort&,OwnedVram,uint64_t offset,const uint32_t*,size_t count);
bool readSlowWindow(BootstrapPort&,OwnedVram,uint64_t offset,uint32_t*,size_t count);
bool flushBar(BootstrapPort&,PollLimit);
// Two write-all/read-all passes catch aliases between chosen owned locations.
bool checkOwnedScratch(BootstrapPort&,OwnedVram,const uint64_t* offsets,size_t samples,PollLimit);
bool commitRunlist(BootstrapPort&,uint32_t runlistId,uint64_t address,RunlistTarget,uint32_t entries,PollLimit);
} // namespace k40::runtime
