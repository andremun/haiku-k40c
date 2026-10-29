// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memstage/Port.h"
namespace k40::memstage {
struct Routing {
    uint32_t type=0,instance=0,address=0,fault=0,runlist=0,engine=0;
    bool hasFault=false,hasRunlist=false,hasEngine=false;
};
class Faults {
public:
    Faults(ReadPort& port,Journal& journal,uint64_t epoch):port_(port),journal_(journal),epoch_(epoch){}
    bool capture(Phase phase,uint64_t epoch);
    bool healthy() const{return error_==Error::None && !journal_.overflow();}
    bool ready() const{return healthy() && next_>=2;}
    Error error() const{return error_;}
    bool completed(Phase phase) const{return healthy() && next_==unsigned(phase)+1;}
    unsigned routeCount() const{return routes_;}
    bool route(unsigned i,Routing& r) const{if(i>=routes_)return false;r=routing_[i];return true;}
private:
    bool read(uint32_t offset,uint32_t& value);
    bool clock();
    bool stop(Error);
    bool topology();
    bool details(uint32_t mask,uint32_t base,unsigned count,unsigned firstBit);
    ReadPort& port_;Journal& journal_;uint64_t epoch_=0,start_=0,last_=0;
    Phase phase_=Phase::Reset;Error error_=Error::None;unsigned next_=0,routes_=0;
    Routing routing_[64]{}; // top/gk104.c:37 fixed descriptor scan bound.
};
}
