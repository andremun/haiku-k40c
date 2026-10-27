// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "devinit/BoardPolicy.h"
namespace k40::devinit {
namespace {
// Permission identity: docs/decisions/004-board-operations-and-review.md.
constexpr Digest allowedRom = { // no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.
    0xae,0xcb,0x0b,0x5f,0xa4,0x66,0xf6,0x4e,0x26,0x51,0xa5,0x51,0xa3,0xca,0xd5,0x7c, // no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.
    0xcc,0xbd,0xed,0xd9,0x29,0xe3,0x99,0x6f,0x54,0x22,0x01,0xaf,0x06,0xff,0x1f,0x54, // no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.
};
constexpr std::array<BoardRule, 6> rules = {{ // no source: software ROM permission identity/size from ADR 004 and reference/vbios/README.md.
    {0x8506, 0x69, allowedRom}, {0x850b, 0x53, allowedRom}, // nvkm/subdev/bios/init.c:2269,2252; offsets from ADR 004.
    {0x85e8, 0x53, allowedRom}, {0x862f, 0x4d, allowedRom}, // nvkm/subdev/bios/init.c:2252,2246; offsets from ADR 004.
    {0x89b7, 0xa9, allowedRom}, {0xab8d, 0x4d, allowedRom}, // nvkm/subdev/bios/init.c:2297,2246; offsets from ADR 004.
}};

}
const Digest& approvedRomDigest() { return allowedRom; }
const std::array<BoardRule, 6>& boardRules() { return rules; }
bool boardAllowed(const Digest& rom, uint32_t offset, uint8_t opcode)
{
    for (const auto& rule : rules)
        if (rule.offset == offset && rule.opcode == opcode && rule.rom == rom) return true;
    return false;
}

}
