// PageTable.cpp — GK104 page-table encoding and address-space model
// Task D2: host-side algorithm for GPU address-space setup.
// Distributed under the terms of the MIT License.

#include "mmu/PageTable.h"

#include <cstring>

using namespace k40::mmu;

// ---------------------------------------------------------------------------
// PTE encoding — vmmgf100.c:32, vmmgf100.c:237-319
// ---------------------------------------------------------------------------

static uint64_t encodeType(Target target, const MapFlags& flags)
{
    // vmmgf100.c:314 — valid bit always set
    uint64_t type = 1ULL << 0;
    // vmmgf100.c:315 — priv
    type |= (uint64_t)flags.priv << 1;
    // vmmgf100.c:316 — readOnly
    type |= (uint64_t)flags.readOnly << 2;
    // vmmgf100.c:317 — vol (only effective for HOST target)
    type |= (uint64_t)flags.vol << 32;
    // vmmgf100.c:318, vmmgf100.c:326-332 — aper: VRAM→0, HOST→2, NCOH→3
    uint64_t aper = 0;
    switch (target) {
    case Target::VRAM:  aper = 0;  break;
    case Target::HOST:  aper = 2;  break;
    case Target::NCOH:  aper = 3;  break;
    }
    type |= aper << 33;
    // vmmgf100.c:319 — kind
    type |= (uint64_t)flags.kind << 36;
    return type;
}

uint64_t k40::mmu::encodePte(uint64_t phys, Target target, const MapFlags& flags)
{
    // vmmgf100.c:35 — base = (addr >> 8) | map->type
    return (phys >> 8) | encodeType(target, flags);
}

// ---------------------------------------------------------------------------
// PDE encoding — vmmgf100.c:106-143
// ---------------------------------------------------------------------------

uint64_t k40::mmu::encodePde(const PageTableRef* large, const PageTableRef* small)
{
    uint64_t data = 0;

    // vmmgf100.c:113-125 — large-page table (pt[0]) in lower 32 bits
    if (large) {
        uint64_t aper = 0;
        switch (large->target) {
        case Target::VRAM:  aper = 1; break;   // vmmgf100.c:115
        case Target::HOST:  aper = 2; break;   // vmmgf100.c:116-117
        case Target::NCOH:  aper = 3; break;   // vmmgf100.c:119
        }
        data |= aper << 0;
        if (large->target == Target::HOST)
            data |= 1ULL << 35;   // vmmgf100.c:117
        data |= large->addr >> 8;  // vmmgf100.c:124
    }

    // vmmgf100.c:127-138 — small-page table (pt[1]) in upper 32 bits
    if (small) {
        uint64_t aper = 0;
        switch (small->target) {
        case Target::VRAM:  aper = 1; break;   // vmmgf100.c:129
        case Target::HOST:  aper = 2; break;   // vmmgf100.c:130-131
        case Target::NCOH:  aper = 3; break;   // vmmgf100.c:133
        }
        data |= aper << 32;
        if (small->target == Target::HOST)
            data |= 1ULL << 34;   // vmmgf100.c:131
        data |= small->addr << 24;  // vmmgf100.c:138
    }

    return data;
}

// ---------------------------------------------------------------------------
// Virtual-address split — vmmgk104.c:40-51
// ---------------------------------------------------------------------------

k40::mmu::VaSplit k40::mmu::splitVa(uint64_t va)
{
    // vmmgk104.c:42 — PGD: 13 bits [27..39] → 8192 entries (128 MiB each)
    uint32_t pde = static_cast<uint32_t>((va >> kPdeShift) & 0x1fff);
    // vmmgk104.c:48 — LPT: 10 bits [17..26] → 1024 entries (128 KiB each)
    uint32_t lpte = static_cast<uint32_t>((va >> kLargeShift) & 0x3ff);
    // vmmgk104.c:41 — SPT: 15 bits [0..14] → 32768 entries (4 KiB each)
    uint32_t spte = static_cast<uint32_t>((va >> kSmallShift) & 0x7fff);
    return { pde, lpte, spte };
}

// ---------------------------------------------------------------------------
// Instance-block encoding — vmmgf100.c:341-362
// ---------------------------------------------------------------------------

uint64_t k40::mmu::encodeInstPdb(const PageTableRef& pd)
{
    // vmmgf100.c:342-359 — base with target bits, then pd->addr
    uint64_t base = 0;
    switch (pd.target) {
    case Target::VRAM:  base |= 0ULL << 0; break;     // vmmgf100.c:347
    case Target::HOST:  base |= 2ULL << 0;             // vmmgf100.c:348
        base |= 1ULL << 2;                              // vmmgf100.c:349 — VOL
        break;
    case Target::NCOH:  base |= 3ULL << 0; break;      // vmmgf100.c:351
    }
    base |= pd.addr;
    return base;
}

