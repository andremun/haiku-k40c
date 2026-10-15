// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#include "fifo/PushBuffer.h"
#include "hw/RegisterIO.h"
#include "mmu/PageTable.h"
#include <cstdio>
#include <sstream>
#include <stdexcept>

static int failed = 0;
#define CHECK(c) do { if (!(c)) { ++failed; std::printf("FAIL: %s\n", #c); } } while (0)
template<class F> bool rejects(F f) {
    try { f(); } catch (const std::invalid_argument&) { return true; }
    return false;
}
int main() {
    // stoull accepts minus and negates modulo 2^64, so a range check alone
    // accepts -ffffffffffffffff as 1 (and -0 as 0).
    for (const char* line : {"R -ffffffffffffffff 0", "W 0 -ffffffffffffffff", "R -0 0", "W 0 -0"}) {
        CHECK(rejects([&] { std::istringstream in(line); k40::parseTrace(in); }));
    }
    CHECK(rejects([] { k40::fifo::encodeGpEntry((1ULL << 40) - 4, 8); }));
    auto entry = k40::fifo::encodeGpEntry((1ULL << 40) - 8, 8);
    auto decoded = k40::fifo::decodeGpEntry(entry);
    CHECK(decoded.addr == (1ULL << 40) - 8 && decoded.lengthBytes == 8);
    // Verify the settled S1 command through the existing encoder, not a
    // second handwritten packet format. docs/S1-PLAN.md:16-19.
    k40::fifo::PushBuffer pb;
    pb.begin(0, 0x08, 1);
    pb.data(0);
    CHECK(pb.finishedWords() == std::vector<uint32_t>({0x20010002, 0}));
    uint64_t next = 0x100000;
    k40::mmu::AddressSpace space([&](uint32_t bytes) { auto a = next; next += bytes; return a; });
    space.map(0, 0x400000, 0x1000, 12, k40::mmu::Target::VRAM);
    CHECK(rejects([&] { space.pte(0, 0, 0); }));
    CHECK(rejects([&] { space.pte(0, 64, 0); }));
    CHECK(space.translate(0xfff).value() == 0x400fff);
    std::printf("S1 boundary regressions: %d failures\n", failed);
    return failed ? 1 : 0;
}
