// Acceptance test for task R1, written by the scaffold. Do not edit:
// `make check` compares this file with a recorded hash.
//
// Each check reproduces a defect that the external review of 2026-10-13
// found in the host code (docs/external/2026-10-13-review-outcome-package-b.md,
// findings F1, F2, F3, F5, F6, F7). Before task R1 these checks fail or the
// program stops with undefined behaviour. F4 (the comparison tool) has its
// own test, tests/accept/r1_accept.py.
#include "compute/LaunchDesc.h"
#include "fifo/PushBuffer.h"
#include "hw/RegisterIO.h"
#include "mmu/PageTable.h"

#include <cstdio>
#include <functional>
#include <sstream>
#include <stdexcept>
#include <string>

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

template <typename E>
static bool throws(const std::function<void()>& f)
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

// A simple allocator for page tables: blocks at 1 MiB and up, 4 KiB apart.
static k40::mmu::AddressSpace newSpace()
{
	static uint64_t next = 0;
	next = 0x100000;
	return k40::mmu::AddressSpace([](uint32_t bytes) {
		uint64_t a = next;
		next += (bytes + 0xfff) & ~uint64_t(0xfff);
		return a;
	});
}

using k40::mmu::Target;

// F1: a mapping of one page size must not overlap a mapping of the other.
static void test_f1_mixed_page_sizes()
{
	{
		// small page first, then a large page that covers it
		auto as = newSpace();
		as.map(0x1000, 0x40000000, 0x1000, 12, Target::VRAM);
		CHECK(throws<std::invalid_argument>([&] { as.map(0, 0x50000000, 0x20000, 17, Target::VRAM); }));
		CHECK(as.translate(0x1000).value_or(0) == 0x40000000);
		CHECK(!as.translate(0x0).has_value());
	}
	{
		// large page first, then a small page inside it (not at its start)
		auto as = newSpace();
		as.map(0x20000, 0x50000000, 0x20000, 17, Target::VRAM);
		CHECK(throws<std::invalid_argument>([&] { as.map(0x31000, 0x40000000, 0x1000, 12, Target::VRAM); }));
		CHECK(as.translate(0x31000).value_or(0) == 0x50011000);
	}
	{
		// small pages that do not overlap a large page are allowed
		auto as = newSpace();
		as.map(0x20000, 0x50000000, 0x20000, 17, Target::VRAM);
		CHECK(!throws<std::exception>([&] { as.map(0x40000, 0x40000000, 0x1000, 12, Target::VRAM); }));
		CHECK(as.translate(0x40000).value_or(0) == 0x40000000);
	}
}

// F2: an unmap that does not remove the mapping must not succeed.
static void test_f2_unmap()
{
	auto as = newSpace();
	as.map(0, 0x50000000, 0x20000, 17, Target::VRAM);
	CHECK(throws<std::invalid_argument>([&] { as.unmap(0, 0x1000, 12); }));
	CHECK(as.translate(0x0).value_or(0) == 0x50000000);
	as.unmap(0, 0x20000, 17);
	CHECK(!as.translate(0x0).has_value());
	CHECK(!as.translate(0x1ffff).has_value());
}

// F3: address and page-size checks before any change and before any shift.
static void test_f3_validation()
{
	auto as = newSpace();
	// The end of the range wraps around 2^64.
	CHECK(throws<std::invalid_argument>([&] { as.map(0x1000, 0, 0xfffffffffffff000ULL, 12, Target::VRAM); }));
	// A physical address that the 40-bit address of the K40c cannot hold.
	CHECK(throws<std::invalid_argument>([&] { as.map(0x1000, 1ULL << 40, 0x1000, 12, Target::VRAM); }));
	// The end of the physical range goes past 40 bits.
	CHECK(throws<std::invalid_argument>([&] { as.map(0x1000, (1ULL << 40) - 0x1000, 0x2000, 12, Target::VRAM); }));
	// Page sizes other than 12 and 17, including one that would shift by 64.
	CHECK(throws<std::invalid_argument>([&] { as.map(0, 0, 0x1000, 64, Target::VRAM); }));
	CHECK(throws<std::invalid_argument>([&] { as.map(0, 0, 0x2000, 13, Target::VRAM); }));
	CHECK(throws<std::invalid_argument>([&] { as.unmap(0, 0x1000, 64); }));
	// Nothing was mapped by the failed calls.
	CHECK(!as.translate(0x1000).has_value());
	CHECK(!as.translate(0x0).has_value());
}

// F5: launch-descriptor inputs that do not fit must be refused.
static void test_f5_launch_desc()
{
	using namespace k40::compute;
	ComputeJob j;
	j.sharedMemSize = 0xffffffffu;   // wraps to 0 if 0xff is added in 32 bits
	CHECK(throws<std::invalid_argument>([&] { buildQmd(j); }));
	ComputeJob k;
	k.localMemLow = 0x1000000;        // 25 bits: does not fit the 24-bit field
	CHECK(throws<std::invalid_argument>([&] { buildQmd(k); }));
	Qmd q;
	CHECK(throws<std::invalid_argument>([&] { q.get(64, 0); }));   // 65 bits
	CHECK(q.get(63, 0) == 0);                                        // 64 bits is allowed
}

// F6: binding an object while a packet waits for data must be refused,
// and a buffer with an incomplete packet must not be handed out.
static void test_f6_push_buffer()
{
	using namespace k40::fifo;
	{
		PushBuffer pb;
		pb.begin(1, 0x100, 1);
		CHECK(throws<std::logic_error>([&] { pb.bindObject(1, 0xa1c0); }));
		pb.data(0x1234);
		CHECK(!throws<std::exception>([&] { decodeBuffer(pb.words()); }));
	}
	{
		PushBuffer pb;
		pb.begin(1, 0x100, 2);
		pb.data(1);
		CHECK(throws<std::logic_error>([&] { pb.finishedWords(); }));
		pb.data(2);
		CHECK(pb.finishedWords() == pb.words());
	}
}

// F7: a trace line with a value that does not fit 32 bits, or with
// characters after the number, must be refused, not truncated.
static void test_f7_trace_parse()
{
	auto parse = [](const std::string& text) {
		std::istringstream in(text);
		return k40::parseTrace(in);
	};
	CHECK(throws<std::invalid_argument>([&] { parse("W 0x100000000 0x1\n"); }));
	CHECK(throws<std::invalid_argument>([&] { parse("W 0x10 0x100000001\n"); }));
	CHECK(throws<std::invalid_argument>([&] { parse("W 0x10zz 0x1\n"); }));
	CHECK(throws<std::invalid_argument>([&] { parse("W 0x10 0x1 extra\n"); }));
	CHECK(throws<std::invalid_argument>([&] { parse("W -0x10 0x1\n"); }));
	// Still valid: a comment after the value, and the plain format.
	auto t = parse("R 0x000200 0x00000100\nW 0x000204 0x7 # comment\n");
	CHECK(t.size() == 2 && t[1].offset == 0x204 && t[1].value == 7);
}

int main()
{
	test_f1_mixed_page_sizes();
	test_f2_unmap();
	test_f3_validation();
	test_f5_launch_desc();
	test_f6_push_buffer();
	test_f7_trace_parse();
	std::printf("r1_accept: %d checks, %d failures\n", checks, failures);
	return failures ? 1 : 0;
}
