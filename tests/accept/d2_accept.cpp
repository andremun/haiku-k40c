// Acceptance test for task D2, written by the scaffold. Do not edit:
// `make check` compares this file with a recorded hash.
// Build: g++ -std=c++17 -Wall -Wextra -Werror -Isrc tests/accept/d2_accept.cpp src/mmu/*.cpp
//
// The expected values come from Nouveau (paths relative to
// reference/nouveau/nvkm/subdev/mmu/):
//   PTE      vmmgf100.c gf100_vmm_pgt_pte (line 32) and gf100_vmm_valid (line 237)
//   PDE      vmmgf100.c gf100_vmm_pgd_pde (line 106)
//   layout   vmmgk104.c gk104_vmm_desc_17_12 and gk104_vmm_desc_17_17 (lines 40, 47)
//   instance vmmgf100.c gf100_vmm_join_ (line 341)
#include "mmu/PageTable.h"

#include <cstdio>
#include <map>
#include <stdexcept>
#include <vector>

using namespace k40::mmu;

static int failures = 0;
static int checks = 0;

#define CHECK(cond) \
	do { \
		checks++; \
		if (!(cond)) { \
			failures++; \
			std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond); \
		} \
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

static void test_constants()
{
	CHECK(kVaBits == 40);
	CHECK(kSmallShift == 12 && kLargeShift == 17 && kPdeShift == 27);
	CHECK(kPdEntries == 8192 && kSptEntries == 32768 && kLptEntries == 1024);
	CHECK(kPteUnmapped == 0);
	CHECK(kLptInvalid == 2);
}

static void test_pte()
{
	MapFlags none;
	CHECK(encodePte(0x123456000ULL, Target::VRAM, none) == 0x0000000001234561ULL);
	CHECK(encodePte(0, Target::VRAM, none) == 0x1ULL);

	MapFlags ro;
	ro.readOnly = true;
	CHECK(encodePte(0x1000, Target::VRAM, ro) == 0x15ULL);

	MapFlags priv;
	priv.priv = true;
	CHECK(encodePte(0x1000, Target::VRAM, priv) == 0x13ULL);

	MapFlags vol;
	vol.vol = true;
	CHECK(encodePte(0x80000000ULL, Target::HOST, vol) == 0x0000000500800001ULL);
	CHECK(encodePte(0x80000000ULL, Target::NCOH, none) == 0x0000000600800001ULL);

	MapFlags kind;
	kind.kind = 0xfe;
	CHECK(encodePte(0x2000, Target::VRAM, kind) == 0x00000fe000000021ULL);

	// the next page of a run: + (1 << shift) >> 8
	CHECK(encodePte(0x20000, Target::VRAM, none) - encodePte(0, Target::VRAM, none) == 0x200);
}

static void test_pde()
{
	PageTableRef spt = {0x20000, Target::VRAM};
	PageTableRef lpt = {0x31000, Target::VRAM};
	CHECK(encodePde(nullptr, nullptr) == 0);
	CHECK(encodePde(nullptr, &spt) == 0x0000020100000000ULL);
	CHECK(encodePde(&lpt, nullptr) == 0x0000000000000311ULL);
	CHECK(encodePde(&lpt, &spt) == 0x0000020100000311ULL);

	PageTableRef hostSpt = {0x20000, Target::HOST};
	PageTableRef hostLpt = {0x31000, Target::HOST};
	CHECK(encodePde(nullptr, &hostSpt) == 0x0000020600000000ULL);
	CHECK(encodePde(&hostLpt, nullptr) == 0x0000000800000312ULL);
}

static void test_split()
{
	VaSplit s = splitVa(0);
	CHECK(s.pde == 0 && s.lpte == 0 && s.spte == 0);
	s = splitVa(0x0000001000ULL);
	CHECK(s.pde == 0 && s.spte == 1 && s.lpte == 0);
	s = splitVa(0x0000020000ULL);
	CHECK(s.pde == 0 && s.spte == 32 && s.lpte == 1);
	s = splitVa(0x0008000000ULL);
	CHECK(s.pde == 1 && s.spte == 0 && s.lpte == 0);
	s = splitVa(0xffffffffffULL);
	CHECK(s.pde == 8191 && s.spte == 32767 && s.lpte == 1023);
	s = splitVa(0x12345678000ULL & 0xffffffffffULL);
	CHECK(s.pde == 0x468 && s.spte == 0x5678 && s.lpte == 0x2b3);
}

static void test_instance_block()
{
	PageTableRef pd = {0x40000, Target::VRAM};
	CHECK(encodeInstPdb(pd) == 0x40000ULL);
	PageTableRef hostPd = {0x40000, Target::HOST};
	CHECK(encodeInstPdb(hostPd) == 0x40006ULL);
	CHECK(encodeInstLimit(1ULL << 40) == 0xffffffffffULL);
}

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

