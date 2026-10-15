// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#include "runtime/S1Experiment.h"

namespace k40::runtime {
Result runS1(Backend& backend, const Limits& limits)
{
    Result result;
    if (limits.ringEntries < 2
        || (limits.ringEntries & (limits.ringEntries - 1))
        || !limits.timeoutUs || !limits.maxPolls) {
        result.primary = Error::InvalidConfig;
        return result; // No resources acquired, no backend calls.
    }
    uint64_t lastTime = backend.nowUs();
    const uint64_t start = lastTime;
    auto withinDeadline = [&]() {
        const uint64_t now = backend.nowUs();
        if (now < lastTime) {
            result.primary = Error::Clock;
            return false;
        }
        lastTime = now;
        // Subtraction avoids deadline overflow near UINT64_MAX.
        if (now - start >= limits.timeoutUs) {
            result.primary = Error::Timeout;
            return false;
        }
        return true;
    };
    auto experiment = [&]() {
        if (!backend.prepare()) {
            result.primary = Error::Prepare;
            return;
        }
        Snapshot initial;
        if (!backend.snapshot(initial)) {
            result.primary = Error::Observe;
            return;
        }
        if (initial.fault) {
            result.primary = Error::Fault;
            return;
        }
        // A single-entry experiment starts from an empty, valid ring.
        if (initial.get >= limits.ringEntries || initial.put != initial.get) {
            result.primary = Error::Baseline;
            return;
        }
        result.initialGet = initial.get;
        result.targetPut = (initial.get + 1) & (limits.ringEntries - 1);
        if (!withinDeadline()) return;
        if (!backend.publishNop(initial.put, result.targetPut)) {
            result.primary = Error::Publish;
            return;
        }
        // Expensive publication cannot silently exhaust the submission budget.
        if (!withinDeadline()) return;
        if (!backend.setPut(result.targetPut)) {
            result.primary = Error::Submit;
            return;
        }
        while (result.polls < limits.maxPolls) {
            if (!withinDeadline()) return;
            Snapshot current;
            ++result.polls;
            if (!backend.snapshot(current)) {
                result.primary = Error::Observe;
                return;
            }
            if (!withinDeadline()) return;
            if (current.fault) {
                result.primary = Error::Fault;
                return;
            }
            if (current.put != result.targetPut || current.get >= limits.ringEntries
                || (current.get != result.initialGet && current.get != result.targetPut)) {
                result.primary = Error::UnexpectedGet;
                return;
            }
            if (current.get == result.targetPut) {
                result.progressed = true;
                return;
            }
            backend.pause();
        }
        result.primary = Error::Timeout;
    };
    experiment();
    result.quiesced = backend.quiesce();
    if (!result.quiesced) {
        result.cleanup = Error::Quiesce;
        return result; // Deliberately retain possibly referenced resources.
    }
    Snapshot final;
    if (!backend.snapshot(final)) result.cleanup = Error::Observe;
    else if (final.fault) result.cleanup = Error::Fault;
    result.released = backend.release();
    if (!result.released && result.cleanup == Error::None)
        result.cleanup = Error::Release;
    return result;
}
} // namespace k40::runtime
