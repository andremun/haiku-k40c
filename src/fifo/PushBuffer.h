// PushBuffer.h — GPFIFO push-buffer encoding and ring model.
// Distributed under the terms of the MIT License.
//
// Sources:
//   Header encoding: reference/mesa/.../nvc0_winsys.h NVC0_FIFO_PKHDR_SQ/NL/IL/1I (lines 65-88)
//   GPFIFO entry:    reference/nouveau/nouveau_dma.c nv50_dma_push (lines 82-84)
//   Max length:      reference/nouveau/nouveau_dma.h NV50_DMA_PUSH_MAX_LENGTH (line 50)
//   USERD offsets:   reference/nouveau/nouveau_dma.c (lines 92, 104)
//   Channel 0x4c:    docs/hardware-model/chan.md (word 0x4c)

#pragma once

#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace k40 {
namespace fifo {

// ---- Header type constants (from nvc0_winsys.h) ----
// NV50_DMA_PUSH_MAX_LENGTH (nouveau_dma.h:50)
constexpr uint32_t kPushMaxLength = 0x7fffff;

// USERD offsets (nouveau_dma.c:92, 104)
constexpr unsigned kUserdGpGet = 0x88;
constexpr unsigned kUserdGpPut = 0x8c;  // nouveau_dma.c:92

// GPFIFO entry size: two 32-bit words — no source: derived from two wr32 in nouveau_dma.c:82-83
constexpr unsigned kGpEntryBytes = 8;

// Header encoding
enum class HeaderType { INCREASING, NON_INCREASING, IMMEDIATE, INCREASE_ONCE };

uint32_t encodeHeader(HeaderType type, unsigned subc, uint32_t method,
                      unsigned count);

struct Header {
    HeaderType type;
    unsigned subc;
    uint32_t method;
    unsigned count;
};

Header decodeHeader(uint32_t word);

// Push-buffer builder
class PushBuffer {
public:
    void bindObject(unsigned subc, uint32_t classId);
    void begin(unsigned subc, uint32_t method, unsigned count);
    void beginNonIncreasing(unsigned subc, uint32_t method, unsigned count);
    void beginIncreaseOnce(unsigned subc, uint32_t method, unsigned count);
    void immediate(unsigned subc, uint32_t method, uint32_t data);
    void data(uint32_t value);

    std::vector<uint32_t> words() const;
    unsigned pending() const;
    unsigned sizeBytes() const;

private:
    struct Pending {
        HeaderType type;
        unsigned subc;
        uint32_t method;
        unsigned count;      // remaining
        unsigned offset;     // index in buffer where the header word sits
    };

    std::vector<uint32_t> buffer_;
    // When a header is active, these track state
    bool hasPending_ = false;
    Pending pending_;
};

// Decode a push-buffer back into method entries
struct Method {
    unsigned subc;
    uint32_t method;
    uint32_t value;
};

std::vector<Method> decodeBuffer(const std::vector<uint32_t>& words);

// GPFIFO entry encoding (nouveau_dma.c:82-84)
struct GpEntry {
    uint32_t word0, word1;
};

GpEntry encodeGpEntry(uint64_t addr, uint32_t lengthBytes,
                      bool noPrefetch = false);

struct GpInfo {
    uint64_t addr;
    uint32_t lengthBytes;
    bool noPrefetch;
};

GpInfo decodeGpEntry(const GpEntry& e);

// GPFIFO ring buffer
class GpFifo {
public:
    explicit GpFifo(unsigned entries);

    unsigned push(uint64_t addr, uint32_t lengthBytes,
                  bool noPrefetch = false, unsigned get = 0);
    unsigned put() const;
    unsigned entries() const;
    unsigned log2Entries() const;
    unsigned freeEntries(unsigned get) const;
    const std::vector<uint32_t>& words() const;

    // Word 0x4c of the channel RAMFC block:
    // upper 32 bits of ring address in bits 0-31, log2 entries in bits 16-31.
    // Formula: (log2 << 16) | (upper32_of_addr)
    uint32_t ramfcWord4c(uint64_t ringAddr) const;

private:
    unsigned entries_;
    unsigned log2_;
    unsigned put_;
    std::vector<uint32_t> ring_;  // two words per entry
};

}  // namespace fifo
}  // namespace k40
