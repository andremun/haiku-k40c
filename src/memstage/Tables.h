// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memory/VramArena.h"
namespace k40::memstage::tables {
// gk104 17/12 format; reusable by future channel VMM encoding, not channel proof.
bool pte(memory::VramPhysical,uint64_t&);
bool smallDirectory(memory::VramPhysical,uint64_t&);
bool instance(memory::VramPhysical directory,uint64_t aperture,uint64_t& base,uint64_t& limit);
bool indices(memory::vram::BarVirtual,uint64_t aperture,uint32_t& directory,uint32_t& small);
void littleEndian(uint64_t,uint8_t bytes[8]);
}
