// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include <array>
#include <cstdint>

namespace k40::devinit {
using Digest = std::array<uint8_t, 32>;
// FIPS 180-4 sections 4.1.2, 4.2.2, 5.1.1, 5.3.3, and 6.2.
// Input must cover size bytes. A null pointer is valid only for size zero.
Digest sha256(const uint8_t* data, uint32_t size);
}
