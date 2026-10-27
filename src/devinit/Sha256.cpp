// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "devinit/Sha256.h"

namespace k40::devinit {
namespace {
// Algorithm constants, not GPU constants: NIST FIPS 180-4 section 4.2.2.
// https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf
constexpr uint32_t rounds[] = { // no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5, // no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174, // no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da, // no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967, // no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85, // no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070, // no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3, // no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2, // no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.
};
uint32_t rotate(uint32_t v, unsigned n) { return (v >> n) | (v << (32 - n)); }
}

Digest sha256(const uint8_t* data, uint32_t size)
{
    // Initial state: FIPS 180-4 section 5.3.3. All arithmetic is modulo 2^32.
    uint32_t state[] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a, // no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.
                        0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19}; // no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.
    const uint64_t padded = (uint64_t(size) + 9 + 63) / 64 * 64;
    for (uint64_t block = 0; block < padded; block += 64) {
        uint32_t words[64] = {};
        for (unsigned j = 0; j < 64; ++j) {
            const uint64_t at = block + j;
            uint8_t byte = 0;
            if (at < size) byte = data[at];
            else if (at == size) byte = 0x80; // no source: SHA-256 algorithm, not hardware. NIST FIPS 180-4 sections 4.2.2,5.1.1,5.3.3.
            else if (at >= padded - 8)
                byte = uint8_t((uint64_t(size) * 8) >> (8 * (padded - 1 - at)));
            words[j / 4] |= uint32_t(byte) << (24 - 8 * (j % 4));
        }
        for (unsigned j = 16; j < 64; ++j) {
            const auto x = words[j - 15], y = words[j - 2];
            words[j] = words[j - 16] + words[j - 7]
                + (rotate(x, 7) ^ rotate(x, 18) ^ (x >> 3))
                + (rotate(y, 17) ^ rotate(y, 19) ^ (y >> 10));
        }
        uint32_t work[8];
        for (unsigned j = 0; j < 8; ++j) work[j] = state[j];
        for (unsigned j = 0; j < 64; ++j) {
            const auto a = work[0], b = work[1], c = work[2];
            const auto e = work[4], f = work[5], g = work[6];
            const auto first = work[7] + (rotate(e, 6) ^ rotate(e, 11) ^ rotate(e, 25))
                + ((e & f) ^ (~e & g)) + rounds[j] + words[j];
            const auto second = (rotate(a, 2) ^ rotate(a, 13) ^ rotate(a, 22))
                + ((a & b) ^ (a & c) ^ (b & c));
            for (unsigned k = 7; k; --k) work[k] = work[k - 1];
            work[4] += first;
            work[0] = first + second;
        }
        for (unsigned j = 0; j < 8; ++j) state[j] += work[j];
    }
    Digest out{};
    for (unsigned j = 0; j < out.size(); ++j) out[j] = uint8_t(state[j / 4] >> (24 - 8 * (j % 4)));
    return out;
}
}
