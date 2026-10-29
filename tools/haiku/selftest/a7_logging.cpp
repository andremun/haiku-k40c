// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// CARDLESS_A7_LOGGING_ONLY: no PCI, MMIO, module API, grant or DMA operations.
#include "a7/PostDiagnostics.h"
#include "a7_logging_input.h"
#include <Drivers.h>
#include <KernelExport.h>
namespace {
k40::a7::PostDiagnostics diagnostics;
struct Sink {
    void log(const char* name,uint64_t a,uint64_t b=0) {
        dprintf("k40_a7: %s a=0x%llx b=0x%llx\n",name,(unsigned long long)a,(unsigned long long)b);
    }
} sink;
const char* devices[]={nullptr};
}
extern "C" {
int32 api_version=B_CUR_DRIVER_API_VERSION;
status_t init_hardware(){return B_OK;}
status_t init_driver() {
    dprintf("logging_probe: BEGIN CARDLESS_A7_LOGGING_ONLY\n");
    for(unsigned repeat=0;repeat<3;++repeat) {
        const auto live=system_time();
        for(const auto& e:loggingEntries)sink.log(e.active?"SCRIPT_ACTIVE":"SCRIPT_SKIPPED",e.pc,e.op);
        const auto liveUs=system_time()-live;
        const auto buffered=system_time();diagnostics.begin(buffered);
        for(const auto& e:loggingEntries)diagnostics.record(e.active?"SCRIPT_ACTIVE":"SCRIPT_SKIPPED",e.pc,e.op,system_time());
        const auto bufferedUs=system_time()-buffered;
        diagnostics.finishPost(system_time());const auto drain=system_time();diagnostics.flush(sink);
        const auto drainUs=system_time()-drain;
        if(!diagnostics.healthy()){dprintf("k40_os: FAIL logging capacity\n");return B_ERROR;}
        dprintf("logging_probe: SAMPLE index=%u live_us=%llu buffered_us=%llu drain_us=%llu entries=%u\n",
            repeat,(unsigned long long)liveUs,(unsigned long long)bufferedUs,(unsigned long long)drainUs,
            unsigned(sizeof(loggingEntries)/sizeof(loggingEntries[0])));
    }
    dprintf("logging_probe: END\nk40_os: PASS native logging only; no hardware\n");return B_OK;
}
void uninit_driver(){}
const char** publish_devices(){return devices;}
device_hooks* find_device(const char*){return nullptr;}
}
