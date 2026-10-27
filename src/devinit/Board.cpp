// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "devinit/Board.h"
#include <cstring>

namespace k40::devinit {
PolicyBackend::PolicyBackend(const uint8_t* rom, uint32_t size, Backend& registers, BoardTransport& ports)
    : rom_(rom && size == approvedRomBytes ? std::vector<uint8_t>(rom, rom + size) : std::vector<uint8_t>{}),
      digest_(sha256(rom_.data(), uint32_t(rom_.size()))),
      approved_(rom_.size() == approvedRomBytes && digest_ == approvedRomDigest()),
      registers_(registers), ports_(ports), helpers_(registers, ports) {}

bool PolicyBackend::hostSimulation() const { return registers_.hostSimulation() && ports_.hostSimulation(); }
uint64_t PolicyBackend::nowUs() { return hostSimulation() && approved_ ? registers_.nowUs() : 0; }
bool PolicyBackend::delayUs(uint64_t us) { return hostSimulation() && approved_ && registers_.delayUs(us); }
bool PolicyBackend::read32(uint32_t reg, uint32_t& value)
{
    return hostSimulation() && approved_ && registers_.read32(reg, value);
}
bool PolicyBackend::write32(uint32_t reg, uint32_t value)
{
    return hostSimulation() && approved_ && registers_.write32(reg, value);
}
void PolicyBackend::trace(uint32_t offset, uint8_t op, bool active)
{
    if (hostSimulation() && approved_) registers_.trace(offset, op, active);
}
bool PolicyBackend::board(uint8_t op, uint32_t offset, const uint8_t* bytes, uint32_t length, bool active)
{
    const RomView view{rom_.data(), uint32_t(rom_.size())};
    boardError_ = Error::Denied;
    if (!hostSimulation()) boardError_ = Error::HardwareDisabled;
    else if (approved_ && boardAllowed(digest_, offset, op) && length && bytes
             && view.contains(offset, length) && bytes[0] == op
             && std::memcmp(bytes, view.data + offset, length) == 0)
        boardError_ = helpers_.execute(view, bytes, length, active);
    ports_.audit(offset, op, active, boardError_);
    return boardError_ == Error::None;
}
Result PolicyBackend::run(uint32_t start, Tables tables, Limits limits, uint8_t flags)
{
    boardError_ = Error::None;
    if (!hostSimulation()) return {Error::HardwareDisabled, start, 0};
    if (!approved_) return {Error::Denied, start, 0};
    auto result = Interpreter(rom_.data(), uint32_t(rom_.size()), tables, *this).run(start, limits, flags);
    if (result.error == Error::Denied && boardError_ != Error::None) result.error = boardError_;
    return result;
}
}
