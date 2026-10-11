// Acceptance test for task D1, written by the scaffold. Do not edit:
// `make check` compares this file with a recorded hash.
// Build: g++ -std=c++17 -Wall -Wextra -Werror -Isrc tests/accept/d1_accept.cpp src/hw/*.cpp
#include "hw/RegisterIO.h"

#include <cstdio>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace k40;

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

static void test_mock_basic()
{
	MockMMIO io(0x1000);
	RegisterIO& r = io;
	CHECK(r.read32(0x10) == 0);
	r.write32(0x10, 0xdeadbeef);
	CHECK(r.read32(0x10) == 0xdeadbeef);
	CHECK(r.read32(0x14) == 0);
	CHECK(io.log().size() == 4);
	CHECK(io.log()[0].op == Access::READ && io.log()[0].offset == 0x10 && io.log()[0].value == 0);
	CHECK(io.log()[1].op == Access::WRITE && io.log()[1].offset == 0x10
		&& io.log()[1].value == 0xdeadbeef);
	CHECK(io.log()[2].op == Access::READ && io.log()[2].value == 0xdeadbeef);
	io.clearLog();
	CHECK(io.log().empty());
	CHECK(r.read32(0x10) == 0xdeadbeef);
}

static void test_mock_peek_poke()
{
	MockMMIO io(0x100);
	io.poke(0x20, 0x12345678);
	CHECK(io.peek(0x20) == 0x12345678);
	CHECK(io.log().empty());
	CHECK(io.read32(0x20) == 0x12345678);
	CHECK(io.log().size() == 1);
}

static void test_mock_bounds()
{
	MockMMIO io(0x100);
	CHECK(throws<std::out_of_range>([&] { io.read32(0x100); }));
	CHECK(throws<std::out_of_range>([&] { io.write32(0x104, 1); }));
	CHECK(throws<std::out_of_range>([&] { io.read32(0x12); }));
	CHECK(throws<std::out_of_range>([&] { io.write32(0x01, 1); }));
	CHECK(throws<std::out_of_range>([&] { io.poke(0x100, 1); }));
	CHECK(!throws<std::out_of_range>([&] { io.read32(0xfc); }));
	CHECK(io.log().size() == 1);
}

static void test_mask()
{
	MockMMIO io(0x100);
	io.poke(0x40, 0xffff0000);
	uint32_t old = io.mask32(0x40, 0x00ff00ff, 0x00120034);
	CHECK(old == 0xffff0000);
	CHECK(io.peek(0x40) == 0xff120034);
	CHECK(io.log().size() == 2);
	CHECK(io.log()[0].op == Access::READ && io.log()[1].op == Access::WRITE);
	CHECK(io.log()[1].value == 0xff120034);
}

static void test_mock_hooks()
{
	MockMMIO io(0x1000);
	int reads = 0;
	// a status register that reports "ready" (bit 31) on the third read
	io.onRead(0x800, [&](uint32_t current) {
		reads++;
		return reads >= 3 ? (current | 0x80000000u) : current;
	});
	CHECK((io.read32(0x800) & 0x80000000u) == 0);
	CHECK((io.read32(0x800) & 0x80000000u) == 0);
	CHECK((io.read32(0x800) & 0x80000000u) != 0);
	CHECK(io.log()[2].value == 0x80000000u);
	CHECK(io.peek(0x800) == 0);

	// a write to a control register sets a status register
	io.onWrite(0x100, [](MockMMIO& m, uint32_t value) {
		if (value == 2)
			m.poke(0x104, 0x1);
	});
	io.write32(0x100, 1);
	CHECK(io.peek(0x104) == 0);
	io.write32(0x100, 2);
	CHECK(io.peek(0x104) == 1);
	CHECK(io.peek(0x100) == 2);
}

