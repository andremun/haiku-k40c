// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include <cstdint>
namespace k40::memstage {
// This interface supplies mechanics only, never stage authority. The physical
// implementation must keep its write gate private to the resident controller.
class ReadPort {
public:
    virtual ~ReadPort()=default;
    virtual bool read32(uint32_t offset,uint32_t& value)=0;
    virtual bool now(uint64_t& microseconds)=0;
};
enum class Phase:uint8_t {Reset,Post,Physical,Tables,Mapped,Remapped,Restored,Disabled,
    ChannelBase,ChannelMemory,ChannelBar,ChannelFifo,ChannelBound,ChannelSubmit,ChannelClosed};
enum class Error:uint8_t {None,Order,Read,Dirty,Clock,Budget,Overflow,Topology,Write,Profile,Bounds,Compare,Flush,Invalidate,Authority,
    Routing,Runlist,Preempt};
enum class Operation:uint8_t {Read,Write,Poll,BulkWrite,BulkRead,Patch,Failure,Witness};
struct Event {
    Phase phase=Phase::Reset;Error error=Error::None;
    uint32_t offset=0;uint64_t value=0;uint32_t polls=0;uint64_t elapsed=0;
    Operation operation=Operation::Read;uint8_t role=0,detail=0;
};
class Journal {
public:
    static constexpr unsigned capacity=4096; // no source: resident diagnostic capacity.
    bool append(const Event& event){if(count_==capacity){overflow_=true;return false;}events_[count_++]=event;return true;}
    const Event* at(unsigned index) const {return index<count_?events_+index:nullptr;}
    unsigned count() const{return count_;}
    bool overflow() const{return overflow_;}
private:
    Event events_[capacity]{};unsigned count_=0;bool overflow_=false;
};
}
