// Acceptance test for task D3, written by the scaffold. Do not edit:
// `make check` compares this file with a recorded hash.
// Build: g++ -std=c++17 -Wall -Wextra -Werror -Isrc tests/accept/d3_accept.cpp src/fifo/*.cpp
//
// The expected values come from:
//   method headers  reference/mesa/src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h
//                   NVC0_FIFO_PKHDR_SQ, _NI, _IL, _1I (lines 66 to 88)
//   GPFIFO entry    reference/nouveau/nouveau_dma.c nv50_dma_push (lines 72 to 95)
//   length limit    reference/nouveau/nouveau_dma.h NV50_DMA_PUSH_MAX_LENGTH (line 50)
//   USERD offsets   reference/nouveau/nouveau_dma.c lines 92 and 104
#include "fifo/PushBuffer.h"

#include <cstdio>
#include <stdexcept>
#include <vector>

using namespace k40::fifo;

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

static void test_header_encode()
{
	// BEGIN_NVC0(push, SUBC_CP(0x02b4), 1): subchannel 1, method 0x02b4, one word
	CHECK(encodeHeader(HeaderType::INCREASING, 1, 0x02b4, 1) == 0x200120adu);
	CHECK(encodeHeader(HeaderType::INCREASING, 0, 0x0000, 1) == 0x20010000u);
	CHECK(encodeHeader(HeaderType::INCREASING, 1, 0x0188, 2) == 0x20022062u);
	CHECK(encodeHeader(HeaderType::NON_INCREASING, 1, 0x01b4, 16) == 0x6010206du);
	CHECK(encodeHeader(HeaderType::INCREASE_ONCE, 1, 0x01b0, 5) == 0xa005206cu);
	CHECK(encodeHeader(HeaderType::IMMEDIATE, 1, 0x1698, 0x1000) == 0x900025a6u);
	CHECK(encodeHeader(HeaderType::INCREASING, 7, 0x7ffc, 0x1fff) == 0x3fffffffu);

	CHECK(throws<std::invalid_argument>([] { encodeHeader(HeaderType::INCREASING, 8, 0x100, 1); }));
	CHECK(throws<std::invalid_argument>([] { encodeHeader(HeaderType::INCREASING, 1, 0x102, 1); }));
	CHECK(throws<std::invalid_argument>([] { encodeHeader(HeaderType::INCREASING, 1, 0x8000, 1); }));
	CHECK(throws<std::invalid_argument>([] { encodeHeader(HeaderType::INCREASING, 1, 0x100, 0x2000); }));
	CHECK(throws<std::invalid_argument>([] { encodeHeader(HeaderType::IMMEDIATE, 1, 0x100, 0x2000); }));
}

static void test_header_decode()
{
	Header h = decodeHeader(0x200120adu);
	CHECK(h.type == HeaderType::INCREASING && h.subc == 1 && h.method == 0x02b4 && h.count == 1);
	h = decodeHeader(0x6010206du);
	CHECK(h.type == HeaderType::NON_INCREASING && h.subc == 1 && h.method == 0x01b4 && h.count == 16);
	h = decodeHeader(0xa005206cu);
	CHECK(h.type == HeaderType::INCREASE_ONCE && h.method == 0x01b0 && h.count == 5);
	h = decodeHeader(0x900025a6u);
	CHECK(h.type == HeaderType::IMMEDIATE && h.subc == 1 && h.method == 0x1698 && h.count == 0x1000);
	// a type that this driver does not produce
	CHECK(throws<std::invalid_argument>([] { decodeHeader(0x00040000u); }));
	CHECK(throws<std::invalid_argument>([] { decodeHeader(0xc0010000u); }));
}

static void test_pushbuffer()
{
	PushBuffer pb;
	CHECK(pb.words().empty() && pb.pending() == 0);
	pb.bindObject(1, 0xa1c0);
	CHECK(pb.words().size() == 2);
	CHECK(pb.words()[0] == 0x20012000u && pb.words()[1] == 0xa1c0u);

	pb.begin(1, 0x0188, 2);
	CHECK(pb.pending() == 2);
	pb.data(0x00000001);
	pb.data(0x23456000);
	CHECK(pb.pending() == 0);
	pb.immediate(1, 0x1698, 0x1000);
	pb.beginNonIncreasing(1, 0x01b4, 3);
	pb.data(7);
	pb.data(8);
	pb.data(9);
	pb.beginIncreaseOnce(1, 0x01b0, 3);
	pb.data(0x41);
	pb.data(0x42);
	pb.data(0x43);
	CHECK(pb.words().size() == 14);
	CHECK(pb.words()[2] == 0x20022062u && pb.words()[4] == 0x23456000u);
	CHECK(pb.words()[5] == 0x900025a6u);
	CHECK(pb.sizeBytes() == 56);

	// misuse
	CHECK(throws<std::logic_error>([&] { pb.data(1); }));
	pb.begin(1, 0x0100, 2);
	pb.data(1);
	CHECK(throws<std::logic_error>([&] { pb.begin(1, 0x0200, 1); }));
	CHECK(throws<std::logic_error>([&] { pb.immediate(1, 0x0200, 1); }));
	CHECK(pb.pending() == 1);
	pb.data(2);
	CHECK(pb.words().size() == 17);
	CHECK(throws<std::invalid_argument>([&] { pb.begin(1, 0x0100, 0); }));
}

