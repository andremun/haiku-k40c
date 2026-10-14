// PushBuffer.cpp — GPFIFO push-buffer encoding and ring model.
// Distributed under the terms of the MIT License.
//
// Sources:
//   Header encoding: reference/mesa/.../nvc0_winsys.h NVC0_FIFO_PKHDR_SQ/NL/IL/1I (lines 65-88)
//   GPFIFO entry:    reference/nouveau/nouveau_dma.c nv50_dma_push (lines 82-84)
//   Max length:      reference/nouveau/nouveau_dma.h NV50_DMA_PUSH_MAX_LENGTH (line 50)
//   USERD offsets:   reference/nouveau/nouveau_dma.c (lines 92, 104)
//   Channel 0x4c:    docs/hardware-model/chan.md (word 0x4c)

#include "fifo/PushBuffer.h"

#include <algorithm>

namespace k40 {
namespace fifo {

// ---- Header encoding (nvc0_winsys.h:65-88) ----
// SQ: 0x20000000 | (size << 16) | (subc << 13) | (mthd >> 2)
// NI: 0x60000000 | (size << 16) | (subc << 13) | (mthd >> 2)
// IL: 0x80000000 | (data << 16) | (subc << 13) | (mthd >> 2)
// 1I: 0xa0000000 | (size << 16) | (subc << 13) | (mthd >> 2)

uint32_t encodeHeader(HeaderType type, unsigned subc, uint32_t method,
                      unsigned count)
{
    // Validate subc (0-7, 3 bits)
    if (subc > 7)
        throw std::invalid_argument("subc must be 0-7");

    // Validate method: must be multiple of 4, fits in 13 bits after shift
    // — no source: 0x7ffc is max 13-bit value aligned to 4; nvc0_winsys.h shifts mthd >> 2
    if (method & 3 || method > 0x7ffc)
        throw std::invalid_argument("method must be multiple of 4, <= 0x7ffc");

    // Validate count: max 13 bits (0x1fff)
    // — no source: 0x1fff is max 13-bit value for the count field;
    //   nvc0_winsys.h uses (size << 16) with 13-bit field
    if (count > 0x1fff)
        throw std::invalid_argument("count must be <= 0x1fff");

    // Base depending on type (nvc0_winsys.h:68, 74, 81, 87)
    uint32_t base = 0;
    switch (type) {
        case HeaderType::INCREASING:     base = 0x20000000u; break;   // nvc0_winsys.h:68
        case HeaderType::NON_INCREASING: base = 0x60000000u; break;   // nvc0_winsys.h:74
        case HeaderType::IMMEDIATE:      base = 0x80000000u; break;   // nvc0_winsys.h:81
        case HeaderType::INCREASE_ONCE:  base = 0xa0000000u; break;   // nvc0_winsys.h:87
    }

    // All types: (count/data << 16) | (subc << 13) | (method >> 2)
    return base | (count << 16) | (subc << 13) | (method >> 2);
}

Header decodeHeader(uint32_t word)
{
    Header h;

    // Determine type from top 3 bits (nvc0_winsys.h:68,74,81,87):
    //   0x20.. → top3=1 → INCREASING
    //   0x60.. → top3=3 → NON_INCREASING
    //   0x80.. → top3=4 → IMMEDIATE
    //   0xa0.. → top3=5 → INCREASE_ONCE
    uint32_t top3 = (word >> 29) & 7;
    switch (top3) {
        case 1:  h.type = HeaderType::INCREASING;     break;
        case 3:  h.type = HeaderType::NON_INCREASING; break;
        case 4:  h.type = HeaderType::IMMEDIATE;      break;
        case 5:  h.type = HeaderType::INCREASE_ONCE;  break;
        default: throw std::invalid_argument("invalid header type");
    }

    h.subc = (word >> 13) & 7;
    h.method = (word & 0x1fff) << 2;  // nvc0_winsys.h:68 — 13-bit method mask
    h.count = (word >> 16) & 0x1fff;   // nvc0_winsys.h:68 — 13-bit count mask

    return h;
}

// ---- PushBuffer ----

void PushBuffer::bindObject(unsigned subc, uint32_t classId)
{
    // F6: refuse binding while a packet is pending (like other begin... functions)
    if (hasPending_)
        throw std::logic_error("data still pending");

    // Method 0 with the class ID (like Mesa does first on each subchannel)
    uint32_t header = encodeHeader(HeaderType::INCREASING, subc, 0, 1);
    buffer_.push_back(header);
    buffer_.push_back(classId);
}

void PushBuffer::begin(unsigned subc, uint32_t method, unsigned count)
{
    if (count == 0)
        throw std::invalid_argument("count must be > 0");
    if (hasPending_)
        throw std::logic_error("data still pending");

    uint32_t header = encodeHeader(HeaderType::INCREASING, subc, method, count);
    pending_ = { HeaderType::INCREASING, subc, method, count,
                 static_cast<unsigned>(buffer_.size()) };
    hasPending_ = true;
    buffer_.push_back(header);
}

void PushBuffer::beginNonIncreasing(unsigned subc, uint32_t method,
                                    unsigned count)
{
    if (count == 0)
        throw std::invalid_argument("count must be > 0");
    if (hasPending_)
        throw std::logic_error("data still pending");

    uint32_t header =
        encodeHeader(HeaderType::NON_INCREASING, subc, method, count);
    pending_ = { HeaderType::NON_INCREASING, subc, method, count,
                 static_cast<unsigned>(buffer_.size()) };
    hasPending_ = true;
    buffer_.push_back(header);
}

void PushBuffer::beginIncreaseOnce(unsigned subc, uint32_t method,
                                   unsigned count)
{
    if (count == 0)
        throw std::invalid_argument("count must be > 0");
    if (hasPending_)
        throw std::logic_error("data still pending");

    uint32_t header =
        encodeHeader(HeaderType::INCREASE_ONCE, subc, method, count);
    pending_ = { HeaderType::INCREASE_ONCE, subc, method, count,
                 static_cast<unsigned>(buffer_.size()) };
    hasPending_ = true;
    buffer_.push_back(header);
}

void PushBuffer::immediate(unsigned subc, uint32_t method, uint32_t data)
{
    if (hasPending_)
        throw std::logic_error("data still pending");

    // Immediate: the count field IS the data value
    uint32_t header = encodeHeader(HeaderType::IMMEDIATE, subc, method, data);
    buffer_.push_back(header);
}

void PushBuffer::data(uint32_t value)
{
    if (!hasPending_)
        throw std::logic_error("no pending header for data");

    buffer_.push_back(value);
    pending_.count--;
    if (pending_.count == 0)
        hasPending_ = false;
}

std::vector<uint32_t> PushBuffer::words() const
{
    return buffer_;
}

std::vector<uint32_t> PushBuffer::finishedWords() const
{
    // F6: throw if there are still pending data words
    if (hasPending_)
        throw std::logic_error("packet not finished");
    return buffer_;
}

unsigned PushBuffer::pending() const
{
    return hasPending_ ? pending_.count : 0;
}

unsigned PushBuffer::sizeBytes() const
{
    return static_cast<unsigned>(buffer_.size()) * 4;
}

// ---- decodeBuffer ----

std::vector<Method> decodeBuffer(const std::vector<uint32_t>& words)
{
    std::vector<Method> methods;
    if (words.empty())
        return methods;

    unsigned i = 0;
    while (i < words.size()) {
        Header h = decodeHeader(words[i]);
        i++;  // skip header word

        // IMMEDIATE type: count field IS the data value, no data words follow
        if (h.type == HeaderType::IMMEDIATE) {
            methods.push_back({ h.subc, h.method, h.count });
            continue;
        }

        // We need h.count data words
        if (i + h.count > words.size())
            throw std::invalid_argument("buffer ends inside a method");

        for (unsigned j = 0; j < h.count; j++) {
            Method m;
            m.subc = h.subc;
            // Increasing: method + 4*j
            // Non-increasing: same method
            // Increase-once: method for first word, method+4 for rest
            switch (h.type) {
                case HeaderType::INCREASING:
                    m.method = h.method + 4 * j;
                    break;
                case HeaderType::NON_INCREASING:
                    m.method = h.method;
                    break;
                case HeaderType::INCREASE_ONCE:
                    m.method = (j == 0) ? h.method : h.method + 4;
                    break;
                default:
                    m.method = h.method;
                    break;
            }
            m.value = words[i + j];
            methods.push_back(m);
        }
        i += h.count;
    }

    return methods;
}

// ---- GPFIFO entry (nouveau_dma.c:82-84) ----
// word0 = lower_32_bits(offset)
// word1 = upper_32_bits(offset) | (length << 8) | (no_prefetch ? (1<<31) : 0)

GpEntry encodeGpEntry(uint64_t addr, uint32_t lengthBytes, bool noPrefetch)
{
    // Validate alignment
    if (addr & 3 || lengthBytes & 3)
        throw std::invalid_argument("addr and length must be multiple of 4");

    // Validate length
    if (lengthBytes == 0 || lengthBytes > kPushMaxLength)
        throw std::invalid_argument("length must be 1..NV50_DMA_PUSH_MAX_LENGTH");

    // Validate address fits in 40 bits
    if (addr >= (1ULL << 40))
        throw std::invalid_argument("address must fit in 40 bits");

    GpEntry e;
    // nouveau_dma.c:82 — lower_32_bits(offset)
    e.word0 = static_cast<uint32_t>(addr & 0xffffffffULL);
    // nouveau_dma.c:83 — upper_32_bits(offset)
    e.word1 = static_cast<uint32_t>((addr >> 32) & 0xffffffffULL) |
              (lengthBytes << 8) |
              (noPrefetch ? (1u << 31) : 0);
    return e;
}

GpInfo decodeGpEntry(const GpEntry& e)
{
    GpInfo info;
    // 40-bit address: upper 8 bits in word1[7:0], lower 32 in word0
    // — no source: 0xff is just 8-bit mask for address upper bits
    info.addr = static_cast<uint64_t>(e.word1 & 0xff) << 32 | e.word0;
    // Length: 23 bits in word1[30:8] — nouveau_dma.h:50 (NV50_DMA_PUSH_MAX_LENGTH)
    info.lengthBytes = (e.word1 >> 8) & 0x7fffff;
    // Bit 31: noPrefetch
    info.noPrefetch = (e.word1 >> 31) & 1;
    return info;
}

// ---- GPFIFO ring ----

GpFifo::GpFifo(unsigned entries)
{
    // Must be a power of two and at least 1
    if (entries == 0 || (entries & (entries - 1)) != 0)
        throw std::invalid_argument("entries must be a power of two");

    entries_ = entries;
    log2_ = 0;
    for (unsigned t = entries; t > 1; t >>= 1)
        log2_++;

    put_ = 0;
    ring_.resize(entries * 2, 0);  // 2 words per entry
}

unsigned GpFifo::push(uint64_t addr, uint32_t lengthBytes,
                      bool noPrefetch, unsigned get)
{
    // Check if ring is full (one slot must stay free)
    if (freeEntries(get) == 0)
        throw std::overflow_error("GPFIFO is full");

    GpEntry e = encodeGpEntry(addr, lengthBytes, noPrefetch);
    ring_[put_ * 2]     = e.word0;
    ring_[put_ * 2 + 1] = e.word1;
    put_ = (put_ + 1) & (entries_ - 1);
    return put_;
}

unsigned GpFifo::put() const
{
    return put_;
}

unsigned GpFifo::entries() const
{
    return entries_;
}

unsigned GpFifo::log2Entries() const
{
    return log2_;
}

unsigned GpFifo::freeEntries(unsigned get) const
{
    if (get >= entries_)
        return 0;
    if (put_ >= get)
        return (entries_ - 1) - (put_ - get);
    return entries_ - 1 - (put_ + entries_ - get);
}

const std::vector<uint32_t>& GpFifo::words() const
{
    return ring_;
}

uint32_t GpFifo::ramfcWord4c(uint64_t ringAddr) const
{
    // From chan.md: word 0x4c holds log2 entries and upper address bits
    // Acceptance test: ramfcWord4c(0x0123456000) == 0x00020001
    // upper32 = 0x00000001, log2 = 2 => (log2 << 16) | upper32 = 0x20001
    uint32_t upper32 = static_cast<uint32_t>(ringAddr >> 32);
    return (log2_ << 16) | upper32;
}

}  // namespace fifo
}  // namespace k40
