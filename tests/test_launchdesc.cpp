// test_launchdesc.cpp — own tests for task D5 (15+ CHECKs).
// Distributed under the terms of the MIT License.
#include "compute/LaunchDesc.h"
#include "fifo/PushBuffer.h"

#include <array>
#include <cstdio>
#include <stdexcept>
#include <vector>

using namespace k40::compute;

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
	try { f(); } catch (const E&) { return true; } catch (...) { return false; }
	return false;
}

// 1. Cross-word get after set: field spans words 1 and 2
static void test_crossword()
{
	Qmd q;
	q.set(63, 32, 0xDEADBEEF);  // crosses word 1→2
	CHECK(q.get(63, 32) == 0xDEADBEEF);
	CHECK(q.words()[1] == 0xDEADBEEFu);
	// read just the low half
	CHECK(q.get(39, 32) == 0xEF);
	// read just the high half
	CHECK(q.get(63, 40) == 0xDEADBE);
}

// 2. buildQmd with max values that fit
static void test_max_fit()
{
	ComputeJob j;
	j.codeOffset = 0xFFFFFFFF;            // 32-bit, fits in PROGRAM_OFFSET (32 bits)
	j.grid[0] = j.grid[1] = j.grid[2] = 0xFFFF;  // 32-bit each, CTA_RASTER fields are 32 bits
	j.block[0] = j.block[1] = j.block[2] = 0xFFFF;  // 32-bit each, CTA_THREAD fields are 32 bits
	j.sharedMemSize = 0xFFFF;             // 18-bit field after alignment → fits
	j.localMemLow = 0xFFFFF0;             // 24-bit field, fits in 24-bit SHADER_LOCAL_MEMORY_LOW_SIZE
	j.numGprs = 0xFF;                     // 8-bit field, fits
	j.numBarriers = 0x1F;                 // 5-bit field, fits

	Qmd q = buildQmd(j);
	CHECK(q.get(287, 256) == 0xFFFFFFFF);
	CHECK(q.get(415, 384) == 0xFFFF);
	CHECK(q.get(431, 416) == 0xFFFF);
	CHECK(q.get(447, 432) == 0xFFFF);
	CHECK(q.get(1503, 1496) == 0xFF);
	CHECK(q.get(1471, 1467) == 0x1F);
}

// 3. buildQmd rejects values that don't fit (BARRIER_COUNT is 5-bit)
static void test_overflow_barrier()
{
	ComputeJob j;
	j.numBarriers = 32;  // 5-bit field, 32 = 0x20 doesn't fit
	CHECK(throws<std::invalid_argument>([&] { buildQmd(j); }));
}

// 4. buildQmd rejects values that don't fit (REGISTER_COUNT is 8-bit)
static void test_overflow_gpr()
{
	ComputeJob j;
	j.numGprs = 0x100;  // 8-bit field, 0x100 doesn't fit
	CHECK(throws<std::invalid_argument>([&] { buildQmd(j); }));
}

// 5. All 8 constant buffers set
static void test_all_constant_buffers()
{
	Qmd q = buildQmd(ComputeJob());
	for (unsigned i = 0; i < 8; i++) {
		setConstantBuffer(q, i, (uint64_t)(i + 1) * 0x1000, 0x1000);
	}
	// Check each valid bit is set
	for (unsigned i = 0; i < 8; i++) {
		CHECK(q.get(640 + i, 640 + i) == 1);
		// Check address lower
		uint64_t expectedAddr = (uint64_t)(i + 1) * 0x1000;
		uint64_t addrLower = q.get(959 + i * 64, 928 + i * 64);
		CHECK(addrLower == (expectedAddr & 0xFFFFFFFF));
	}
}

// 6. encodeLaunch decoded with k40::fifo::decodeBuffer
static void test_encode_decode()
{
	std::vector<uint32_t> words = encodeLaunch(0xABCDEF000ULL);
	auto methods = k40::fifo::decodeBuffer(words);
	CHECK(methods.size() == 3);
	// First method: LAUNCH_DESC_ADDRESS
	CHECK(methods[0].method == 0x02b4);
	CHECK(methods[0].value == 0x0ABCDEF0u);  // shifted right by 8
	// Second method: LAUNCH
	CHECK(methods[1].method == 0x02bc);
	CHECK(methods[1].value == 3);
	// Third method: NV50_GRAPH_SERIALIZE
	CHECK(methods[2].method == 0x0110);
	CHECK(methods[2].value == 0);
}

