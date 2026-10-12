// LaunchDesc.h — QMD bitfield class and compute-launch helper functions.
// Distributed under the terms of the MIT License.
//
// Sources:
//   Bit positions: reference/mesa/.../nvc0/cla0c0qmd.h (QMDV00_06)
//   Field assigns: reference/mesa/.../nvc0/nve4_compute.c lines 581-617, 543-546
//   Methods:       reference/mesa/.../nve4_compute.xml.h NVE4_CP entries
//                  reference/mesa/.../nv_object.xml.h NV50_GRAPH_SERIALIZE

#pragma once

#include <array>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace k40 {
namespace compute {

// ---- Constants (task D5) ----
constexpr unsigned kComputeClass        = 0xa1c0;  // nv_object.xml.h:209
constexpr unsigned kComputeSubchannel   = 1;       // SUBC_CP, nve4_compute.c:873
constexpr unsigned kQmdBytes            = 256;     // 64 × 32 bits, no source: derived

// ---- 64-word QMD bitfield class (2048 bits total) ----
class Qmd {
public:
    std::array<uint32_t, 64> words() const { return data_; }

    // Set bits [lo:hi] (inclusive, lo ≤ hi) to value.
    // value must fit in (hi - lo + 1) bits; hi < 2048.
    void set(unsigned hi, unsigned lo, uint64_t value);

    // Read bits [lo:hi].
    uint64_t get(unsigned hi, unsigned lo) const;

private:
    std::array<uint32_t, 64> data_{};
};

// ---- Compute-job description (what the user fills) ----
struct ComputeJob {
    uint32_t codeOffset  = 0;
    uint32_t grid[3]     = {1, 1, 1};
    uint32_t block[3]    = {1, 1, 1};
    uint32_t sharedMemSize = 0;
    uint32_t localMemLow = 0;
    uint32_t numGprs     = 0;
    uint32_t numBarriers = 0;
};

// ---- Public API (task D5) ----

/**
 * buildQmd — fill a QMD with the 23 fields from nve4_compute_setup_launch_desc.
 *
 * Fields set (all from cla0c0qmd.h QMDV00_06):
 *   INVALIDATE_TEXTURE_HEADER_CACHE   (250)  = 1
 *   INVALIDATE_TEXTURE_SAMPLER_CACHE  (251)  = 1
 *   INVALIDATE_TEXTURE_DATA_CACHE     (252)  = 1
 *   INVALIDATE_SHADER_DATA_CACHE      (253)  = 1
 *   INVALIDATE_SHADER_CONSTANT_CACHE  (255)  = 1
 *   RELEASE_MEMBAR_TYPE               (366)  = FE_SYSMEMBAR (1)
 *   CWD_MEMBAR_TYPE                   (369:368) = L1_SYSMEMBAR (1)
 *   API_VISIBLE_CALL_LIMIT            (378)  = NO_CHECK (1)
 *   SASS_VERSION                      (1535:1528) = 0x30  // cla0c0qmd.h:216; nve4_compute.c:589
 *   PROGRAM_OFFSET                    (287:256) = codeOffset
 *   CTA_RASTER_WIDTH                  (415:384) = grid[0]
 *   CTA_RASTER_HEIGHT                 (431:416) = grid[1]
 *   CTA_RASTER_DEPTH                  (447:432) = grid[2]
 *   CTA_THREAD_DIMENSION0             (607:592) = block[0]
 *   CTA_THREAD_DIMENSION1             (623:608) = block[1]
 *   CTA_THREAD_DIMENSION2             (639:624) = block[2]
 *   SHARED_MEMORY_SIZE                (561:544) = align(sharedMemSize, 0x100)  // cla0c0qmd.h:139; nve4_compute.c:600
 *   SHADER_LOCAL_MEMORY_LOW_SIZE      (1463:1440) = localMemLow
 *   SHADER_LOCAL_MEMORY_HIGH_SIZE     (1495:1472) = 0
 *   SHADER_LOCAL_MEMORY_CRS_SIZE      (1527:1504) = 0x800  // cla0c0qmd.h:215; nve4_compute.c:603
 *   L1_CONFIGURATION                  (671:669) = derived from sharedMemSize
 *   REGISTER_COUNT                    (1503:1496) = numGprs
 *   BARRIER_COUNT                     (1471:1467) = numBarriers
 *
 * Throws std::invalid_argument if values do not fit their field widths.
 */
Qmd buildQmd(const ComputeJob& j);

/**
 * setConstantBuffer — write 4 fields for constant buffer *index* (0-7).
 *
 * Fields (from nve4_cp_launch_desc_set_cb):
 *   CONSTANT_BUFFER_ADDR_LOWER  ((928+i*64):(959+i*64)) = address
 *   CONSTANT_BUFFER_ADDR_UPPER  ((960+i*64):(967+i*64)) = address >> 32
 *   CONSTANT_BUFFER_SIZE        ((975+i*64):(991+i*64)) = size
 *   CONSTANT_BUFFER_VALID       ((640+i):(640+i))       = 1
 *
 * Throws std::invalid_argument if index ≥ 8, address has low 8 bits set,
 * or size exceeds 17-bit field.
 */
void setConstantBuffer(Qmd& q, unsigned index, uint64_t address, uint32_t size);

/**
 * encodeLaunch — produce push-buffer words for launching the compute grid.
 *
 * Three method writes on compute subchannel 1:
 *   LAUNCH_DESC_ADDRESS (0x02b4): value = descGpuAddr >> 8  // nve4_compute.xml.h:165
 *   LAUNCH              (0x02bc): value = 3  // nve4_compute.xml.h:170
 *   NV50_GRAPH_SERIALIZE(0x0110): value = 0  // nv_object.xml.h:284
 *
 * Throws std::invalid_argument if descGpuAddr is not 256-byte aligned
 * or does not fit in 40 bits.
 */
std::vector<uint32_t> encodeLaunch(uint64_t descGpuAddr);

}  // namespace compute
}  // namespace k40
