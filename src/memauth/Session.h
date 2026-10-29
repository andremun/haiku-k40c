// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include <cstddef>
#include <cstdint>
namespace k40::memauth {
constexpr size_t requestBytes=256,grantBytes=320; // no source: distinct software memory-phase frames.
struct Binding {
    uint8_t key[32]{},nonce[32]{},plan[32]{},challenge[16]{};
    uint64_t epoch=0,owner=0,bar0=0,bar0Bytes=0,bar1=0,bar1Bytes=0,vram=0,begin=0,end=0;
};
// Supplied by fixed resident code at construction, never by a guest client ABI.
class Runtime {
public:
    virtual ~Runtime()=default;
    virtual bool execute()=0; // Revoke native gate before returning, including failure.
};
enum class State:uint8_t {New,Prepared,Executing,Passed,Failed};
class Session {
public:
    Session(const Binding& binding,Runtime& runtime):binding_(binding),runtime_(runtime){}
    bool prepare(uint8_t out[requestBytes]);
    bool submit(const uint8_t*,size_t);
    bool detach();
    State state() const{return state_;}
private:
    void request(uint8_t*) const;
    bool accept(const uint8_t*,size_t) const;
    Binding binding_;Runtime& runtime_;State state_=State::New;
    bool detached_=false;
};
}
