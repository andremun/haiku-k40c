// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include <cstdint>
namespace k40::a7 {
// no source: software storage bounds, not hardware constants; resident owner storage.
class PostDiagnostics {
public:
    static constexpr unsigned capacity=2048, pollCapacity=16; // no source: software record/table bounds.
    void begin(uint64_t now) {
        count_=postEvents_=polls_=delays_=mmios_=0;wallUs_=requestedUs_=delayUs_=mmioUs_=maxMmioUs_=0;
        overflow_=clockFault_=false;started_=last_=now;recording_=measuring_=true;
    }
    bool healthy() const {return !overflow_ && !clockFault_;}
    bool recording() const {return recording_;}
    bool measuring() const {return measuring_;}
    void record(const char* name,uint64_t a,uint64_t b,uint64_t now) {
        if(!recording_)return;
        if(now<last_){clockFault_=true;return;}last_=now;
        if(count_==capacity){overflow_=true;return;}
        events_[count_++]={name,a,b,now-started_};
    }
    void poll(uint32_t pc,uint8_t index,uint32_t value,bool met,uint64_t now) {
        if(!measuring_)return;
        if(now<last_){clockFault_=true;return;}last_=now;
        unsigned at=0;
        while(at<polls_ && (pollsData_[at].pc!=pc || pollsData_[at].index!=index))++at;
        if(at==polls_) {
            if(polls_==pollCapacity){overflow_=true;return;}
            pollsData_[polls_++]={pc,index,0,0,false,now-started_,0};
        }
        auto& p=pollsData_[at];++p.samples;p.value=value;p.met=met;p.last=now-started_;
    }
    void delay(uint64_t requested,uint64_t before,uint64_t after) {
        if(!measuring_)return;
        if(after<before){clockFault_=true;return;}
        ++delays_;requestedUs_+=requested;delayUs_+=after-before;
    }
    void mmio(uint64_t before,uint64_t after) {
        if(!measuring_)return;
        if(after<before){clockFault_=true;return;}
        ++mmios_;const auto elapsed=after-before;mmioUs_+=elapsed;
        if(elapsed>maxMmioUs_)maxMmioUs_=elapsed;
    }
    void finishPost(uint64_t now) {
        if(now<started_)clockFault_=true;else wallUs_=now-started_;
        postEvents_=count_;measuring_=false;
    }
    template<class Sink> void flush(Sink& sink) {
        recording_=false;
        sink.log("TRACE_BEGIN",count_,capacity);
        for(unsigned i=0;i<postEvents_;++i) {
            const auto& e=events_[i];sink.log(e.name,e.a,e.b);
            sink.log("TRACE_AT",i,e.us);
        }
        for(unsigned i=0;i<polls_;++i) {
            const auto& p=pollsData_[i];sink.log("POLL_COUNT",p.pc,p.samples);
            sink.log("POLL_LAST",p.pc,p.value);
            sink.log("POLL_STATE",p.index,p.met);
            sink.log("POLL_FIRST_US",p.pc,p.first);sink.log("POLL_LAST_US",p.pc,p.last);
        }
        sink.log("POST_WALL_US",wallUs_,0);
        sink.log("POST_DELAY_US",requestedUs_,delayUs_);
        sink.log("POST_DELAY_COUNT",delays_,0);
        sink.log("POST_MMIO_US",mmioUs_,maxMmioUs_);
        sink.log("POST_MMIO_COUNT",mmios_,0);
        sink.log("TRACE_END",overflow_,clockFault_);
        // Lifecycle records follow the complete script/timing dump. In particular,
        // POST_RESULT cannot hide pending diagnostics if it reports failure.
        for(unsigned i=postEvents_;i<count_;++i) {
            const auto& e=events_[i];sink.log(e.name,e.a,e.b);
            sink.log("TRACE_AT",i,e.us);
        }
    }
private:
    struct Event {const char* name;uint64_t a,b,us;};
    struct Poll {uint32_t pc,index,samples,value;bool met;uint64_t first,last;};
    Event events_[capacity]{};
    Poll pollsData_[pollCapacity]{};
    uint64_t started_=0,last_=0,wallUs_=0,requestedUs_=0,delayUs_=0,mmioUs_=0,maxMmioUs_=0;
    unsigned count_=0,postEvents_=0,polls_=0,delays_=0,mmios_=0;
    bool recording_=false,measuring_=false,overflow_=false,clockFault_=false;
};
}
