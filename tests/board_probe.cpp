// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Offline ROM/helper probe. The ROM is never copied to the output.
#include "board_fake.h"
#include <fstream>
#include <iostream>
#include <iterator>
#include <stdexcept>
#include <string>

static void require(bool condition, const char* message)
{
    if (!condition) throw std::runtime_error(message);
}
static void printDigest(const Digest& value)
{
    for (auto byte : value) std::printf("%02x", byte);
}
static std::vector<uint8_t> load(const char* path)
{
    std::ifstream input(path, std::ios::binary);
    require(bool(input), "input file absent");
    input.seekg(0, std::ios::end);
    const std::streamoff size = input.tellg();
    require(size >= 0 && size <= 1024 * 1024, "input exceeds one MiB host probe limit");
    input.seekg(0);
    std::vector<uint8_t> bytes(static_cast<size_t>(size));
    if (size) {
        input.read(reinterpret_cast<char*>(bytes.data()), size);
        require(input.gcount() == size, "short input read");
    }
    return bytes;
}
static uint32_t instructionSize(const std::vector<uint8_t>& rom, const BoardRule& rule)
{
    require(rule.offset + 4 <= rom.size(), "instruction out of bounds");
    switch (rule.opcode) {
    case 0x69: return 5;
    case 0x53: return 3;
    case 0x4d: return 4 + 2 * rom[rule.offset + 3];
    case 0xa9: return 2 + rom[rule.offset + 1];
    default: throw std::runtime_error("unexpected policy opcode");
    }
}
static void exercisePolicy(std::vector<uint8_t> rom)
{
    BoardFake fake;
    PolicyBackend policy(rom.data(), uint32_t(rom.size()), fake, fake);
    require(policy.approved(), "ROM is not approved by ADR 004");
    unsigned allowed = 0;
    for (const auto& rule : boardRules()) {
        require(policy.board(rule.opcode, rule.offset, rom.data() + rule.offset,
                             instructionSize(rom, rule), true), "approved board operation failed");
        ++allowed;
    }
    require(allowed == 6, "policy must contain six instructions");
    const auto first = boardRules()[0];
    auto length = instructionSize(rom, first);
    std::vector<uint8_t> original(rom.begin() + first.offset, rom.begin() + first.offset + length);
    rom[first.offset + 4] ^= 1;
    require(policy.approved(), "owned ROM changed with the caller buffer");
    require(!policy.board(first.opcode, first.offset, rom.data() + first.offset, length, true),
            "mutated caller instruction accepted");
    require(policy.board(first.opcode, first.offset, original.data(), length, true),
            "owned snapshot was not retained");
    PolicyBackend changed(rom.data(), uint32_t(rom.size()), fake, fake);
    require(!changed.approved() && changed.run(first.offset).error == Error::Denied,
            "changed ROM accepted");
    require(!policy.board(first.opcode, first.offset, original.data(), length - 1, true),
            "truncated instruction accepted");
    require(!policy.board(first.opcode, first.offset, nullptr, length, true), "null payload accepted");
    require(!policy.board(first.opcode, 0xffffffff, nullptr, 0xffffffff, true), "overflow accepted");
    require(policy.run(0x89c2).error == Error::Denied, "Linux-skipped GPIO operation accepted");
    BoardFake failure;
    failure.failAt = 0;
    // Restore the caller buffer to the approved ROM before binding another adapter.
    rom[first.offset + 4] ^= 1;
    PolicyBackend failing(rom.data(), uint32_t(rom.size()), failure, failure);
    require(failing.run(0xab8d).error == Error::Io, "I2C failure did not stop the interpreter");
    BoardFake timed;
    PolicyBackend limited(rom.data(), uint32_t(rom.size()), timed, timed);
    require(limited.run(first.offset, {}, {100,32,15000}, 3).error == Error::Timeout,
            "skipped IO waits did not reach the interpreter deadline");
    require(timed.events.size() == 2 && timed.events[0].kind == 'D' && timed.events[1].kind == 'D',
            "skipped IO performed register access");
    BoardFake hardware;
    hardware.simulation = false;
    PolicyBackend forbidden(rom.data(), uint32_t(rom.size()), hardware, hardware);
    require(forbidden.run(first.offset).error == Error::HardwareDisabled && hardware.events.empty(),
            "hardware backend reached helpers");
    std::printf("%u\n", allowed);
}

int main(int argc, char** argv)
{
    try {
        require(argc >= 2, "usage: board_probe --rules | --sha FILE | --policy ROM | --io ROM [--skip]");
        const std::string mode = argv[1];
        if (mode == "--rules") {
            require(argc == 2, "rules takes no input");
            for (const auto& rule : boardRules()) {
                printDigest(rule.rom);
                std::printf(" %x %x\n", rule.offset, rule.opcode);
            }
            return 0;
        }
        require(argc >= 3, "input file required");
        auto rom = load(argv[2]);
        if (mode == "--sha") { printDigest(sha256(rom.data(), uint32_t(rom.size()))); std::puts(""); return 0; }
        if (mode == "--policy") { exercisePolicy(rom); return 0; }
        require(mode == "--io" && (argc == 3 || (argc == 4 && std::string(argv[3]) == "--skip")),
                "unsupported probe operation");
        BoardFake fake;
        uint32_t reg = 0, value = 0;
        while (std::cin >> std::hex >> reg >> value) fake.regs[reg] = value;
        PolicyBackend policy(rom.data(), uint32_t(rom.size()), fake, fake);
        require(policy.approved(), "ROM is not approved by ADR 004");
        const bool active = argc == 3;
        require(policy.board(0x69, 0x8506, rom.data() + 0x8506, 5, active), "IO helper refused");
        if (active)
            require(policy.board(0x53, 0x850b, rom.data() + 0x850b, 3, true), "following ZM_CR refused");
        for (const auto& event : fake.events)
            std::printf("%c %u %x %x\n", event.kind, event.width, event.address, event.value);
        return 0;
    } catch (const std::exception& error) {
        std::fprintf(stderr, "board_probe: %s\n", error.what());
        return 1;
    }
}
