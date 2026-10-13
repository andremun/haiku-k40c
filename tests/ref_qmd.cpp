// ref_qmd.cpp — build the descriptor of the reference run and compare.
// Distributed under the terms of the MIT License.
//
// The reference job (2026-10-13 Linux run, compute_test):
//   codeOffset = 0x7f100, grid = {16, 1, 1}, block = {64, 1, 1},
//   sharedMemSize = 0, localMemLow = 0, numGprs = 5, numBarriers = 0,
//   constant buffer 7 at 0x510000, size 0x800.
#include "compute/LaunchDesc.h"

#include <cstdio>
#include <string>
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

static ComputeJob referenceJob()
{
	ComputeJob j;
	j.codeOffset = 0x7f100;
	j.grid[0] = 16; j.grid[1] = 1; j.grid[2] = 1;
	j.block[0] = 64; j.block[1] = 1; j.block[2] = 1;
	j.sharedMemSize = 0;
	j.localMemLow = 0;
	j.numGprs = 5;
	j.numBarriers = 0;
	return j;
}

int main(int argc, char** argv)
{
	ComputeJob j = referenceJob();
	Qmd q = buildQmd(j);
	setConstantBuffer(q, 7, 0x510000, 0x800);

	const auto& words = q.words();

	// Check --words mode: print 64 words, nothing else.
	if (argc > 1 && std::string(argv[1]) == "--words") {
		for (int i = 0; i < 64; i++)
			std::printf("0x%08x\n", words[i]);
		return 0;
	}

	// Without --words: smoke checks using get() for correctness.
	// PROGRAM_OFFSET = 0x7f100 (bits 287:256)
	CHECK(q.get(287, 256) == 0x7f100);

	// CTA_RASTER_WIDTH = 16 (bits 415:384)
	CHECK(q.get(415, 384) == 16);

	// CTA_THREAD_DIMENSION0 = 64 (bits 607:592)
	CHECK(q.get(607, 592) == 64);

	// CONSTANT_BUFFER_VALID(7) = 1 (bit 647)
	CHECK(q.get(647, 647) == 1);

	// CONSTANT_BUFFER_ADDR_LOWER(7) = 0x510000 (bits 1407:1376)
	CHECK(q.get(1407, 1376) == 0x510000);

	// CONSTANT_BUFFER_SIZE(7) = 0x800 (bits 1439:1423)
	CHECK(q.get(1439, 1423) == 0x800);

	// REGISTER_COUNT = 5 (bits 1503:1496)
	CHECK(q.get(1503, 1496) == 5);

	// SASS_VERSION = 0x30 (bits 1535:1528)
	CHECK(q.get(1535, 1528) == 0x30);

	// SHADER_LOCAL_MEMORY_CRS_SIZE = 0x800 (bits 1527:1504)
	CHECK(q.get(1527, 1504) == 0x800);

	// L1_CONFIGURATION = 1 (bits 671:669) — sharedMemSize=0 → 16KB
	CHECK(q.get(671, 669) == 1);

	std::printf("ref_qmd: %d checks, %d failures\n", checks, failures);
	return failures == 0 ? 0 : 1;
}
