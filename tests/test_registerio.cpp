// test_registerio.cpp — own tests for RegisterIO
// Task D1.
// Distributed under the terms of the MIT License.

#include "hw/RegisterIO.h"

#include <cstdio>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace k40;

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

// 1. Hook that counts writes (hook runs after write32 stores the value)
static void test_write_counter_hook()
{
	MockMMIO io(0x100);

	// A write hook on 0x10 that sets another register
	io.onWrite(0x10, [](MockMMIO& m, uint32_t value) {
		if (value == 0x42)
			m.poke(0x14, 0x99);
	});

	io.write32(0x10, 1);
	io.write32(0x10, 0x42);
	io.write32(0x18, 3);

	CHECK(io.log().size() == 3);
	// Hook was only called for 0x10 with value 0x42
	CHECK(io.peek(0x14) == 0x99);
	CHECK(io.peek(0x10) == 0x42);
}

// 2. mask32 on TraceMMIO
static void test_mask_trace()
{
	std::vector<Access> expected = {
		{Access::READ, 0x000100, 0xff00ff00},
		{Access::WRITE, 0x000100, 0x00120012},
	};
	TraceMMIO io(expected);
	// mask32(0x000100, 0xff00ff00, 0x00120012)
	// old = 0xff00ff00, new = (0xff00ff00 & ~0xff00ff00) | 0x00120012 = 0x00000000 | 0x00120012 = 0x00120012
	uint32_t old = io.mask32(0x000100, 0xff00ff00, 0x00120012);
	CHECK(old == 0xff00ff00);
	CHECK(io.done());
}

// 3. Trace with only comments
static void test_comment_only_trace()
{
	std::istringstream in("# comment only\n# another\n\n");
	auto t = parseTrace(in);
	CHECK(t.empty());
}

// 4. Hex values in upper case (formatTrace output is lowercase, parseTrace handles both)
static void test_uppercase_hex_parse()
{
	std::istringstream in("R 0x000200 0xDEADBEEF\n");
	auto t = parseTrace(in);
	CHECK(t.size() == 1);
	CHECK(t[0].op == Access::READ && t[0].value == 0xDEADBEEF);
}

// 5. Size that is not a multiple of 4
static void test_non_multiple_size()
{
	// Size must be multiple of 4 for uint32_t array
	// Constructor should accept it (integer division), but only aligned offsets
	// work
	MockMMIO io(0x101);  // 0x101 / 4 = 64 uint32_t = 256 bytes capacity
	io.poke(0x100, 0x12345678);
	CHECK(io.peek(0x100) == 0x12345678);
}

// 6. Multiple hooks on same offset — last one wins (map behavior)
static void test_hook_overwrite()
{
	MockMMIO io(0x100);
	int callCount = 0;
	io.onRead(0x20, [&](uint32_t current) {
		(void)current;
		callCount = 1;
		return 0x11111111;
	});
	io.onRead(0x20, [&](uint32_t current) {
		(void)current;
		callCount = 2;
		return 0x22222222;
	});

	CHECK(io.read32(0x20) == 0x22222222);
	CHECK(callCount == 2);
}

// 7. TraceMismatch message format
static void test_trace_mismatch_message()
{
	std::vector<Access> expected = {
		{Access::WRITE, 0x000200, 0x00000100},
	};
	TraceMMIO io(expected);
	try {
		io.read32(0x000300);
	} catch (const TraceMismatch& e) {
		std::string msg(e.what());
		CHECK(msg.find("TraceMismatch") != std::string::npos);
		CHECK(msg.find("0x000300") != std::string::npos);
		CHECK(e.index() == 0);
	}
}

// 8. Empty trace vector — done() immediately
static void test_empty_trace()
{
	std::vector<Access> expected;
	TraceMMIO io(expected);
	CHECK(io.done());
	CHECK(io.position() == 0);
}

