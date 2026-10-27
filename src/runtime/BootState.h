// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include <atomic>
#include <cstdint>
namespace k40::os { class NativeOwner; }
namespace k40::runtime::startup {
enum class BootState : uint8_t { Fresh, Running, Complete, Failed };
// The owner survives client recreation. There is no reset to Fresh.
class OncePerBoot {
    friend class Controller;
    friend class k40::os::NativeOwner;
    std::atomic<BootState> state_{BootState::Fresh};
    bool begin() {
        auto expected = BootState::Fresh;
        return state_.compare_exchange_strong(expected, BootState::Running, std::memory_order_acq_rel);
    }
    bool finish(bool success) {
        auto expected = BootState::Running;
        return state_.compare_exchange_strong(expected, success ? BootState::Complete : BootState::Failed,
                                             std::memory_order_acq_rel);
    }
public:
    BootState state() const { return state_.load(std::memory_order_acquire); }
};
}
