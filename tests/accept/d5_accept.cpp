// Acceptance test for task D5, written by the scaffold. Do not edit:
// `make check` compares this file with a recorded hash.
// Build: g++ -std=c++17 -Wall -Wextra -Werror -Isrc tests/accept/d5_accept.cpp
//        src/compute/*.cpp src/fifo/*.cpp
//
// The expected descriptor words were computed by the scaffold from the bit
// positions in reference/mesa/src/gallium/drivers/nouveau/nvc0/cla0c0qmd.h
// and the assignments of nve4_compute_setup_launch_desc and
// nve4_cp_launch_desc_set_cb (nve4_compute.c lines 573 to 632 and 535 to 547).
// The launch methods are those of nve4_launch_grid (lines 869 to 883).
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
	try {
		f();
	} catch (const E&) {
		return true;
	} catch (...) {
		return false;
	}
	return false;
}

static const std::array<uint32_t, 64> kJob1 = {0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0xbc000000u, 0x00001200u, 0x00000000u, 0x00000000u, 0x04014000u, 0x00000040u, 0x00010002u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000200u, 0x00100000u, 0x00010004u, 0x20000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x18012340u, 0x0e000000u, 0x30000800u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u};
static const std::array<uint32_t, 64> kJob2 = {0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0xbc000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x04014000u, 0x00000001u, 0x00010001u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00009d00u, 0x00010000u, 0x00010001u, 0x60000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x01000000u, 0x30000800u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u};
static const std::array<uint32_t, 64> kJob1Cb = {0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0xbc000000u, 0x00001200u, 0x00000000u, 0x00000000u, 0x04014000u, 0x00000040u, 0x00010002u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000200u, 0x00100000u, 0x00010004u, 0x20000081u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00020000u, 0x80000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x23456700u, 0x04000001u, 0x18012340u, 0x0e000000u, 0x30000800u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u, 0x00000000u};

static void report(const char* name, const std::array<uint32_t, 64>& got,
	const std::array<uint32_t, 64>& want)
{
	for (size_t i = 0; i < 64; i++) {
		if (got[i] != want[i])
			std::printf("  %s word %zu (bits %zu to %zu): got 0x%08x, expected 0x%08x\n",
				name, i, i * 32, i * 32 + 31, got[i], want[i]);
	}
}

static void test_bitfield()
{
	Qmd q;
	CHECK(q.words().size() == 64);
	for (uint32_t w : q.words())
		CHECK(w == 0);
	q.set(7, 0, 0xab);
	CHECK(q.words()[0] == 0xab);
	q.set(15, 12, 0x5);
	CHECK(q.words()[0] == 0x50ab);
	// a field that crosses a word boundary
	q.set(39, 28, 0xfff);
	CHECK(q.words()[0] == 0xf00050abu && q.words()[1] == 0xff);
	CHECK(q.get(39, 28) == 0xfff && q.get(15, 12) == 5 && q.get(7, 0) == 0xab);
	// setting a field replaces its old value and leaves its neighbours
	q.set(39, 28, 0x801);
	CHECK(q.words()[0] == 0x100050abu && q.words()[1] == 0x80);
	q.set(1535, 1528, 0x30);
	CHECK(q.words()[47] == 0x30000000u);
	q.set(2047, 2047, 1);
	CHECK(q.words()[63] == 0x80000000u);
	CHECK(throws<std::invalid_argument>([&] { q.set(3, 4, 0); }));
	CHECK(throws<std::invalid_argument>([&] { q.set(2048, 2040, 0); }));
	CHECK(throws<std::invalid_argument>([&] { q.set(3, 0, 0x10); }));
	CHECK(throws<std::invalid_argument>([&] { q.set(100, 0, 0); }));
	CHECK(throws<std::invalid_argument>([&] { q.get(2048, 2040); }));
}

