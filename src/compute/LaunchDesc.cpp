// LaunchDesc.cpp — QMD bitfield ops, buildQmd, setConstantBuffer, encodeLaunch.
// Distributed under the terms of the MIT License.
//
// Sources:
//   Bit positions: reference/mesa/.../nvc0/cla0c0qmd.h (QMDV00_06)
//   Field assigns: reference/mesa/.../nvc0/nve4_compute.c lines 581-617, 543-546
//   Methods:       reference/mesa/.../nve4_compute.xml.h NVE4_CP entries
//                  reference/mesa/.../nv_object.xml.h NV50_GRAPH_SERIALIZE

#include "compute/LaunchDesc.h"
#include "fifo/PushBuffer.h"

#include <cstdint>
#include <stdexcept>
#include <vector>

namespace k40 {
namespace compute {

// ---- Qmd bitfield helpers ----

static inline unsigned wordIndex(unsigned bit) { return bit / 32; }
static inline unsigned bitInWord(unsigned bit) { return bit % 32; }

void Qmd::set(unsigned hi, unsigned lo, uint64_t value) {
    if (hi < lo)
        throw std::invalid_argument("hi < lo in Qmd::set");
    if (hi >= 2048)
        throw std::invalid_argument("hi >= 2048 in Qmd::set");
    unsigned width = hi - lo + 1;
    if (width > 64)
        throw std::invalid_argument("field width > 64 in Qmd::set");

    // Check value fits
    uint64_t fieldMask = width >= 64 ? ~0ULL : ((1ULL << width) - 1);
    if ((value & fieldMask) != value)
        throw std::invalid_argument("value does not fit field in Qmd::set");

    // Write bit by bit (field may span multiple words)
    for (unsigned bit = lo; bit <= hi; bit++) {
        unsigned w = wordIndex(bit);
        unsigned b = bitInWord(bit);
        uint32_t bitVal = (value >> (bit - lo)) & 1u;
        data_[w] = (data_[w] & ~(1u << b)) | (bitVal << b);
    }
}

uint64_t Qmd::get(unsigned hi, unsigned lo) const {
    if (hi >= 2048)
        throw std::invalid_argument("hi >= 2048 in Qmd::get");
    if (hi < lo)
        throw std::invalid_argument("hi < lo in Qmd::get");

    uint64_t result = 0;
    for (unsigned bit = lo; bit <= hi; bit++) {
        unsigned w = wordIndex(bit);
        unsigned b = bitInWord(bit);
        uint64_t bitVal = (data_[w] >> b) & 1u;
        result |= bitVal << (bit - lo);
    }
    return result;
}

// ---- buildQmd (23 fields from nve4_compute_setup_launch_desc) ----

static uint64_t fld_shared_mem(const ComputeJob& j) {
    // align(sharedMemSize, 0x100) = (x + 0xFF) & ~0xFF
    uint64_t aligned = (j.sharedMemSize + 0xFF) & ~0xFFULL;  // nve4_compute.c:600 align(shared_size, 0x100)
    if (aligned > 0x3FFFF)  // 18-bit field: cla0c0qmd.h:139
        throw std::invalid_argument("sharedMemSize too large for 18-bit field");
    return aligned;
}

static uint64_t fld_l1_config(const ComputeJob& j) {
    // nve4_compute.c:605-613: uses unaligned shared_size
    if (j.sharedMemSize > (32 << 10)) return 3;  // 48KB
    if (j.sharedMemSize > (16 << 10)) return 2;  // 32KB
    return 1;                                      // 16KB
}

Qmd buildQmd(const ComputeJob& j) {
    Qmd q;

    // Field definitions from nve4_compute_setup_launch_desc
    // (lines 581-617 of nve4_compute.c, all from cla0c0qmd.h QMDV00_06)
    struct Def { unsigned hi, lo; uint64_t value; };
    Def defs[] = {
        {250, 250,  1},                             // INVALIDATE_TEXTURE_HEADER_CACHE      // cla0c0qmd.h:75; nve4_compute.c:581
        {251, 251,  1},                             // INVALIDATE_TEXTURE_SAMPLER_CACHE     // cla0c0qmd.h:78; nve4_compute.c:582
        {252, 252,  1},                             // INVALIDATE_TEXTURE_DATA_CACHE        // cla0c0qmd.h:81; nve4_compute.c:583
        {253, 253,  1},                             // INVALIDATE_SHADER_DATA_CACHE         // cla0c0qmd.h:84; nve4_compute.c:584
        {255, 255,  1},                             // INVALIDATE_SHADER_CONSTANT_CACHE     // cla0c0qmd.h:90; nve4_compute.c:585
        {366, 366,  1},                             // RELEASE_MEMBAR_TYPE=FE_SYSMEMBAR     // cla0c0qmd.h:100; nve4_compute.c:586
        {369, 368,  1},                             // CWD_MEMBAR_TYPE=L1_SYSMEMBAR         // cla0c0qmd.h:103; nve4_compute.c:587
        {378, 378,  1},                             // API_VISIBLE_CALL_LIMIT=NO_CHECK      // cla0c0qmd.h:118; nve4_compute.c:588
        {1535,1528, 0x30},                          // SASS_VERSION                         // cla0c0qmd.h:216; nve4_compute.c:589
        {287, 256,  j.codeOffset},                  // PROGRAM_OFFSET                       // cla0c0qmd.h:93; nve4_compute.c:591
        {415, 384,  j.grid[0]},                     // CTA_RASTER_WIDTH                     // cla0c0qmd.h:128; nve4_compute.c:593
        {431, 416,  j.grid[1]},                     // CTA_RASTER_HEIGHT                    // cla0c0qmd.h:129; nve4_compute.c:594
        {447, 432,  j.grid[2]},                     // CTA_RASTER_DEPTH                     // cla0c0qmd.h:130; nve4_compute.c:595
        {607, 592,  j.block[0]},                    // CTA_THREAD_DIMENSION0                // cla0c0qmd.h:144; nve4_compute.c:596
        {623, 608,  j.block[1]},                    // CTA_THREAD_DIMENSION1                // cla0c0qmd.h:145; nve4_compute.c:597
        {639, 624,  j.block[2]},                    // CTA_THREAD_DIMENSION2                // cla0c0qmd.h:146; nve4_compute.c:598
        {561, 544,  fld_shared_mem(j)},             // SHARED_MEMORY_SIZE                   // cla0c0qmd.h:139; nve4_compute.c:600
        {1463,1440, j.localMemLow & 0xfffff0ULL},   // SHADER_LOCAL_MEMORY_LOW_SIZE         // cla0c0qmd.h:210; nve4_compute.c:601
        {1495,1472, 0ULL},                          // SHADER_LOCAL_MEMORY_HIGH_SIZE        // cla0c0qmd.h:213; nve4_compute.c:602
        {1527,1504, 0x800ULL},                      // SHADER_LOCAL_MEMORY_CRS_SIZE         // cla0c0qmd.h:215; nve4_compute.c:603
        {671, 669,  fld_l1_config(j)},              // L1_CONFIGURATION                     // cla0c0qmd.h:151; nve4_compute.c:606,610,613
        {1503,1496, j.numGprs},                     // REGISTER_COUNT                       // cla0c0qmd.h:214; nve4_compute.c:616
        {1471,1467, j.numBarriers},                 // BARRIER_COUNT                        // cla0c0qmd.h:212; nve4_compute.c:617
    };

    for (auto& d : defs)
        q.set(d.hi, d.lo, d.value);

    return q;
}

// ---- setConstantBuffer ----

void setConstantBuffer(Qmd& q, unsigned index, uint64_t address, uint32_t size) {
    if (index > 7)
        throw std::invalid_argument("constant buffer index >= 8");
    if (address & 0xFF)  // nve4_compute.c:542
        throw std::invalid_argument("address low 8 bits not zero");
    if (address >= (1ULL << 40))
        throw std::invalid_argument("address needs more than 40 bits");
    if (size > 0x1FFFF)  // 17-bit field: cla0c0qmd.h:209
        throw std::invalid_argument("size does not fit 17-bit field");

    unsigned base_addr = 928 + index * 64;

    // CONSTANT_BUFFER_ADDR_LOWER: bits (928+i*64) to (959+i*64) — 32 bits
    q.set(base_addr + 31, base_addr, address & 0xFFFFFFFF);  // cla0c0qmd.h:203
    // CONSTANT_BUFFER_ADDR_UPPER: bits (960+i*64) to (967+i*64) — 8 bits
    q.set(base_addr + 39, base_addr + 32, address >> 32);
    // CONSTANT_BUFFER_SIZE: bits (975+i*64) to (991+i*64) — 17 bits
    // (corrected by the scaffold: the bits were 967 to 975)
    q.set(base_addr + 63, base_addr + 47, size);
    // CONSTANT_BUFFER_VALID: bit (640+i) — 1 bit
    q.set(640 + index, 640 + index, 1);
}

// ---- encodeLaunch ----

std::vector<uint32_t> encodeLaunch(uint64_t descGpuAddr) {
    if (descGpuAddr & 0xFF)  // nve4_compute.c:542
        throw std::invalid_argument("descriptor address not 256-byte aligned");
    if (descGpuAddr >= (1ULL << 40))
        throw std::invalid_argument("descriptor address > 40 bits");

    uint32_t addrWord = static_cast<uint32_t>(descGpuAddr >> 8);

    fifo::PushBuffer pb;
    pb.begin(kComputeSubchannel, 0x02b4, 1);  // LAUNCH_DESC_ADDRESS  // nve4_compute.xml.h:165
    pb.data(addrWord);
    pb.begin(kComputeSubchannel, 0x02bc, 1);  // LAUNCH, value=3  // nve4_compute.xml.h:170
    pb.data(3);
    pb.begin(kComputeSubchannel, 0x0110, 1);  // NV50_GRAPH_SERIALIZE  // nv_object.xml.h:284
    pb.data(0);

    return pb.words();
}

}  // namespace compute
}  // namespace k40