static void test_trace_replay()
{
	std::vector<Access> expected = {
		{Access::READ, 0x000000, 0x0f1000a1},
		{Access::WRITE, 0x000200, 0x00000100},
		{Access::READ, 0x000200, 0x00000100},
	};
	TraceMMIO io(expected);
	CHECK(!io.done());
	CHECK(io.position() == 0);
	CHECK(io.read32(0x000000) == 0x0f1000a1);
	io.write32(0x000200, 0x100);
	CHECK(io.position() == 2);
	CHECK(io.read32(0x000200) == 0x100);
	CHECK(io.done());
	CHECK(throws<TraceMismatch>([&] { io.read32(0); }));
}

static void test_trace_mismatch()
{
	std::vector<Access> expected = {
		{Access::WRITE, 0x000200, 0x00000100},
		{Access::READ, 0x000100, 0x00000000},
	};
	{
		TraceMMIO io(expected);
		CHECK(throws<TraceMismatch>([&] { io.write32(0x000200, 0x101); }));
		CHECK(io.position() == 0);
	}
	{
		TraceMMIO io(expected);
		CHECK(throws<TraceMismatch>([&] { io.write32(0x000204, 0x100); }));
	}
	{
		TraceMMIO io(expected);
		CHECK(throws<TraceMismatch>([&] { io.read32(0x000200); }));
	}
	{
		TraceMMIO io(expected);
		io.write32(0x000200, 0x100);
		size_t index = 99;
		try {
			io.write32(0x000100, 0);
		} catch (const TraceMismatch& e) {
			index = e.index();
			CHECK(std::string(e.what()).find("0x000100") != std::string::npos);
		}
		CHECK(index == 1);
	}
}

static void test_trace_text()
{
	std::istringstream in(
		"# boot\n"
		"R 0x000000 0x0f1000a1\n"
		"\n"
		"W 0x000200 0x00000100   # enable\n"
		"R 0x00020c 0x00000000\n");
	std::vector<Access> t = parseTrace(in);
	CHECK(t.size() == 3);
	CHECK(t[0].op == Access::READ && t[0].offset == 0 && t[0].value == 0x0f1000a1);
	CHECK(t[1].op == Access::WRITE && t[1].offset == 0x200 && t[1].value == 0x100);
	CHECK(t[2].offset == 0x20c);

	CHECK(formatTrace(t) ==
		"R 0x000000 0x0f1000a1\n"
		"W 0x000200 0x00000100\n"
		"R 0x00020c 0x00000000\n");

	std::istringstream bad("X 0x000000 0x00000000\n");
	CHECK(throws<std::invalid_argument>([&] { parseTrace(bad); }));
	std::istringstream bad2("R 0x000000\n");
	CHECK(throws<std::invalid_argument>([&] { parseTrace(bad2); }));
}

// The point of the layer: the same routine runs on a mock and on a trace.
static bool start_engine(RegisterIO& io)
{
	io.write32(0x10c, 0);
	io.write32(0x100, 2);
	for (int i = 0; i < 5; i++) {
		if (io.read32(0x800) & 0x80000000u)
			return true;
	}
	return false;
}

static void test_record_and_replay()
{
	MockMMIO mock(0x1000);
	int polls = 0;
	mock.onRead(0x800, [&](uint32_t c) { return ++polls >= 2 ? (c | 0x80000000u) : c; });
	CHECK(start_engine(mock));
	CHECK(mock.log().size() == 4);

	std::istringstream in(formatTrace(mock.log()));
	TraceMMIO replay(parseTrace(in));
	CHECK(start_engine(replay));
	CHECK(replay.done());
}

int main()
{
	test_mock_basic();
	test_mock_peek_poke();
	test_mock_bounds();
	test_mask();
	test_mock_hooks();
	test_trace_replay();
	test_trace_mismatch();
	test_trace_text();
	test_record_and_replay();
	std::printf("d1_accept: %d checks, %d failures\n", checks, failures);
	return failures == 0 ? 0 : 1;
}
