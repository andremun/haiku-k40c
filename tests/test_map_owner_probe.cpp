// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Native probe lifecycle exercised with host OS spies; not module-load evidence.
#include "os/HaikuMemory.h"
#include "os/HaikuOwnerModule.h"
#include <cstdarg>
#include <cstdio>
#include <map>
#include <string>
#include <vector>
extern "C" { extern module_info* modules[]; status_t init_driver(void); void uninit_driver(void); }
static unsigned checks = 0, failures = 0, frees = 0;
static std::map<int,std::vector<uint8_t>> areas;
static int nextArea = 1;
static std::string logText;
#define CHECK(c) do { ++checks; if (!(c)) { ++failures; std::printf("FAIL %d: %s\n",__LINE__,#c); } } while (0)
void k40_probe_log(const char* format, ...)
{
    char text[512]; va_list args; va_start(args,format);
    std::vsnprintf(text,sizeof(text),format,args); va_end(args); logText += text;
}
extern "C" status_t get_module(const char*, module_info** info) { *info = modules[0]; return B_OK; }
extern "C" status_t put_module(const char*) { return B_OK; }
extern "C" status_t k40_os_allocate_dma32(size_t bytes, k40_host_allocation* out)
{
    const auto id = nextArea++; areas[id].resize(bytes);
    *out = {id,areas[id].data(),bytes,0x10001000}; return B_OK;
}
extern "C" status_t k40_os_free(k40_host_allocation* allocation)
{
    CHECK(areas.erase(allocation->area) == 1); ++frees;
    *allocation = {-1,nullptr,0,0}; return B_OK;
}
int main()
{
    CHECK(modules[0]->std_ops(B_MODULE_INIT)==B_OK);
    auto* api=reinterpret_cast<k40_owner_module*>(modules[0]);
    auto read=api->read;
    api->read=[](uint64,uint64,uint64,void*,size_t)->int32{return K40_OWNER_IO;};
    CHECK(init_driver()==B_ERROR);
    CHECK(logText.find("FAIL D0 owner preparation")!=std::string::npos);
    CHECK(areas.empty() && frees==1);
    api->read=read;logText.clear();
    CHECK(init_driver()==B_OK);uninit_driver();
    CHECK(logText.find("phase=1 lease=2 token=2 gpa=0x10001000 bytes=4096 quarantine=0 visibility=DENIED")!=std::string::npos);
    CHECK(logText.find("phase=1 detached lease=2 token=2 retained")!=std::string::npos);
    CHECK(areas.size()==1 && frees==1);
    CHECK(init_driver()==B_OK);uninit_driver();
    CHECK(logText.find("phase=2 lease=3 token=2 gpa=0x10001000 bytes=4096 quarantine=1 visibility=DENIED")!=std::string::npos);
    CHECK(logText.find("phase=2 detached lease=3 token=2 retained")!=std::string::npos);
    CHECK(logText.find("PASS retained host extent only; DMA denied")!=std::string::npos);
    CHECK(logText.find("FAIL")==std::string::npos && areas.size()==1 && frees==1);
    CHECK(init_driver()==B_OK);uninit_driver();
    CHECK(logText.find("phase=2 lease=4 token=2")!=std::string::npos);
    std::printf("D0 memory probe host lifecycle: %u checks, %u failures; no device evidence\n",checks,failures);
    return failures?1:0;
}
