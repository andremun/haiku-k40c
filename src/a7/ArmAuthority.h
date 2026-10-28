// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memory/ArmedReference.h"
#include <cstddef>
#include <cstdint>
namespace k40::a7 {
// Fixed little-endian software wire protocol. This is not a device packet.
constexpr size_t requestBytes=128, grantBytes=192; // no source: software request/grant frame sizes, not hardware packets.
class ArmAuthority {
public:
    ArmAuthority(const uint8_t publicKey[32],const uint8_t packageNonce[32],const uint8_t instanceChallenge[16]);
    void request(const memory::ArmedReference&,uint8_t out[requestBytes]) const;
    bool accept(memory::ArmedReference&,const uint8_t*,size_t) const;
private:
    uint8_t key_[32],nonce_[32],challenge_[16];
};
}
