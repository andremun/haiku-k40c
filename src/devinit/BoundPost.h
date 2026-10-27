// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "devinit/PostImage.h"
#include "devinit/Board.h"
namespace k40::devinit {
// Host-only executor adapter. PostImage itself is freestanding. Callers serialize
// selection/execution, and keep the image and both transports alive throughout.
class BoundPost final : private Backend, private BoardTransport {
public:
    BoundPost(PostImage& image, Backend& registers, BoardTransport& ports)
        : image_(image), registers_(registers), ports_(ports), helpers_(*this,*this) {}
    Result runPost(Limits limits = {}); // No caller root, table pointer, digest, or RAM index.
private:
    bool hostSimulation() const override { return registers_.hostSimulation() && ports_.hostSimulation(); }
    uint64_t nowUs() override { return registers_.nowUs(); }
    bool delayUs(uint64_t) override;
    bool read32(uint32_t, uint32_t&) override;
    bool write32(uint32_t, uint32_t) override;
    bool read8(uint32_t, uint8_t&) override;
    bool write8(uint32_t, uint8_t) override;
    bool i2cWrite(const I2cBus&, uint8_t, uint8_t, uint8_t) override;
    bool board(uint8_t, uint32_t, const uint8_t*, uint32_t, bool) override;
    void trace(uint32_t, uint8_t, bool) override;
    bool guard();
    bool permission(uint32_t reg, unsigned width, bool write);
    PostImage& image_;
    Backend& registers_;
    BoardTransport& ports_;
    BoardHelpers helpers_;
    uint32_t pc_ = 0;
    uint64_t started_ = 0, last_ = 0, timeout_ = 0;
    bool running_ = false, active_ = false;
    Error error_ = Error::None;
};
}
