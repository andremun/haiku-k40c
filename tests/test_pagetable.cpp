// test_pagetable.cpp — own tests for GK104 page-table encoding
// Task D2.
// Distributed under the terms of the MIT License.

#include "mmu/PageTable.h"

#include <cstdio>
#include <stdexcept>
#include <vector>

using namespace k40::mmu;

static int failures = 0;
static int checks = 0;

#define CHECK(cond)                                                       \
	do {                                                                \
		checks++;                                                     \
		if (!(cond)) {                                                \
			failures++;                                             \
			std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__,    \
			                  #cond);                               \
		}                                                             \
	} while (0)

template <typename E, typename F>
static bool throws(F f)
{
	try {
		f();
	} catch (const E&) {
		return true;
	} catch (...) {
		return false;
	}
	return false;
}

// Simple bump allocator for AddressSpace tests.
struct Pool {
	uint64_t next = 0x100000;
	std::vector<uint32_t> sizes;
	uint64_t alloc(uint32_t bytes)
	{
		uint64_t addr = next;
		sizes.push_back(bytes);
		next += (bytes + 0xfffu) & ~0xfffu;
		return addr;
	}
};

// 1. encodePte with all flags set (priv, readOnly, vol, kind)
static void test_pte_all_flags()
{
	MapFlags f;
	f.priv = true;
	f.readOnly = true;
	f.vol = true;
	f.kind = 0xff;
	// aper=2 (HOST), vol=bit 32, kind=0xff at bits 36-43
	// type = 1 | 2 | 4 | 0x10000000 | 0x40000000 | 0xff00000000
	// phys=0xABCDEF000 → phys>>8 = 0xABCDEF0
	// result = 0xABCDEF0 | type
	uint64_t result = encodePte(0xABCDEF000ULL, Target::HOST, f);
	CHECK(result == 0xff50abcdef7ULL);
}

// 2. encodePte with kind = 0 (default)
static void test_pte_kind_zero()
{
	MapFlags f;
	uint64_t result = encodePte(0x0, Target::VRAM, f);
	CHECK(result == 1ULL);  // only the valid bit
}

// 3. splitVa at zero
static void test_split_zero()
{
	VaSplit s = splitVa(0);
	CHECK(s.pde == 0 && s.lpte == 0 && s.spte == 0);
}

// 4. splitVa at the boundary of the first 128 MiB (0x8000000)
static void test_split_128mb_boundary()
{
	VaSplit s = splitVa(0x8000000ULL);
	CHECK(s.pde == 1 && s.lpte == 0 && s.spte == 0);

	// one byte before the boundary
	s = splitVa(0x7FFFFFF);
	CHECK(s.pde == 0 && s.lpte == 1023 && s.spte == 32767);
}

// 5. splitVa at the last valid 40-bit address
static void test_split_last_address()
{
	// 0xFFFFFFFFFF is the max 40-bit address
	VaSplit s = splitVa(0xFFFFFFFFFFULL);
	CHECK(s.pde == 8191 && s.lpte == 1023 && s.spte == 32767);
}

// 6. encodePde: both null pointers
static void test_pde_null()
{
	CHECK(encodePde(nullptr, nullptr) == 0);
}

// 7. encodePde: only small table, VRAM target
static void test_pde_small_vram()
{
	PageTableRef spt = {0x12340, Target::VRAM};
	// aper=1 at bit 32, addr<<24 at upper
	uint64_t result = encodePde(nullptr, &spt);
	CHECK(result == ((1ULL << 32) | (0x12340ULL << 24)));
}

// 8. encodePde: only large table, HOST target
static void test_pde_large_host()
{
	PageTableRef lpt = {0x56780, Target::HOST};
	// aper=2 at bit 0, HOST extra bit at 35, addr>>8
	uint64_t result = encodePde(&lpt, nullptr);
	CHECK(result == ((2ULL << 0) | (1ULL << 35) | (0x56780ULL >> 8)));
}

// 9. Map, unmap, map again — same VA should succeed
static void test_map_unmap_map()
{
	Pool pool;
	AddressSpace as([&](uint32_t bytes) { return pool.alloc(bytes); });

	as.map(0x10000, 0xA0000, 0x1000, 12, Target::VRAM);
	CHECK(as.translate(0x10000) && *as.translate(0x10000) == 0xA0000);

	as.unmap(0x10000, 0x1000, 12);
	CHECK(!as.translate(0x10000));

	// same VA should now be mappable
	as.map(0x10000, 0xB0000, 0x1000, 12, Target::VRAM);
	CHECK(as.translate(0x10000) && *as.translate(0x10000) == 0xB0000);
}