uint64_t k40::mmu::encodeInstLimit(uint64_t vaLimit)
{
    // vmmgf100.c:360 — limit = vaLimit - 1
    return vaLimit - 1;
}

// ---------------------------------------------------------------------------
// AddressSpace model
// ---------------------------------------------------------------------------

struct TableInfo {
    uint64_t addr;    // physical address
    uint32_t size;    // size in bytes (kSptEntries*8 or kLptEntries*8)
    uint32_t entries; // number of entries
    bool isLarge;     // true = large-page table (pt[0]), false = small-page (pt[1])
};

k40::mmu::AddressSpace::AddressSpace(std::function<uint64_t(uint32_t)> alloc)
    : fPdSize(kPdEntries * 8)
    , fAlloc(alloc)
{
    // Allocate and zero the page directory — vmmgf100.c:109
    fPd.assign(fPdSize, 0);
    fPdBase = alloc(fPdSize);
}

// ---------------------------------------------------------------------------
// Validation helpers
// ---------------------------------------------------------------------------

static void validatePageShift(uint32_t pageShift)
{
    if (pageShift != 12 && pageShift != 17)
        throw std::invalid_argument("Page shift must be 12 or 17");
}

static void validateAlign(uint64_t value, uint64_t pageSize)
{
    if (value & (pageSize - 1))
        throw std::invalid_argument("Address not page-aligned");
}

static void validateSize(uint64_t size, uint64_t pageSize)
{
    if (size == 0 || (size & (pageSize - 1)))
        throw std::invalid_argument("Size must be non-zero and page-aligned");
}

static bool beyond40bits(uint64_t va, uint64_t size)
{
    uint64_t limit = 1ULL << kVaBits;
    return va >= limit || size > UINT64_MAX - va || (va + size) > limit;
}

static bool physBeyond40bits(uint64_t phys, uint64_t size)
{
    uint64_t limit = 1ULL << kVaBits;
    return phys >= limit || size > UINT64_MAX - phys || (phys + size) > limit;
}

// ---------------------------------------------------------------------------
// map — vmmgf100.c:236-320 (valid), vmmgf100.c:32-55 (pte write)
// ---------------------------------------------------------------------------

void k40::mmu::AddressSpace::map(uint64_t va, uint64_t phys, uint64_t size,
                                  uint32_t pageShift, Target target, const MapFlags& flags)
{
    validatePageShift(pageShift);

    uint64_t pageSize = 1ULL << pageShift;

    validateAlign(va, pageSize);
    validateAlign(phys, pageSize);
    validateSize(size, pageSize);
    if (beyond40bits(va, size))
        throw std::invalid_argument("Address beyond 40-bit range");
    if (physBeyond40bits(phys, size))
        throw std::invalid_argument("Physical address beyond 40-bit range");

    // Check for overlap with existing mappings across both page sizes.
    // Check each individual PTE, not entire table ranges (F1: mixed-page-size overlap).
    for (uint32_t i = 0; i < static_cast<uint32_t>(fTableInfos.size()); i++) {
        const auto& info = fTableInfos[i];
        uint64_t tblPageSize = info.isLarge ? (1ULL << kLargeShift) : (1ULL << kSmallShift);
        auto& table = fTableData[i];
        const uint64_t* ptePtr = reinterpret_cast<const uint64_t*>(table.data());
        uint64_t tableBaseVA = static_cast<uint64_t>(info.pdeIndex) << kPdeShift;
        for (uint32_t e = 0; e < info.entries; e++) {
            if (ptePtr[e] == kPteUnmapped)
                continue;
            uint64_t pteVA = tableBaseVA + static_cast<uint64_t>(e) * tblPageSize;
            if ((pteVA >= va && pteVA < va + size) ||
                (va >= pteVA && va < pteVA + tblPageSize))
                throw std::invalid_argument("Mapping overlaps existing mapping");
        }
    }

    for (uint64_t pva = va; pva < va + size; pva += pageSize) {
        VaSplit split = splitVa(pva);
        uint32_t pdeIdx = split.pde;
        uint32_t pteIdx = (pageShift == 12) ? split.spte : split.lpte;

        uint64_t pte = encodePte(phys + (pva - va), target, flags);

        // Find existing table for this PDE
        uint32_t tblIdx = 0;
        bool hasTable = false;
        for (uint32_t i = 0; i < static_cast<uint32_t>(fTableInfos.size()); i++) {
            if (fTableInfos[i].pdeIndex == pdeIdx && fTableInfos[i].isLarge == (pageShift == 17)) {
                tblIdx = i;
                hasTable = true;
                break;
            }
        }

        if (!hasTable) {
            // Allocate a new page table
            uint32_t tblEntries = pageShift == 12 ? kSptEntries : kLptEntries;
            uint64_t tblAddr = fAlloc(tblEntries * 8);
            std::vector<uint8_t> tblData(tblEntries * 8, 0);

            // Update the PDE: if there's already another table (large or small),
            // combine them using encodePde
            // Copies, not pointers into fTableRefs: the push_back below may
            // move the vector's storage (corrected by the scaffold).
            PageTableRef largeCopy = {0, Target::VRAM};
            PageTableRef smallCopy = {0, Target::VRAM};
            PageTableRef* largeRef = nullptr;
            PageTableRef* smallRef = nullptr;

            // Look for the other table type under the same PDE
            for (const auto& info : fTableInfos) {
                if (info.pdeIndex == pdeIdx && info.isLarge != (pageShift == 17)) {
                    if (info.isLarge) {
                        largeCopy = fTableRefs[info.tableIndex];
                        largeRef = &largeCopy;
                    } else {
                        smallCopy = fTableRefs[info.tableIndex];
                        smallRef = &smallCopy;
                    }
                }
            }

            PageTableRef newRef;
            newRef.addr = tblAddr;
            newRef.target = Target::VRAM;  // page tables always in VRAM
            fTableRefs.push_back(newRef);
            uint32_t newRefIdx = static_cast<uint32_t>(fTableRefs.size()) - 1;

            uint64_t newPde = encodePde(
                pageShift == 17 ? &newRef : largeRef,
                pageShift == 12 ? &newRef : smallRef);

            // vmmgf100.c:142 VMM_WO064 — write 8 bytes at pdei * 8 offset
            memcpy(&fPd[pdeIdx * 8], &newPde, 8);

            TableInfo info;
            info.addr = tblAddr;
            info.size = tblEntries * 8;
            info.entries = tblEntries;
            info.isLarge = (pageShift == 17);
            info.pdeIndex = pdeIdx;
            info.tableIndex = newRefIdx;
            fTableInfos.push_back(info);
            fTableData.push_back(std::move(tblData));
            tblIdx = static_cast<uint32_t>(fTableInfos.size()) - 1;
        }

        // Write the PTE into the table data
        auto& table = fTableData[tblIdx];
        uint64_t* ptePtr = reinterpret_cast<uint64_t*>(table.data());
        ptePtr[pteIdx] = pte;
    }
}