// 9. TraceMMIO position accuracy
static void test_trace_position()
{
	std::vector<Access> expected = {
		{Access::READ, 0x00, 0x11},
		{Access::READ, 0x04, 0x22},
		{Access::WRITE, 0x08, 0x33},
		{Access::READ, 0x0C, 0x44},
	};
	TraceMMIO io(expected);
	CHECK(io.position() == 0);
	CHECK(!io.done());

	io.read32(0x00);
	CHECK(io.position() == 1);
	CHECK(!io.done());

	io.read32(0x04);
	CHECK(io.position() == 2);

	io.write32(0x08, 0x33);
	CHECK(io.position() == 3);

	io.read32(0x0C);
	CHECK(io.position() == 4);
	CHECK(io.done());
}

// 10. mask32 returns old, stores new
static void test_mask_stores_new()
{
	MockMMIO io(0x100);
	io.poke(0x50, 0xAABBCCDD);
	uint32_t old = io.mask32(0x50, 0x00FF0000, 0x00110000);
	CHECK(old == 0xAABBCCDD);
	CHECK(io.peek(0x50) == ((0xAABBCCDD & ~0x00FF0000) | 0x00110000));
}

// 11. parseTrace with trailing spaces
static void test_parse_trailing_spaces()
{
	std::istringstream in("R 0x000100 0x00000001   \n");
	auto t = parseTrace(in);
	CHECK(t.size() == 1);
	CHECK(t[0].op == Access::READ && t[0].offset == 0x100);
}

// 12. formatTrace round-trip
static void test_format_roundtrip()
{
	std::vector<Access> original = {
		{Access::READ, 0x000000, 0x0f100000},
		{Access::WRITE, 0x000100, 0x00000001},
		{Access::READ, 0x000200, 0x80000000},
	};
	std::istringstream s(formatTrace(original));
	auto t = parseTrace(s);
	CHECK(t.size() == 3);
	for (size_t i = 0; i < original.size(); i++) {
		CHECK(t[i].op == original[i].op);
		CHECK(t[i].offset == original[i].offset);
		CHECK(t[i].value == original[i].value);
	}
}

// 13. Poke does not trigger hooks
static void test_poke_no_hooks()
{
	MockMMIO io(0x100);
	int triggered = 0;
	io.onWrite(0x50, [&](MockMMIO& m, uint32_t v) {
		(void)m;
		(void)v;
		triggered = 1;
	});
	io.poke(0x50, 0xBEEF);
	CHECK(triggered == 0);
	CHECK(io.peek(0x50) == 0xBEEF);
}

// 14. Multiple writes, clear, verify
static void test_clear_log_resets_count()
{
	MockMMIO io(0x100);
	io.write32(0x10, 1);
	io.write32(0x14, 2);
	CHECK(io.log().size() == 2);

	io.clearLog();
	CHECK(io.log().empty());

	io.write32(0x18, 3);
	CHECK(io.log().size() == 1);
	CHECK(io.log()[0].value == 3);
}

// 15. TraceMMIO rejects wrong type (write when expecting read)
static void test_trace_wrong_type()
{
	std::vector<Access> expected = {
		{Access::READ, 0x100, 0x12345678},
	};
	TraceMMIO io(expected);
	CHECK(throws<TraceMismatch>([&] { io.write32(0x100, 0); }));
	CHECK(io.position() == 0);  // position unchanged on mismatch
}

// 16. mask32 on TraceMMIO with specific bit pattern
static void test_mask_bit_pattern()
{
	std::vector<Access> expected = {
		{Access::READ, 0x200, 0xFFFFFFFF},
		{Access::WRITE, 0x200, 0x0000FFFF},
	};
	TraceMMIO io(expected);
	uint32_t old = io.mask32(0x200, 0xFFFF0000, 0x00000000);
	CHECK(old == 0xFFFFFFFF);
	CHECK(io.done());
}

int main()
{
	test_write_counter_hook();
	test_mask_trace();
	test_comment_only_trace();
	test_uppercase_hex_parse();
	test_non_multiple_size();
	test_hook_overwrite();
	test_trace_mismatch_message();
	test_empty_trace();
	test_trace_position();
	test_mask_stores_new();
	test_parse_trailing_spaces();
	test_format_roundtrip();
	test_poke_no_hooks();
	test_clear_log_resets_count();
	test_trace_wrong_type();
	test_mask_bit_pattern();

	std::printf("test_registerio: %d checks, %d failures\n", checks, failures);
	return failures == 0 ? 0 : 1;
}