// 10. Two independent address spaces do not share tables
static void test_two_spaces()
{
	Pool pool1;
	Pool pool2;
	AddressSpace as1([&](uint32_t b) { return pool1.alloc(b); });
	AddressSpace as2([&](uint32_t b) { return pool2.alloc(b); });

	as1.map(0x10000, 0xA0000, 0x1000, 12, Target::VRAM);
	as2.map(0x10000, 0xC0000, 0x1000, 12, Target::VRAM);

	// Each space has its own table
	CHECK(as1.tableCount() == 1);
	CHECK(as2.tableCount() == 1);
	// Different translations
	CHECK(*as1.translate(0x10000) == 0xA0000);
	CHECK(*as2.translate(0x10000) == 0xC0000);
}

// 11. Large mapping crossing a directory boundary
static void test_large_cross_boundary()
{
	Pool pool;
	AddressSpace as([&](uint32_t bytes) { return pool.alloc(bytes); });

	// 256 KiB = 2 large pages starting at 0x7FE0000
	// This crosses from PDE 0 to PDE 1
	as.map(0x7FE0000, 0xD00000, 0x40000, 17, Target::VRAM);
	CHECK(as.tableCount() == 2);  // one LPT per PDE
	// The last entry of PDE 0's LPT should be mapped
	CHECK(as.pte(0, 17, 1023) != 0);
	// The first entry of PDE 1's LPT should be mapped
	CHECK(as.pte(1, 17, 0) != 0);
}

// 12. translate at the last byte of a page
static void test_translate_last_byte()
{
	Pool pool;
	AddressSpace as([&](uint32_t bytes) { return pool.alloc(bytes); });

	as.map(0x20000, 0xE0000, 0x1000, 12, Target::VRAM);

	// First byte
	CHECK(*as.translate(0x20000) == 0xE0000);
	// Last byte of the page
	CHECK(*as.translate(0x20FFF) == 0xE0FFF);
	// First byte of the next page should be unmapped
	CHECK(!as.translate(0x21000));
}

// 13. map error: overlap with existing mapping
static void test_map_overlap_error()
{
	Pool pool;
	AddressSpace as([&](uint32_t bytes) { return pool.alloc(bytes); });

	as.map(0x10000, 0xF0000, 0x2000, 12, Target::VRAM);
	CHECK(throws<std::invalid_argument>([&] {
		as.map(0x11000, 0xF2000, 0x1000, 12, Target::VRAM);
	}));
	// The original mapping should still be intact
	CHECK(*as.translate(0x10000) == 0xF0000);
	CHECK(*as.translate(0x11000) == 0xF1000);
}

// 14. unmap error: page is not mapped
static void test_unmap_not_mapped_error()
{
	Pool pool;
	AddressSpace as([&](uint32_t bytes) { return pool.alloc(bytes); });

	CHECK(throws<std::invalid_argument>([&] {
		as.unmap(0x10000, 0x1000, 12);
	}));
}

// 15. pte accessor throws out_of_range for a table that was never created
static void test_pte_nonexistent_table()
{
	Pool pool;
	AddressSpace as([&](uint32_t bytes) { return pool.alloc(bytes); });

	// No mappings yet — table for PDE 0 doesn't exist
	CHECK(throws<std::out_of_range>([&] { as.pte(0, 12, 0); }));
}

// 16. encodeInstPdb with VRAM target (no target bits set)
static void test_inst_pdb_vram()
{
	PageTableRef pd = {0x50000, Target::VRAM};
	CHECK(encodeInstPdb(pd) == 0x50000ULL);
}

// 17. encodeInstLimit with a non-max limit
static void test_inst_limit()
{
	// limit = vaLimit - 1
	CHECK(encodeInstLimit(0x100000) == 0xFFFFF);
	CHECK(encodeInstLimit(1ULL << 32) == 0xFFFFFFFFULL);
}

// 18. NCOH target encoding for PTE
static void test_pte_ncoh()
{
	MapFlags f;
	// aper=3 (NCOH) at bits 33-35
	uint64_t result = encodePte(0x1000, Target::NCOH, f);
	// phys>>8 = 0x10, type = 1 | 3<<33 = 1 | 0x600000000
	CHECK(result == 0x600000011ULL);
}

int main()
{
	test_pte_all_flags();
	test_pte_kind_zero();
	test_split_zero();
	test_split_128mb_boundary();
	test_split_last_address();
	test_pde_null();
	test_pde_small_vram();
	test_pde_large_host();
	test_map_unmap_map();
	test_two_spaces();
	test_large_cross_boundary();
	test_translate_last_byte();
	test_map_overlap_error();
	test_unmap_not_mapped_error();
	test_pte_nonexistent_table();
	test_inst_pdb_vram();
	test_inst_limit();
	test_pte_ncoh();

	std::printf("test_pagetable: %d checks, %d failures\n", checks, failures);
	return failures == 0 ? 0 : 1;
}
