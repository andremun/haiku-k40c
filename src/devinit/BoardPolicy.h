// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "devinit/Sha256.h"
namespace k40::devinit {
// no source: software exact-image permission size, ADR 004 and reference/vbios/README.md.
inline constexpr uint32_t approvedRomBytes = 181760;
struct BoardRule { uint32_t offset; uint8_t opcode; Digest rom; };
const Digest& approvedRomDigest();
const std::array<BoardRule, 6>& boardRules();
bool boardAllowed(const Digest&, uint32_t offset, uint8_t opcode);
}