static ComputeJob job1()
{
	ComputeJob j;
	j.codeOffset = 0x1200;
	j.grid[0] = 64; j.grid[1] = 2; j.grid[2] = 1;
	j.block[0] = 16; j.block[1] = 4; j.block[2] = 1;
	j.sharedMemSize = 0x123;
	j.localMemLow = 0x12345;
	j.numGprs = 14;
	j.numBarriers = 3;
	return j;
}

static void test_build()
{
	Qmd q = buildQmd(job1());
	CHECK(q.words() == kJob1);
	if (q.words() != kJob1)
		report("job1", q.words(), kJob1);

	ComputeJob j;
	j.codeOffset = 0;
	j.grid[0] = j.grid[1] = j.grid[2] = 1;
	j.block[0] = j.block[1] = j.block[2] = 1;
	j.sharedMemSize = 40000;
	j.localMemLow = 0;
	j.numGprs = 1;
	j.numBarriers = 0;
	Qmd q2 = buildQmd(j);
	CHECK(q2.words() == kJob2);
	if (q2.words() != kJob2)
		report("job2", q2.words(), kJob2);
	// the L1 configuration follows the shared memory size (nve4_compute.c:605)
	CHECK(q.get(671, 669) == 1 && q2.get(671, 669) == 3);
	j.sharedMemSize = 20000;
	CHECK(buildQmd(j).get(671, 669) == 2);
	j.sharedMemSize = 16 << 10;
	CHECK(buildQmd(j).get(671, 669) == 1);

	// values that do not fit their field
	ComputeJob bad = job1();
	bad.grid[1] = 0x10000;
	CHECK(throws<std::invalid_argument>([&] { buildQmd(bad); }));
	bad = job1();
	bad.numBarriers = 32;
	CHECK(throws<std::invalid_argument>([&] { buildQmd(bad); }));
}

static void test_constant_buffer()
{
	Qmd q = buildQmd(job1());
	setConstantBuffer(q, 7, 0x123456700ULL, 0x800);
	setConstantBuffer(q, 0, 0x20000, 0x10000);
	CHECK(q.words() == kJob1Cb);
	if (q.words() != kJob1Cb)
		report("job1 with buffers", q.words(), kJob1Cb);
	CHECK(q.get(647, 640) == 0x81);
	CHECK(throws<std::invalid_argument>([&] { setConstantBuffer(q, 8, 0x1000, 0x100); }));
	CHECK(throws<std::invalid_argument>([&] { setConstantBuffer(q, 1, 0x1001, 0x100); }));
	CHECK(throws<std::invalid_argument>([&] { setConstantBuffer(q, 1, 0x1000, 0x20000); }));
	CHECK(q.words() == kJob1Cb);
}

static void test_launch_methods()
{
	std::vector<uint32_t> w = encodeLaunch(0x123456700ULL);
	CHECK(w.size() == 6);
	CHECK(w[0] == 0x200120adu && w[1] == 0x01234567u);
	CHECK(w[2] == 0x200120afu && w[3] == 0x3u);
	CHECK(w[4] == 0x20012044u && w[5] == 0x0u);
	std::vector<k40::fifo::Method> m = k40::fifo::decodeBuffer(w);
	CHECK(m.size() == 3);
	CHECK(m[0].subc == 1 && m[0].method == 0x02b4 && m[0].value == 0x01234567u);
	CHECK(m[1].method == 0x02bc && m[1].value == 3);
	CHECK(m[2].method == 0x0110 && m[2].value == 0);
	// the descriptor address is sent shifted right by 8
	CHECK(throws<std::invalid_argument>([] { encodeLaunch(0x123456701ULL); }));
	CHECK(throws<std::invalid_argument>([] { encodeLaunch(1ULL << 40); }));
	CHECK(kComputeClass == 0xa1c0 && kComputeSubchannel == 1 && kQmdBytes == 256);
}

int main()
{
	test_bitfield();
	test_build();
	test_constant_buffer();
	test_launch_methods();
	std::printf("d5_accept: %d checks, %d failures\n", checks, failures);
	return failures == 0 ? 0 : 1;
}
