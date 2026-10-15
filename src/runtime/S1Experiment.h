// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#pragma once
#include <cstdint>

namespace k40::runtime {

// Software orchestration contract, not a hardware register specification.
// No exceptions, allocation, STL containers or GPU addresses cross this API.
// Backend owns all storage, address translation and chip-specific operations.
enum class Error {
    None, InvalidConfig, Prepare, Baseline, Publish, Submit, Observe,
    Fault, UnexpectedGet, Timeout, Clock, Quiesce, Release
};

struct Snapshot {
    uint32_t get = 0;
    uint32_t put = 0;
    // Backend must collect all reviewed relevant raw fault sources, even when
    // interrupts are masked. A failed/incomplete read must return false.
    bool fault = false;
};

struct Limits {
    uint32_t ringEntries;
    uint64_t timeoutUs;
    uint32_t maxPolls; // Independently bounds iterations if the host clock stalls.
};

struct Result {
    Error primary = Error::None;
    Error cleanup = Error::None;
    uint32_t polls = 0;
    uint32_t initialGet = 0;
    uint32_t targetPut = 0;
    bool progressed = false;
    bool quiesced = false;
    bool released = false;
    bool success() const {
        return primary == Error::None && cleanup == Error::None
            && progressed && quiesced && released;
    }
};

class Backend {
public:
    virtual ~Backend() = default;
    // Monotonic HOST microseconds, never the GPU timer.
    virtual uint64_t nowUs() = 0;
    // Each call must itself be bounded. prepare rejects missing readiness,
    // unverified DMA addresses, incompatible page sizes or unsafe ownership.
    // It may partially acquire resources: cleanup runs even on failure.
    virtual bool prepare() = 0;
    virtual bool snapshot(Snapshot&) = 0;
    // Stage exactly one reviewed host NOP in owned pushbuffer/ring storage,
    // using the current ring slot. Upload/flush/readback must complete before
    // returning true. This must NOT change PUT or kick the channel.
    virtual bool publishNop(uint32_t slot, uint32_t newPut) = 0;
    // Separate commit point. Failure may still mean the write reached hardware.
    virtual bool setPut(uint32_t newPut) = 0;
    virtual void pause() = 0;
    // Block scheduling, preempt/remove the channel and wait for quiescence.
    // Failure MUST retain all possibly GPU-referenced storage for recovery.
    virtual bool quiesce() = 0;
    // Called only after quiescence and a final fault snapshot.
    virtual bool release() = 0;
};

Result runS1(Backend&, const Limits&);
} // namespace k40::runtime