static void test_space_small()
{
	Pool pool;
	AddressSpace as([&](uint32_t bytes) { return pool.alloc(bytes); });
	CHECK(as.pdAddr() == 0x100000);
	CHECK(pool.sizes.size() == 1 && pool.sizes[0] == 8192 * 8);
	CHECK(as.tableCount() == 0);
	CHECK(as.pde(0) == 0);
	CHECK(!as.translate(0x10000));

	as.map(0x10000, 0x7654000, 0x3000, 12, Target::VRAM);
	CHECK(as.tableCount() == 1);
	CHECK(pool.sizes.size() == 2 && pool.sizes[1] == 32768 * 8);
	// the small-page table is at 0x110000
	CHECK(as.pde(0) == ((1ULL << 32) | (0x110000ULL << 24)));
	CHECK(as.pte(0, 12, 0x10) == 0x76541ULL);
	CHECK(as.pte(0, 12, 0x11) == 0x76551ULL);
	CHECK(as.pte(0, 12, 0x12) == 0x76561ULL);
	CHECK(as.pte(0, 12, 0x13) == 0);
	CHECK(as.pte(0, 12, 0x0f) == 0);
	CHECK(as.translate(0x10000) && *as.translate(0x10000) == 0x7654000);
	CHECK(as.translate(0x12abc) && *as.translate(0x12abc) == 0x7656abc);
	CHECK(!as.translate(0x13000));
	CHECK(!as.translate(0xf000));
	CHECK(throws<std::out_of_range>([&] { as.pte(0, 17, 0); }));
	CHECK(throws<std::out_of_range>([&] { as.pte(1, 12, 0); }));

	as.unmap(0x11000, 0x1000, 12);
	CHECK(as.pte(0, 12, 0x11) == 0);
	CHECK(!as.translate(0x11000));
	CHECK(as.translate(0x12000));
}

static void test_space_large_and_crossing()
{
	Pool pool;
	AddressSpace as([&](uint32_t bytes) { return pool.alloc(bytes); });

	// two large pages (128 KiB each), read-only, from system memory
	MapFlags f;
	f.readOnly = true;
	f.vol = true;
	as.map(0x40000, 0x80000000ULL, 0x40000, 17, Target::HOST, f);
	CHECK(pool.sizes.size() == 2 && pool.sizes[1] == 1024 * 8);
	CHECK(as.pde(0) == (1ULL | (0x110000ULL >> 8)));
	CHECK(as.pte(0, 17, 2) == 0x0000000500800005ULL);
	CHECK(as.pte(0, 17, 3) == 0x0000000500800205ULL);
	CHECK(as.pte(0, 17, 1) == 0);
	CHECK(as.translate(0x61234) && *as.translate(0x61234) == 0x80021234ULL);

	// a small-page mapping that crosses a page directory boundary (128 MiB)
	as.map(0x7fff000, 0x200000, 0x2000, 12, Target::VRAM);
	CHECK(as.tableCount() == 3);
	CHECK(as.pte(0, 12, 32767) == 0x2001ULL);
	CHECK(as.pte(1, 12, 0) == 0x2011ULL);
	CHECK(as.translate(0x8000010) && *as.translate(0x8000010) == 0x201010);
	// directory entry 0 now has both tables
	CHECK((as.pde(0) & 0xffffffffULL) == (1ULL | (0x110000ULL >> 8)));
	CHECK((as.pde(0) >> 32 & 0x3) == 1);
}

static void test_space_errors()
{
	Pool pool;
	AddressSpace as([&](uint32_t bytes) { return pool.alloc(bytes); });
	CHECK(throws<std::invalid_argument>([&] { as.map(0x1234, 0x1000, 0x1000, 12, Target::VRAM); }));
	CHECK(throws<std::invalid_argument>([&] { as.map(0x1000, 0x1234, 0x1000, 12, Target::VRAM); }));
	CHECK(throws<std::invalid_argument>([&] { as.map(0x1000, 0x1000, 0x800, 12, Target::VRAM); }));
	CHECK(throws<std::invalid_argument>([&] { as.map(0x1000, 0x1000, 0, 12, Target::VRAM); }));
	CHECK(throws<std::invalid_argument>([&] { as.map(0x1000, 0x1000, 0x1000, 16, Target::VRAM); }));
	CHECK(throws<std::invalid_argument>([&] { as.map(0x21000, 0x20000, 0x20000, 17, Target::VRAM); }));
	CHECK(throws<std::invalid_argument>(
		[&] { as.map(0xfffffff000ULL, 0x1000, 0x2000, 12, Target::VRAM); }));
	CHECK(as.tableCount() == 0);

	as.map(0x1000, 0x5000, 0x2000, 12, Target::VRAM);
	// overlap: nothing changes
	CHECK(throws<std::invalid_argument>([&] { as.map(0x2000, 0x9000, 0x2000, 12, Target::VRAM); }));
	CHECK(as.pte(0, 12, 2) == 0x51ULL + 0x10);
	CHECK(as.pte(0, 12, 3) == 0);
	// unmapping a page that is not mapped is an error
	CHECK(throws<std::invalid_argument>([&] { as.unmap(0x3000, 0x1000, 12); }));
}

int main()
{
	test_constants();
	test_pte();
	test_pde();
	test_split();
	test_instance_block();
	test_space_small();
	test_space_large_and_crossing();
	test_space_errors();
	std::printf("d2_accept: %d checks, %d failures\n", checks, failures);
	return failures == 0 ? 0 : 1;
}