// ---------------------------------------------------------------------------
// unmap — vmmgf100.c:236-320 (valid path)
// ---------------------------------------------------------------------------

void k40::mmu::AddressSpace::unmap(uint64_t va, uint64_t size, uint32_t pageShift)
{
    validatePageShift(pageShift);

    uint64_t pageSize = 1ULL << pageShift;

    validateAlign(va, pageSize);
    validateSize(size, pageSize);
    if (beyond40bits(va, size))
        throw std::invalid_argument("Address beyond 40-bit range");

    // Check all pages are mapped and the page size matches
    for (uint64_t pva = va; pva < va + size; pva += pageSize) {
        auto opt = translate(pva);
        if (!opt.has_value())
            throw std::invalid_argument("Unmapping unmapped page");
        // The mapping must cover this VA with the same page size
        // Check by seeing if translate finds a mapping at the next page boundary
        // If the mapping is smaller than pageSize, translate at pva+pageSize would
        // find a different mapping or no mapping
        uint64_t nextVa = pva + pageSize;
        if (nextVa < va) // overflow check
            throw std::invalid_argument("Unmapping unmapped page");
        // If translate(nextVa) finds a mapping that doesn't cover from pva,
        // the page size doesn't match. We check by verifying the found mapping
        // covers the full pageSize from pva.
        // Simpler: try to find a table entry for this exact pva and pageShift.
        // If the mapping was done with a different page size, no matching table
        // entry exists for this (pva, pageShift) combination.
    }

    // Verify each page can be found with the requested page size
    for (uint64_t pva = va; pva < va + size; pva += pageSize) {
        VaSplit split = splitVa(pva);
        uint32_t pdeIdx = split.pde;
        uint32_t pteIdx = (pageShift == 12) ? split.spte : split.lpte;

        bool found = false;
        for (uint32_t i = 0; i < static_cast<uint32_t>(fTableInfos.size()); i++) {
            if (fTableInfos[i].pdeIndex == pdeIdx &&
                fTableInfos[i].isLarge == (pageShift == 17)) {
                auto& table = fTableData[i];
                if (pteIdx < table.size() / 8) {
                    const uint64_t* ptePtr = reinterpret_cast<const uint64_t*>(table.data());
                    if (ptePtr[pteIdx] != kPteUnmapped) {
                        found = true;
                        break;
                    }
                }
            }
        }
        if (!found)
            throw std::invalid_argument("Unmapping unmapped page or wrong page size");
    }

    for (uint64_t pva = va; pva < va + size; pva += pageSize) {
        VaSplit split = splitVa(pva);
        uint32_t pdeIdx = split.pde;
        uint32_t pteIdx = (pageShift == 12) ? split.spte : split.lpte;

        // Find and clear the PTE
        for (uint32_t i = 0; i < static_cast<uint32_t>(fTableInfos.size()); i++) {
            if (fTableInfos[i].pdeIndex == pdeIdx &&
                fTableInfos[i].isLarge == (pageShift == 17)) {
                auto& table = fTableData[i];
                uint64_t* ptePtr = reinterpret_cast<uint64_t*>(table.data());
                ptePtr[pteIdx] = kPteUnmapped;
                break;
            }
        }
    }
}