static void test_decode_buffer()
{
	PushBuffer pb;
	pb.begin(1, 0x0188, 2);
	pb.data(0x11);
	pb.data(0x22);
	pb.beginNonIncreasing(1, 0x01b4, 2);
	pb.data(0x33);
	pb.data(0x44);
	pb.beginIncreaseOnce(2, 0x0300, 3);
	pb.data(0x55);
	pb.data(0x66);
	pb.data(0x77);
	pb.immediate(1, 0x1698, 5);
	std::vector<Method> m = decodeBuffer(pb.words());
	CHECK(m.size() == 8);
	CHECK(m[0].subc == 1 && m[0].method == 0x0188 && m[0].value == 0x11);
	CHECK(m[1].method == 0x018c && m[1].value == 0x22);
	CHECK(m[2].method == 0x01b4 && m[3].method == 0x01b4 && m[3].value == 0x44);
	CHECK(m[4].subc == 2 && m[4].method == 0x0300 && m[4].value == 0x55);
	CHECK(m[5].method == 0x0304 && m[6].method == 0x0304 && m[6].value == 0x77);
	CHECK(m[7].method == 0x1698 && m[7].value == 5);

	std::vector<uint32_t> cut = pb.words();
	cut.resize(2);
	CHECK(throws<std::invalid_argument>([&] { decodeBuffer(cut); }));
	CHECK(decodeBuffer(std::vector<uint32_t>()).empty());
}

static void test_gp_entry()
{
	GpEntry e = encodeGpEntry(0x123456000ULL, 0x40);
	CHECK(e.word0 == 0x23456000u && e.word1 == 0x00004001u);
	e = encodeGpEntry(0x123456000ULL, 0x40, true);
	CHECK(e.word1 == 0x80004001u);
	e = encodeGpEntry(0x1000, 0x7ffffc);
	CHECK(e.word0 == 0x1000u && e.word1 == 0x7ffffc00u);
	GpInfo i = decodeGpEntry(encodeGpEntry(0xff12345000ULL, 0x1000, true));
	CHECK(i.addr == 0xff12345000ULL && i.lengthBytes == 0x1000 && i.noPrefetch);

	CHECK(throws<std::invalid_argument>([] { encodeGpEntry(0x1002, 0x40); }));
	CHECK(throws<std::invalid_argument>([] { encodeGpEntry(0x1000, 0x42); }));
	CHECK(throws<std::invalid_argument>([] { encodeGpEntry(0x1000, 0); }));
	CHECK(throws<std::invalid_argument>([] { encodeGpEntry(0x1000, 0x800000); }));
	CHECK(throws<std::invalid_argument>([] { encodeGpEntry(1ULL << 40, 0x40); }));
	CHECK(kUserdGpGet == 0x88 && kUserdGpPut == 0x8c);
	CHECK(kGpEntryBytes == 8);
}

static void test_gpfifo_ring()
{
	CHECK(throws<std::invalid_argument>([] { GpFifo bad(6); }));
	CHECK(throws<std::invalid_argument>([] { GpFifo bad(0); }));
	GpFifo ring(4);
	CHECK(ring.entries() == 4 && ring.log2Entries() == 2);
	CHECK(ring.words().size() == 8);
	CHECK(ring.put() == 0);
	CHECK(ring.freeEntries(0) == 3);

	CHECK(ring.push(0x10000, 0x40) == 1);
	CHECK(ring.words()[0] == 0x10000u && ring.words()[1] == 0x4000u);
	CHECK(ring.push(0x20000, 0x80) == 2);
	CHECK(ring.push(0x30000, 0x100, true) == 3);
	CHECK(ring.words()[5] == 0x80010000u);
	// the GPU has consumed nothing (get = 0): one slot must stay free
	CHECK(ring.freeEntries(0) == 0);
	CHECK(throws<std::overflow_error>([&] { ring.push(0x40000, 0x40, false, 0); }));
	CHECK(ring.put() == 3);
	// the GPU has consumed two entries
	CHECK(ring.freeEntries(2) == 2);
	CHECK(ring.push(0x40000, 0x40, false, 2) == 0);
	CHECK(ring.words()[6] == 0x40000u);
	CHECK(ring.push(0x50000, 0x40, false, 2) == 1);
	CHECK(ring.words()[0] == 0x50000u);
	CHECK(ring.freeEntries(2) == 0);
	// the word that gk104_chan_ramfc_write puts at 0x4c of the channel block
	CHECK(ring.ramfcWord4c(0x0123456000ULL) == 0x00020001u);
}

int main()
{
	test_header_encode();
	test_header_decode();
	test_pushbuffer();
	test_decode_buffer();
	test_gp_entry();
	test_gpfifo_ring();
	std::printf("d3_accept: %d checks, %d failures\n", checks, failures);
	return failures == 0 ? 0 : 1;
}
