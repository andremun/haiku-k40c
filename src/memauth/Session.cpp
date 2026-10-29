// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memauth/Session.h"
#include <cstring>
extern "C" int ed25519_verify(const unsigned char*,const unsigned char*,size_t,const unsigned char*);
namespace k40::memauth {
namespace {
constexpr uint8_t magic[16]={'K','4','0','M','E','M','R','E','Q',1,0,0,0,0,0,0}; // no source: memory role/version framing.
constexpr uint8_t grantMagic[16]={'K','4','0','M','E','M','R','U','N',1,0,0,0,0,0,0}; // no source: separate signed role/version framing.
void put(uint8_t* out,uint64_t value){for(unsigned i=0;i<8;++i)out[i]=uint8_t(value>>(i*8));}
bool nonzero(const uint8_t* data,size_t size){uint8_t any=0;for(size_t i=0;i<size;++i)any|=data[i];return any!=0;}
bool canonical(const uint8_t* scalar)
{
    constexpr uint8_t order[32]={0xed,0xd3,0xf5,0x5c,0x1a,0x63,0x12,0x58,0xd6,0x9c,0xf7,0xa2,0xde,0xf9,0xde,0x14, // no source: RFC 8032 subgroup order, signature canonicality.
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0x10}; // no source: RFC 8032 subgroup order continuation.
    for(int i=31;i>=0;--i){if(scalar[i]<order[i])return true;if(scalar[i]>order[i])return false;}return false;
}
}
void Session::request(uint8_t* out) const
{
    std::memset(out,0,requestBytes);std::memcpy(out,magic,16);
    std::memcpy(out+16,binding_.nonce,32);std::memcpy(out+48,binding_.plan,32);std::memcpy(out+80,binding_.challenge,16);
    const uint64_t words[]={binding_.epoch,binding_.owner,binding_.bar0,binding_.bar0Bytes,
        binding_.bar1,binding_.bar1Bytes,binding_.vram,binding_.begin,binding_.end,8192}; // no source: fixed read-only two-page BAR1 software scope.
    for(unsigned i=0;i<10;++i)put(out+96+i*8,words[i]);
}
bool Session::prepare(uint8_t* out)
{
    if(!out || state_!=State::New || detached_)return false;
    state_=State::Failed;
    if(!binding_.epoch || !binding_.owner || !nonzero(binding_.key,32) || !nonzero(binding_.nonce,32) || !nonzero(binding_.plan,32)
        || !nonzero(binding_.challenge,16) || !binding_.bar0 || !binding_.bar1 || binding_.bar0==binding_.bar1
        || binding_.bar0Bytes<8388608 || binding_.bar1Bytes<8192 || binding_.begin>=binding_.end
        || binding_.end>=binding_.vram)return false; // no source: finite software resource contract, not device discovery.
    request(out);state_=State::Prepared;return true;
}
bool Session::accept(const uint8_t* grant,size_t size) const
{
    if(!grant || size!=grantBytes || std::memcmp(grant,grantMagic,16) || !nonzero(grant+192,32)
        || !canonical(grant+288))return false;
    uint8_t expected[requestBytes];request(expected);
    if(std::memcmp(grant+16,expected+16,176) || std::memcmp(grant+224,expected+224,32))return false;
    return ed25519_verify(grant+256,grant,256,binding_.key)!=0;
}
bool Session::submit(const uint8_t* grant,size_t size)
{
    if(state_!=State::Prepared || detached_)return false;
    state_=State::Failed;
    if(!accept(grant,size))return false;
    state_=State::Executing;
    const bool passed=runtime_.execute();state_=passed?State::Passed:State::Failed;return passed;
}
bool Session::detach()
{
    if(detached_ || state_==State::Executing)return false;
    detached_=true;
    if(state_!=State::Passed)state_=State::Failed;
    return true; // Retention only. No rearm, free or quiescence claim.
}
}
