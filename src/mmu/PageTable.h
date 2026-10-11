// PageTable.h — GK104 page-table encoding and address-space model
// Task D2: host-side algorithm for GPU address-space setup.
// Distributed under the terms of the MIT License.

#pragma once

#include <cstdint>
#include <functional>
#include <optional>
#include <stdexcept>
#include <vector>

namespace k40 {
namespace mmu {

// Memory targets — vmmgf100.c:326-332 gf100_vmm_aper
enum class Target { VRAM, HOST, NCOH };

// Mapping flags — vmmgf100.c:257-266, 314-319
struct MapFlags {
    bool priv = false;       // bit 1
    bool readOnly = false;   // bit 2
    bool vol = false;        // bit 32 (only effective for HOST target)
    uint8_t kind = 0;        // bits 36-43
};

// Address-space geometry — vmmgk104.c:40-51
// 40-bit address space split across three levels.
static constexpr uint32_t kVaBits = 40;        // total address width
static constexpr uint32_t kSmallShift = 12;    // 4 KiB small-page shift — vmmgk104.c:41
static constexpr uint32_t kLargeShift = 17;    // 128 KiB large-page shift — vmmgk104.c:48
static constexpr uint32_t kPdeShift = 27;      // 128 MiB page-directory shift — vmmgk104.c:42

// Number of entries per table — vmmgk104.c:41 (15 bits → 32768), 42 (13 bits → 8192), 48 (10 bits → 1024)
static constexpr uint32_t kPdEntries = 1u << 13;   // 8192 — vmmgk104.c:42 PGD level
static constexpr uint32_t kSptEntries = 1u << 15;  // 32768 — vmmgk104.c:41 SPT level
static constexpr uint32_t kLptEntries = 1u << 10;  // 1024 — vmmgk104.c:48 LPT level

// Unmapped PTE value — all-zero
static constexpr uint64_t kPteUnmapped = 0;

// Invalid LPT-entry value — vmmgk104.c:29 (BIT_ULL(1))
static constexpr uint64_t kLptInvalid = 2;

// Encode a page-table entry.
// Formula: (phys >> 8) | type, where type has:
//   bit 0  = valid (always set) — vmmgf100.c:314
//   bit 1  = priv — vmmgf100.c:315
//   bit 2  = readOnly — vmmgf100.c:316
//   bit 32 = vol — vmmgf100.c:317
//   bits 33-35 = aper (VRAM→0, HOST→2, NCOH→3) — vmmgf100.c:318, vmmgf100.c:326-332
//   bits 36-43 = kind — vmmgf100.c:319
uint64_t encodePte(uint64_t phys, Target target, const MapFlags& flags);

// Page-table reference for encoding into a directory entry.
// pgt->pt[0] = large-page table, pgt->pt[1] = small-page table — vmmgf100.c:109, 113, 127
struct PageTableRef {
    uint64_t addr;   // physical address of the table
    Target target;   // memory target of the table
};

// Encode a page-directory entry.
// Lower 32 bits: large-page table info — vmmgf100.c:113-125
// Upper 32 bits: small-page table info — vmmgf100.c:127-138
uint64_t encodePde(const PageTableRef* large, const PageTableRef* small);

// Split a virtual address into its three index components.
// pde = bits [27..39] of the address — vmmgk104.c:42
// lpte = bits [17..26] — vmmgk104.c:48
// spte = bits [0..11] — vmmgk104.c:41
struct VaSplit {
    uint32_t pde;    // page-directory index
    uint32_t lpte;   // large-page-table index
    uint32_t spte;   // small-page-table index
};
VaSplit splitVa(uint64_t va);

// Encode the instance-block entry at offset 0x200.
// Base address with target bits — vmmgf100.c:342-359
uint64_t encodeInstPdb(const PageTableRef& pd);

// Encode the instance-block limit at offset 0x208.
// vmmgf100.c:360 — limit = vaLimit - 1 (wraps to 0xffffffffffff for 40-bit)
uint64_t encodeInstLimit(uint64_t vaLimit);

// Address-space model: page directory + page tables in simulated memory.
class AddressSpace {
public:
    // Allocate a zeroed block; returns its physical address.
    explicit AddressSpace(std::function<uint64_t(uint32_t bytes)> alloc);

    // Map [va, va+size) with pageShift (12 or 17).
    // Throws std::invalid_argument on error (nothing changes).
    void map(uint64_t va, uint64_t phys, uint64_t size,
             uint32_t pageShift, Target target, const MapFlags& flags = {});

    // Unmap [va, va+size).
    void unmap(uint64_t va, uint64_t size, uint32_t pageShift);

    // Translate a virtual address → physical (optional).
    std::optional<uint64_t> translate(uint64_t va) const;

    // Accessors — throw std::out_of_range if the table does not exist.
    uint64_t pdAddr() const;
    uint64_t pde(uint32_t index) const;
    uint64_t pte(uint32_t pdeIndex, uint32_t pageShift, uint32_t index) const;
    uint32_t tableCount() const;

private:
    void validateMap(uint64_t va, uint64_t size, uint32_t pageShift) const;
    void validateUnmap(uint64_t va, uint64_t size, uint32_t pageShift) const;

    std::vector<uint8_t> fPd;           // page directory memory (kPdEntries * 8 bytes)
    uint32_t fPdSize;                   // page directory size in bytes
    uint64_t fPdBase;                   // physical address of the page directory
    // Page table info
    struct TableInfo {
        uint64_t addr;
        uint32_t size;
        uint32_t entries;
        bool isLarge;
        uint32_t pdeIndex;
        uint32_t tableIndex;
    };
    std::vector<TableInfo> fTableInfos;
    std::vector<std::vector<uint8_t>> fTableData;
    std::vector<PageTableRef> fTableRefs;
    std::function<uint64_t(uint32_t bytes)> fAlloc;
};

} // namespace mmu
} // namespace k40