// 7. encodeLaunch with address at boundary (40 bits max)
static void test_encode_boundary()
{
	// Max 40-bit address (all 40 bits set), aligned to 256 bytes
	std::vector<uint32_t> w = encodeLaunch((1ULL << 40) - 0x100);
	CHECK(w.size() == 6);
	// Address >> 8 = ((1<<40) - 0x100) >> 8 = (1<<32) - 1 = 0xFFFFFFFF
	CHECK(w[1] == 0xFFFFFFFF);
}

// 8. Qmd get/set round-trip for a wide field (62 bits)
static void test_wide_field()
{
	Qmd q;
	uint64_t val = 0x3FFFFFFFFFFFFFFFULL;  // 62 bits
	q.set(61, 0, val);
	CHECK(q.get(61, 0) == val);
}

// 9. setConstantBuffer doesn't modify descriptor on error
static void test_cb_error_preserves()
{
	Qmd q = buildQmd(ComputeJob());
	q.set(63, 32, 0x1234);  // set something
	uint32_t saved = q.words()[3];
	CHECK(throws<std::invalid_argument>([&] { setConstantBuffer(q, 9, 0x1000, 0x100); }));
	CHECK(q.words()[3] == saved);  // descriptor unchanged
}

// 10. encodeLaunch with zero address
static void test_encode_zero()
{
	std::vector<uint32_t> w = encodeLaunch(0);
	CHECK(w.size() == 6);
	CHECK(w[1] == 0);
}

// 11. Default ComputeJob produces minimal QMD
static void test_default_job()
{
	ComputeJob j;
	Qmd q = buildQmd(j);
	// All grid/block default to 1
	CHECK(q.get(415, 384) == 1);
	CHECK(q.get(431, 416) == 1);
	CHECK(q.get(447, 432) == 1);
	CHECK(q.get(607, 592) == 1);
	CHECK(q.get(623, 608) == 1);
	CHECK(q.get(639, 624) == 1);
	// codeOffset, sharedMemSize, localMemLow, numGprs, numBarriers default to 0
	CHECK(q.get(287, 256) == 0);
	CHECK(q.get(1503, 1496) == 0);
	CHECK(q.get(1471, 1467) == 0);
}

// 12. setConstantBuffer rejects invalid address (low 8 bits set)
static void test_cb_bad_address()
{
	Qmd q = buildQmd(ComputeJob());
	CHECK(throws<std::invalid_argument>([&] { setConstantBuffer(q, 0, 0x123, 0x100); }));
}

// 13. setConstantBuffer rejects address too large (> 40 bits)
static void test_cb_large_address()
{
	Qmd q = buildQmd(ComputeJob());
	CHECK(throws<std::invalid_argument>([&] { setConstantBuffer(q, 0, 1ULL << 40, 0x100); }));
}

// 14. setConstantBuffer rejects size too large (> 17 bits)
static void test_cb_large_size()
{
	Qmd q = buildQmd(ComputeJob());
	CHECK(throws<std::invalid_argument>([&] { setConstantBuffer(q, 0, 0x1000, 0x20000); }));
}

// 15. encodeLaunch rejects unaligned address
static void test_encode_unaligned()
{
	CHECK(throws<std::invalid_argument>([&] { encodeLaunch(0x1001); }));
}

// 16. encodeLaunch rejects address > 40 bits
static void test_encode_large_address()
{
	CHECK(throws<std::invalid_argument>([&] { encodeLaunch(1ULL << 40); }));
}

int main()
{
	test_crossword();
	test_max_fit();
	test_overflow_barrier();
	test_overflow_gpr();
	test_all_constant_buffers();
	test_encode_decode();
	test_encode_boundary();
	test_wide_field();
	test_cb_error_preserves();
	test_encode_zero();
	test_default_job();
	test_cb_bad_address();
	test_cb_large_address();
	test_cb_large_size();
	test_encode_unaligned();
	test_encode_large_address();

	std::printf("test_launchdesc: %d checks, %d failures\n", checks, failures);
	return failures == 0 ? 0 : 1;
}
