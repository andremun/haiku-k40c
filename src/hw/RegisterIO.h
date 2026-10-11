// RegisterIO.h — register access abstraction
// Task D1: interface, mock, trace replay.
// Distributed under the terms of the MIT License.

#pragma once

#include <cstdint>
#include <functional>
#include <istream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace k40 {

struct Access {
    enum Op { READ, WRITE };
    Op op;
    uint32_t offset;
    uint32_t value;
};

class RegisterIO {
public:
    virtual ~RegisterIO() = default;
    virtual uint32_t read32(uint32_t offset) = 0;
    virtual void write32(uint32_t offset, uint32_t value) = 0;
    uint32_t mask32(uint32_t offset, uint32_t mask, uint32_t value);
};

class MockMMIO : public RegisterIO {
public:
    explicit MockMMIO(uint32_t size);
    void poke(uint32_t offset, uint32_t value);
    uint32_t peek(uint32_t offset);
    std::vector<Access> log() const;
    void clearLog();
    void onRead(uint32_t offset, std::function<uint32_t(uint32_t)> hook);
    void onWrite(uint32_t offset,
                 std::function<void(MockMMIO&, uint32_t)> hook);

    uint32_t read32(uint32_t offset) override;
    void write32(uint32_t offset, uint32_t value) override;

private:
    void checkBounds(uint32_t offset) const;

    uint32_t fSize;
    std::vector<uint32_t> fMemory;
    std::vector<Access> fLog;
    std::map<uint32_t, std::function<uint32_t(uint32_t)>> fReadHooks;
    std::map<uint32_t, std::function<void(MockMMIO&, uint32_t)>> fWriteHooks;
};

class TraceMismatch : public std::runtime_error {
public:
    TraceMismatch(size_t index, uint32_t offset);
    size_t index() const;

private:
    size_t fIndex;
};

class TraceMMIO : public RegisterIO {
public:
    explicit TraceMMIO(std::vector<Access> expected);

    uint32_t read32(uint32_t offset) override;
    void write32(uint32_t offset, uint32_t value) override;
    bool done() const;
    size_t position() const;

private:
    std::vector<Access> fExpected;
    size_t fPos;
};

std::vector<Access> parseTrace(std::istream& in);
std::string formatTrace(const std::vector<Access>& t);

} // namespace k40
