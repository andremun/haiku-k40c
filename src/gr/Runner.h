// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "gr/Program.h"
namespace k40::gr {
// Mechanics only. The native port routes every access through the resident
// write policy; this class holds no authority of its own.
class Port {
public:
    virtual ~Port()=default;
    virtual bool read32(uint32_t addr,uint32_t& value)=0;
    virtual bool write32(uint32_t addr,uint32_t value)=0;
    virtual bool now(uint64_t& microseconds)=0;
    virtual bool delay(uint32_t microseconds)=0;
    virtual bool hook(uint32_t number)=0;
};
enum class Error:uint8_t {None,Read,Write,Expect,Poll,Idle,Clock,Delay,Hook,Program,Order};
struct Failure {Error error=Error::None;uint32_t index=0,addr=0,value=0,expected=0;};
// Runs one stage, op by op, and stops at the first failure. No retry, no
// rollback: after a failure the caller runs its own teardown.
class Runner {
public:
    explicit Runner(Port& port):port_(port){}
    void input(Input which,uint64_t bytes){slots_[which]=bytes;}
    bool run(const Stage& stage);
    bool failed() const{return failure_.error!=Error::None;}
    const Failure& failure() const{return failure_;}
    uint64_t slot(unsigned index) const{return index<maxSlots?slots_[index]:0;}
    uint32_t reads() const{return reads_;}
    uint32_t writes() const{return writes_;}
    uint32_t done() const{return done_;}
    // The value of one patch-list entry with the current inputs.
    uint32_t patchValue(const Patch& patch) const;
private:
    bool fail(Error,uint32_t index,uint32_t addr=0,uint32_t value=0,uint32_t expected=0);
    bool read(uint32_t index,uint32_t addr,uint32_t& value);
    bool write(uint32_t index,uint32_t addr,uint32_t value);
    bool poll(uint32_t index,const Op&);
    bool waitIdle(uint32_t index);
    Port& port_;uint64_t slots_[maxSlots]{};Failure failure_{};
    uint32_t reads_=0,writes_=0,done_=0;
};
}
