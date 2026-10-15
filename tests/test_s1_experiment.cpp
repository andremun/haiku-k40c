// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#include "runtime/S1Experiment.h"
#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>
using namespace k40::runtime;
static unsigned checks = 0, failed = 0;
#define CHECK(c) do { ++checks; if (!(c)) { ++failed; std::printf("FAIL line %d: %s\n", __LINE__, #c); } } while (0)
struct Fake : Backend {
    uint64_t time = 0, tick = 1, publicationDelay = 0;
    unsigned reads = 0, failRead = 0;
    bool prepareOk = true, publishOk = true, submitOk = true;
    bool quiesceOk = true, releaseOk = true, submitted = false, stopped = false;
    bool stall = false, baselineFault = false, pollFault = false, finalFault = false;
    bool backwards = false, jump = false, corruptPut = false;
    Snapshot initial{};
    std::vector<std::string> events;
    uint64_t nowUs() override {
        if (backwards && submitted) return 0;
        time += tick;
        return time;
    }
    bool prepare() override { events.push_back("prepare"); return prepareOk; }
    bool snapshot(Snapshot& s) override {
        events.push_back(stopped ? "final" : "snapshot");
        if (++reads == failRead) return false;
        s = initial;
        if (stopped) { s.fault = finalFault; return true; }
        if (!submitted) { s.fault = baselineFault; return true; }
        s.put = corruptPut ? initial.put : (initial.put + 1) % 4;
        s.get = stall ? initial.get : (jump ? 2 : s.put);
        s.fault = pollFault;
        return true;
    }
    bool publishNop(uint32_t slot, uint32_t put) override {
        events.push_back("publish");
        CHECK(slot == initial.put && put == (slot + 1) % 4);
        time += publicationDelay;
        return publishOk;
    }
    bool setPut(uint32_t) override { events.push_back("put"); submitted = true; return submitOk; }
    void pause() override { events.push_back("pause"); }
    bool quiesce() override { events.push_back("quiesce"); stopped = true; return quiesceOk; }
    bool release() override { events.push_back("release"); return releaseOk; }
    bool saw(const char* s) { return std::find(events.begin(), events.end(), s) != events.end(); }
};
static Limits limits{4, 100, 5};
int main() {
    {
        Fake b; auto r = runS1(b, limits);
        CHECK(r.success() && r.initialGet == 0 && r.targetPut == 1);
        CHECK(b.events == std::vector<std::string>({"prepare", "snapshot", "publish", "put", "snapshot", "quiesce", "final", "release"}));
    }
    { Fake b; b.initial = {3,3,false}; auto r = runS1(b, limits); CHECK(r.success() && r.targetPut == 0); }
    for (auto invalid : {Limits{1,100,5}, Limits{3,100,5}, Limits{4,0,5}, Limits{4,100,0}}) {
        Fake b; CHECK(runS1(b, invalid).primary == Error::InvalidConfig); CHECK(b.events.empty());
    }
    { Fake b; b.prepareOk = false; auto r = runS1(b, limits); CHECK(r.primary == Error::Prepare && r.released); CHECK(!b.saw("put")); }
    { Fake b; b.initial.put = 1; CHECK(runS1(b, limits).primary == Error::Baseline); CHECK(!b.saw("publish")); }
    { Fake b; b.initial = {4,4,false}; CHECK(runS1(b, limits).primary == Error::Baseline); }
    { Fake b; b.baselineFault = true; CHECK(runS1(b, limits).primary == Error::Fault); CHECK(!b.saw("put")); }
    { Fake b; b.publishOk = false; CHECK(runS1(b, limits).primary == Error::Publish); CHECK(!b.saw("put")); }
    { Fake b; b.publicationDelay = 100; CHECK(runS1(b, limits).primary == Error::Timeout); CHECK(!b.saw("put")); }
    { Fake b; b.submitOk = false; auto r = runS1(b, limits); CHECK(r.primary == Error::Submit && r.quiesced && r.released); }
    { Fake b; b.pollFault = true; auto r = runS1(b, limits); CHECK(r.primary == Error::Fault && !r.progressed); }
    { Fake b; b.jump = true; CHECK(runS1(b, limits).primary == Error::UnexpectedGet); }
    { Fake b; b.corruptPut = true; CHECK(runS1(b, limits).primary == Error::UnexpectedGet); }
    { Fake b; b.stall = true; auto r = runS1(b, limits); CHECK(r.primary == Error::Timeout && !r.progressed && r.polls == 5); }
    { Fake b; b.stall = true; b.tick = 0; auto r = runS1(b, limits); CHECK(r.primary == Error::Timeout && r.polls == 5); }
    { Fake b; b.tick = 30; auto r = runS1(b, limits); CHECK(r.primary == Error::Timeout && !r.progressed); }
    { Fake b; b.backwards = true; CHECK(runS1(b, limits).primary == Error::Clock); }
    { Fake b; b.time = UINT64_MAX - 100; auto r = runS1(b, limits); CHECK(r.success()); }
    for (unsigned read : {1,2}) {
        Fake b; b.failRead = read; auto r = runS1(b, limits); CHECK(r.primary == Error::Observe && !r.success());
    }
    { Fake b; b.quiesceOk = false; auto r = runS1(b, limits); CHECK(r.progressed && !r.success() && !r.released && r.cleanup == Error::Quiesce); CHECK(!b.saw("release")); }
    { Fake b; b.submitOk = false; b.quiesceOk = false; auto r = runS1(b, limits); CHECK(r.primary == Error::Submit && r.cleanup == Error::Quiesce && !r.released); }
    { Fake b; b.failRead = 3; auto r = runS1(b, limits); CHECK(r.progressed && !r.success() && r.cleanup == Error::Observe && r.released); }
    { Fake b; b.finalFault = true; auto r = runS1(b, limits); CHECK(r.progressed && !r.success() && r.cleanup == Error::Fault); }
    { Fake b; b.releaseOk = false; auto r = runS1(b, limits); CHECK(r.progressed && !r.success() && r.cleanup == Error::Release && !r.released); }
    std::printf("S1 controller: %u checks, %u failures (HOST_ONLY)\n", checks, failed);
    return failed ? 1 : 0;
}
