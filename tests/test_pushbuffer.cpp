// test_pushbuffer.cpp — own tests for GPFIFO push-buffer encoding.
// Task D3.
// Distributed under the terms of the MIT License.

#include "fifo/PushBuffer.h"

#include <cstdio>
#include <vector>

using namespace k40::fifo;

static int failures = 0;
static int checks = 0;

#define CHECK(cond)                                                          \
	do {                                                                   \
		checks++;                                                        \
		if (!(cond)) {                                                   \
			failures++;                                                \
			std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);\
		}                                                                \
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

// 1. Encode then decode gives the same header for all four types
static void test_roundtrip_header()
{
	HeaderType types[] = {
		HeaderType::INCREASING,
		HeaderType::NON_INCREASING,
		HeaderType::INCREASE_ONCE,
	};
	for (auto type : types) {
		Header orig = { type, 3, 0x0180, 7 };
		uint32_t enc = encodeHeader(type, orig.subc, orig.method, orig.count);
		Header dec = decodeHeader(enc);
		CHECK(dec.type == orig.type && dec.subc == orig.subc &&
		      dec.method == orig.method && dec.count == orig.count);
	}
	// IMMEDIATE also round-trips (count field = data value)
	Header orig = { HeaderType::IMMEDIATE, 5, 0x0100, 0x1234 };
	uint32_t enc = encodeHeader(orig.type, orig.subc, orig.method, orig.count);
	Header dec = decodeHeader(enc);
	CHECK(dec.type == orig.type && dec.subc == orig.subc &&
	      dec.method == orig.method && dec.count == orig.count);
}

// 2. Bind object on multiple subchannels
static void test_multi_bind()
{
	PushBuffer pb;
	pb.bindObject(0, 0xa067);
	pb.bindObject(1, 0xa1c0);
	pb.bindObject(2, 0xb402);
	CHECK(pb.words().size() == 6);
	// First bind on subc 0
	CHECK(pb.words()[0] == encodeHeader(HeaderType::INCREASING, 0, 0, 1));
	CHECK(pb.words()[1] == 0xa067u);
	// Second bind on subc 1
	CHECK(pb.words()[2] == encodeHeader(HeaderType::INCREASING, 1, 0, 1));
	CHECK(pb.words()[3] == 0xa1c0u);
}

// 3. Ring that wraps twice
static void test_wrap_twice()
{
	GpFifo ring(4);
	// Fill: 3 entries, then wrap
	CHECK(ring.push(0x10000, 0x40, false, 0) == 1);
	CHECK(ring.push(0x20000, 0x40, false, 0) == 2);
	CHECK(ring.push(0x30000, 0x40, false, 0) == 3);
	// GPU consumes 3, put is at 3, free = 1
	CHECK(ring.push(0x40000, 0x40, false, 3) == 0);  // wraps to index 0
	CHECK(ring.words()[6] == 0x40000u);
	// GPU consumes 1 more (get=0), free = 2
	CHECK(ring.push(0x50000, 0x40, false, 0) == 1);
	CHECK(ring.push(0x60000, 0x40, false, 0) == 2);
	// put=2, get=0, free = 3 - 2 = 1
	CHECK(ring.freeEntries(0) == 1);
}

// 4. freeEntries for every get position (ring of 8)
static void test_free_entries_all_positions()
{
	GpFifo ring(8);
	for (unsigned get = 0; get <= 7; get++) {
		// Initially empty, put = 0
		unsigned free = ring.freeEntries(get);
		// With 1 slot reserved, free is in range [0, 7]
		CHECK(free <= 7);
	}
}

// 5. encodeGpEntry and decodeGpEntry round-trip for several addresses
static void test_gp_roundtrip()
{
	uint64_t addrs[] = { 0x0, 0x1000, 0x7ffffc, 0x123456000ULL,
	                     0xff12345000ULL };
	uint32_t lens[] = { 4, 0x100, 0x7ffffc, 0x400, 0x1000 };
	for (auto addr : addrs) {
		for (auto len : lens) {
			if (len > kPushMaxLength)
				continue;
			GpEntry enc = encodeGpEntry(addr, len, false);
			GpInfo dec = decodeGpEntry(enc);
			CHECK(dec.addr == addr && dec.lengthBytes == len &&
			      !dec.noPrefetch);
			GpEntry enc2 = encodeGpEntry(addr, len, true);
			GpInfo dec2 = decodeGpEntry(enc2);
			CHECK(dec2.addr == addr && dec2.lengthBytes == len &&
			      dec2.noPrefetch);
		}
	}
}