// ---------------------------------------------------------------------------
// translate — walk the page-directory and page-table entries
// ---------------------------------------------------------------------------

std::optional<uint64_t> k40::mmu::AddressSpace::translate(uint64_t va) const
{
    if (beyond40bits(va, 1))
        return std::nullopt;

    VaSplit split = splitVa(va);
    uint32_t pdeIdx = split.pde;

    // Check page directory entry
    if (fPd.size() <= pdeIdx * 8)
        return std::nullopt;
    uint64_t pdeVal = 0;
    memcpy(&pdeVal, &fPd[pdeIdx * 8], 8);
    if (pdeVal == 0)
        return std::nullopt;

    // Check PDE validity (bit 0 = valid for large table)
    // A PDE with bit 0 set means a large-page table exists
    // A PDE with bit 32 set means a small-page table exists

    // Find the appropriate page table for this virtual address
    // We need to determine which table serves this PTE
    // Try both large and small tables
    for (uint32_t i = 0; i < static_cast<uint32_t>(fTableInfos.size()); i++) {
        if (fTableInfos[i].pdeIndex != pdeIdx)
            continue;

        // Determine which shift this table handles
        bool isLarge = fTableInfos[i].isLarge;
        uint64_t pageSize = isLarge ? (1ULL << kLargeShift) : (1ULL << kSmallShift);
        uint32_t pteIdx = isLarge ? split.lpte : split.spte;

        // Check if the virtual address falls within this table's range
        uint64_t tableBaseVA = static_cast<uint64_t>(pdeIdx) << kPdeShift;
        uint64_t tableEndVA = tableBaseVA + static_cast<uint64_t>(fTableInfos[i].entries) * pageSize;

        if (va >= tableBaseVA && va < tableEndVA) {
            // Read the PTE
            const auto& table = fTableData[i];
            if (table.size() < (pteIdx + 1) * 8)
                continue;

            const uint64_t* ptePtr = reinterpret_cast<const uint64_t*>(table.data());
            uint64_t pte = ptePtr[pteIdx];

            if (pte == kPteUnmapped)
                continue;

            // Decode the physical address — vmmgf100.c:35
            // pte = (phys >> 8) | type; phys is a multiple of 4096
            // (pte & 0xfffffff0ULL) clears bits 0-3 (type occupies 0-2),
            // giving (phys >> 8) with bit 3 always 0.
            uint64_t phys = (pte & 0xfffffff0ULL) << 8;

            // Add the page offset
            uint64_t pageOffset = va & (pageSize - 1);
            return phys + pageOffset;
        }
    }

    return std::nullopt;
}

// ---------------------------------------------------------------------------
// Accessors
// ---------------------------------------------------------------------------

uint64_t k40::mmu::AddressSpace::pdAddr() const
{
    return fPdBase;
}

uint64_t k40::mmu::AddressSpace::pde(uint32_t index) const
{
    if (index >= kPdEntries)
        throw std::out_of_range("PDE index out of range");
    uint64_t val = 0;
    memcpy(&val, &fPd[index * 8], 8);
    return val;
}

uint64_t k40::mmu::AddressSpace::pte(uint32_t pdeIndex, uint32_t pageShift,
                                      uint32_t index) const
{
    bool isLarge = (pageShift == 17);

    for (uint32_t i = 0; i < static_cast<uint32_t>(fTableInfos.size()); i++) {
        if (fTableInfos[i].pdeIndex == pdeIndex && fTableInfos[i].isLarge == isLarge) {
            if (index >= fTableInfos[i].entries)
                throw std::out_of_range("PTE index out of range");
            const auto& table = fTableData[i];
            const uint64_t* ptePtr = reinterpret_cast<const uint64_t*>(table.data());
            return ptePtr[index];
        }
    }

    throw std::out_of_range("Page table does not exist for this PDE and shift");
}

uint32_t k40::mmu::AddressSpace::tableCount() const
{
    return static_cast<uint32_t>(fTableInfos.size());
}
