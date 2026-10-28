// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "a7/NativePlatform.h"
static unsigned checks=0,maps=0,reservations=0,frees=0,allocations=0;
static bool duplicate=false,reserveFail=false,partial=false;
static std::vector<uint8_t> aperture(0x1000000),page(8192,0xa5);
#define REQUIRE(x) do{++checks;if(!(x)){std::fprintf(stderr,"line %u: %s\n",__LINE__,#x);std::exit(1);}}while(0)
static status_t nth(int32 index,pci_info* info)
{
 if(index>(duplicate?1:0))return B_ERROR;
 *info={};info->vendor_id=0x10de;info->device_id=0x1024;
 info->u.h0.base_registers_pci[0]=0x10000000;info->u.h0.base_register_sizes[0]=aperture.size();return B_OK;
}
static uint32 config(uint8,uint8,uint8,uint8 offset,uint8 bytes){REQUIRE(offset==4 && bytes==2);return 7;}
static status_t reserve(uint8,uint8,uint8,const char* name,void* owner)
{++reservations;REQUIRE(std::strcmp(name,"k40_a7_stage")==0 && owner);return reserveFail?B_ERROR:B_OK;}
static pci_module_info pci={nth,config,reserve};
extern "C" status_t get_module(const char* name,module_info** out){REQUIRE(std::strcmp(name,B_PCI_MODULE_NAME)==0);*out=reinterpret_cast<module_info*>(&pci);return B_OK;}
extern "C" status_t put_module(const char*){REQUIRE(false);return B_ERROR;}
area_id map_physical_memory(const char*,phys_addr_t physical,size_t bytes,uint32,uint32 flags,void** out)
{REQUIRE(reservations && !reserveFail && physical==0x10000000 && bytes==aperture.size());REQUIRE(flags==(B_KERNEL_READ_AREA|B_KERNEL_WRITE_AREA));++maps;*out=aperture.data();return 1;}
bigtime_t system_time(){return 1000;}
status_t snooze(bigtime_t){return B_OK;}
void spin(bigtime_t){}
int k40_a7_mock_log(const char*,...){return 0;}
extern "C" status_t k40_os_allocate_dma32(size_t bytes,k40_host_allocation* out)
{++allocations;REQUIRE(bytes==8191);*out={1,page.data(),page.size(),0x400001};return partial?B_ERROR:B_OK;}
extern "C" status_t k40_os_free(k40_host_allocation*){++frees;REQUIRE(false);return B_ERROR;}
int main()
{
 using namespace k40::a7;
 {NativePlatform native;duplicate=true;REQUIRE(!native.initialize());REQUIRE(maps==0 && reservations==0);}
 duplicate=false;reserveFail=true;
 {NativePlatform native;REQUIRE(!native.initialize());REQUIRE(maps==0 && reservations==1);}
 reserveFail=false;
 {NativePlatform native;REQUIRE(native.initialize());REQUIRE(!native.initialize());uint16_t command=0;REQUIRE(native.pciCommand(command) && command==7);
 uint32_t value=0;uint8_t byte=0;REQUIRE(native.read32(0,value));REQUIRE(!native.read32(1,value));REQUIRE(!native.read32(aperture.size(),value));
 REQUIRE(!native.write32(0,0xdeadbeef));REQUIRE(!native.write8(0,1));REQUIRE(native.read8(0,byte) && byte==0);REQUIRE(!native.read8(aperture.size(),byte));REQUIRE(!native.delayUs(1000001));}
 {NativeStorage storage;k40::memory::ArmAllocation owned;REQUIRE(storage.reserveZeroed(owned));REQUIRE(owned.token && owned.bytes==4096 && owned.physical.value==0x401000);
 for(unsigned i=4095;i<8191;++i)REQUIRE(page[i]==0);
 REQUIRE(page[4094]==0xa5 && page[8191]==0xa5);storage.retain(owned);REQUIRE(!storage.reserveZeroed(owned));REQUIRE(frees==0 && allocations==1);}
 partial=true;
 {NativeStorage storage;k40::memory::ArmAllocation owned;REQUIRE(!storage.reserveZeroed(owned));REQUIRE(owned.token);storage.retain(owned);}
 REQUIRE(frees==0 && allocations==2);std::printf("A7 native boundary: %u checks pass (host mocks only)\n",checks);
}