// 6. GpFifo ramfcWord4c for various sizes
static void test_ramfc_word4c()
{
	GpFifo r2(2);
	CHECK(r2.ramfcWord4c(0x0ULL) == ((1 << 16) | 0x0u));  // log2=1, upper=0
	CHECK(r2.ramfcWord4c(0x100000000ULL) == ((1 << 16) | 0x1u));

	GpFifo r16(16);
	CHECK(r16.ramfcWord4c(0x0ULL) == ((4 << 16) | 0x0u));  // log2=4
	CHECK(r16.ramfcWord4c(0xdeadbeef000ULL) == ((4 << 16) | 0xdeau));  // upper32=0xdea
}

// 7. decodeBuffer with a single header
static void test_decode_single()
{
	PushBuffer pb;
	pb.begin(0, 0, 3);
	pb.data(1);
	pb.data(2);
	pb.data(3);
	auto methods = decodeBuffer(pb.words());
	CHECK(methods.size() == 3);
	CHECK(methods[0].method == 0 && methods[0].value == 1);
	CHECK(methods[1].method == 4 && methods[1].value == 2);
	CHECK(methods[2].method == 8 && methods[2].value == 3);
}

// 8. PushBuffer sizeBytes matches word count
static void test_size_bytes()
{
	PushBuffer pb;
	pb.begin(0, 0, 5);
	CHECK(pb.sizeBytes() == 4);   // 1 header word = 4 bytes
	pb.data(1);
	pb.data(2);
	pb.data(3);
	CHECK(pb.sizeBytes() == 16);  // 1 header + 3 data = 4 words
	pb.data(4);
	pb.data(5);
	CHECK(pb.sizeBytes() == 24);  // 1 header + 5 data = 6 words
}

// 9. decodeBuffer with empty buffer returns empty
static void test_decode_empty()
{
	auto methods = decodeBuffer(std::vector<uint32_t>());
	CHECK(methods.empty());
}

// 10. GpFifo constructor rejects non-power-of-two
static void test_gpfifo_invalid_sizes()
{
	CHECK(throws<std::invalid_argument>([] { GpFifo(0); }));
	CHECK(throws<std::invalid_argument>([] { GpFifo(3); }));
	CHECK(throws<std::invalid_argument>([] { GpFifo(5); }));
	CHECK(throws<std::invalid_argument>([] { GpFifo(6); }));
	CHECK(throws<std::invalid_argument>([] { GpFifo(10); }));
	// 1 is a valid power of two (2^0)
	GpFifo r1(1);
	CHECK(r1.entries() == 1);
}

// 11. encodeHeader boundary values
static void test_header_boundaries()
{
	// Max values for increasing
	uint32_t enc = encodeHeader(HeaderType::INCREASING, 7, 0x7ffc, 0x1fff);
	CHECK(enc == 0x3fffffffu);
	Header h = decodeHeader(enc);
	CHECK(h.type == HeaderType::INCREASING && h.subc == 7 &&
	      h.method == 0x7ffc && h.count == 0x1fff);
}

// 12. GpEntry with noPrefetch on a larger ring
static void test_gpfifo_no_prefetch()
{
	GpFifo ring(8);
	auto e1 = encodeGpEntry(0x100000, 0x100, true);
	CHECK(e1.word1 & (1u << 31));
	CHECK(ring.push(0x100000, 0x100, true, 0) == 1);
	CHECK(ring.words()[1] == e1.word1);
}

int main()
{
	test_roundtrip_header();
	test_multi_bind();
	test_wrap_twice();
	test_free_entries_all_positions();
	test_gp_roundtrip();
	test_ramfc_word4c();
	test_decode_single();
	test_size_bytes();
	test_decode_empty();
	test_gpfifo_invalid_sizes();
	test_header_boundaries();
	test_gpfifo_no_prefetch();

	std::printf("test_pushbuffer: %d checks, %d failures\n", checks, failures);
	return failures == 0 ? 0 : 1;
}
