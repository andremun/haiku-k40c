// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "a7/ArmAuthority.h"
#include <cstring>
extern "C" int ed25519_verify(const unsigned char*,const unsigned char*,size_t,const unsigned char*);
namespace k40::a7 {
namespace {
constexpr uint8_t requestMagic[16]={'K','4','0','A','7','R','E','Q',1,0,0,0,0,0,0,0}; // no source: software request framing magic and version.
constexpr uint8_t grantMagic[16]={'K','4','0','A','7','A','R','M',1,0,0,0,0,0,0,0}; // no source: software grant framing magic and version.
void put(uint8_t* out,uint64_t value) {for(unsigned i=0;i<8;++i)out[i]=uint8_t(value>>(8*i));}
uint64_t get(const uint8_t* in) {uint64_t value=0;for(unsigned i=0;i<8;++i)value|=uint64_t(in[i])<<(8*i);return value;}
bool canonicalScalar(const uint8_t* scalar)
{
    // Ed25519 subgroup order, RFC 8032 sections 5.1 and 5.1.7. Public data only.
    constexpr uint8_t order[32]={0xed,0xd3,0xf5,0x5c,0x1a,0x63,0x12,0x58,0xd6,0x9c,0xf7,0xa2,0xde,0xf9,0xde,0x14, // no source: RFC 8032 sections 5.1,5.1.7 subgroup order for signature verification.
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0x10}; // no source: continuation of the RFC 8032 subgroup order, not a hardware constant.
    for(int i=31;i>=0;--i) {if(scalar[i]<order[i])return true;if(scalar[i]>order[i])return false;}
    return false;
}
}
ArmAuthority::ArmAuthority(const uint8_t key[32],const uint8_t nonce[32],const uint8_t challenge[16])
{std::memcpy(key_,key,32);std::memcpy(nonce_,nonce,32);std::memcpy(challenge_,challenge,16);}
void ArmAuthority::request(const memory::ArmedReference& page,uint8_t out[requestBytes]) const
{
    std::memset(out,0,requestBytes);std::memcpy(out,requestMagic,16);std::memcpy(out+16,nonce_,32);
    const auto owned=page.allocation();put(out+48,owned.token);put(out+56,owned.physical.value);put(out+64,owned.bytes);std::memcpy(out+112,challenge_,16);
}
bool ArmAuthority::accept(memory::ArmedReference& page,const uint8_t* grant,size_t size) const
{
    if(!grant || size!=grantBytes || page.state()!=memory::ArmedReference::State::Prepared)return false;
    if(std::memcmp(grant,grantMagic,16) || std::memcmp(grant+16,nonce_,32))return false;
    if(std::memcmp(grant+112,challenge_,16))return false;
    uint8_t proof=0;for(unsigned i=80;i<112;++i)proof|=grant[i];
    if(!proof || !canonicalScalar(grant+160) || !ed25519_verify(grant+128,grant,128,key_))return false;
    const auto owned=page.allocation();
    if(get(grant+48)!=owned.token || get(grant+56)!=owned.physical.value || get(grant+64)!=owned.bytes)return false;
    return page.bind(memory::ArmGrant(owned.token,owned.physical,{get(grant+72)},owned.bytes));
}
}
