// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "devinit/PostImage.h"
#include "devinit/I2c.h"
namespace k40::devinit {
enum class PostI2c { TransactionCallback, DedicatedPins };
// Freestanding executor adapter, gated by simulation or the resident A7 permit. Callers serialize
// selection/execution, and keep the image and both transports alive throughout.
class BoundPost final : private Backend, private BoardTransport {
public:
    BoundPost(PostImage& image, Backend& registers, BoardTransport& ports,
              PostI2c mode = PostI2c::TransactionCallback)
        : image_(image), registers_(registers), ports_(ports), helpers_(*this,*this),
          i2c_(*this,ports), mode_(mode) {}
    BoundPost(const BoundPost&) = delete;
    BoundPost& operator=(const BoundPost&) = delete;
    // Separate host preinit: derive the dedicated bus, then write its init value.
    // One preparation attempt per image, no retry or implicit init during POST.
    bool dedicatedBus(I2cBus&) const; // Derive only from the immutable approved image.
    Error prepareI2c();
    I2cResult i2cResult() const { return i2c_.result(); }
    Result runPost(Limits limits = {}); // No caller root, table pointer, digest, or RAM index.
private:
    bool hostSimulation() const override { return registers_.hostSimulation() && ports_.hostSimulation(); }
    const a7::ExecutionPermit* a7Permit() const override {
        return !registers_.hostSimulation() && !ports_.hostSimulation()
            && registers_.a7Permit()==ports_.a7Permit()?registers_.a7Permit():nullptr;
    }
    bool executionAllowed() const { return a7::permitted(hostSimulation(),a7Permit()); }
    uint64_t nowUs() override { return registers_.nowUs(); }
    bool delayUs(uint64_t) override;
    bool read32(uint32_t, uint32_t&) override;
    bool write32(uint32_t, uint32_t) override;
    bool read8(uint32_t, uint8_t&) override;
    bool write8(uint32_t, uint8_t) override;
    bool i2cWrite(const I2cBus&, uint8_t, uint8_t, uint8_t) override;
    bool board(uint8_t, uint32_t, const uint8_t*, uint32_t, bool) override;
    void trace(uint32_t, uint8_t, bool) override;
    bool diagnosticsHealthy() const override {return registers_.diagnosticsHealthy();}
    void pollSample(uint32_t pc,uint8_t index,uint32_t value,bool met) override {
        registers_.pollSample(pc,index,value,met);
    }
    bool guard();
    bool permission(uint32_t reg, unsigned width, bool write);
    PostImage& image_;
    Backend& registers_;
    BoardTransport& ports_;
    BoardHelpers helpers_;
    DedicatedI2c i2c_;
    const PostI2c mode_;
    uint32_t pin_ = 0;
    unsigned sensorPairs_ = 0;
    bool preparing_ = false, prepared_ = false, inI2c_ = false;
    uint32_t pc_ = 0;
    uint64_t started_ = 0, last_ = 0, timeout_ = 0;
    bool running_ = false, active_ = false;
    Error error_ = Error::None;
};
}
