/* Copyright 2026 Mario Andrés Muñoz.
 * Distributed under the terms of the MIT License. */
#include "HaikuBackend.h"
#include <stdio.h>
#include <string.h>
static unsigned checks,failed,deleted,put_count,maps,creates;
static int module_ok=1,map_ok=1,create_ok=1,memory_map_ok=1,short_map=0,delete_ok=1,put_ok=1;
static uint32 scratch[B_PAGE_SIZE/4];static uint64 mapped_physical;
static uint64 allocated_physical=0x12345000;
static uint32 expected_lock=B_CONTIGUOUS;
#define CHECK(c) do{++checks;if(!(c)){++failed;printf("FAIL line %d: %s\n",__LINE__,#c);}}while(0)
status_t get_module(const char* name,module_info** out){(void)name;if(!module_ok)return B_ERROR;*out=(module_info*)scratch;return B_OK;}
status_t put_module(const char* name){(void)name;++put_count;return put_ok?B_OK:B_ERROR;}
area_id map_physical_memory(const char* name,phys_addr_t physical,size_t bytes,uint32 mode,uint32 protection,void** out){
 (void)name;(void)mode;++maps;CHECK(bytes==B_PAGE_SIZE && protection==B_KERNEL_READ_AREA);mapped_physical=physical;
 if(!map_ok)return B_ERROR;
 *out=scratch;return 3;
}
status_t delete_area(area_id area){CHECK(area>=0);++deleted;return delete_ok?B_OK:B_ERROR;}
area_id create_area(const char* name,void** address,uint32 mode,size_t bytes,uint32 lock,uint32 protection){
 (void)name;(void)mode;(void)protection;++creates;CHECK(bytes==B_PAGE_SIZE && lock==expected_lock);
 if(!create_ok)return B_ERROR;
 *address=scratch;return 4;
}
int32 get_memory_map(const void* address,size_t bytes,physical_entry* entry,int32 count){
 CHECK(address==scratch&&count==1);if(!memory_map_ok)return B_ERROR;
 entry->address=allocated_physical;entry->size=short_map?bytes-1:bytes;return B_OK;
}
int main(void){
 k40_os os;module_ok=0;CHECK(k40_os_init(&os)==B_ERROR);CHECK(os.pci==NULL&&os.mapping==-1);module_ok=1;
 CHECK(k40_os_init(&os)==B_OK);pci_info info;memset(&info,0,sizeof(info));
 info.u.h0.base_registers_pci[1]=0xe0000000;info.u.h0.base_registers_pci[2]=0x20f;
 info.u.h0.base_register_sizes[1]=B_PAGE_SIZE;info.u.h0.base_register_flags[1]=PCI_address_type_64;
 CHECK(k40_os_map_readonly(&os,&info,1,B_PAGE_SIZE)==B_OK);CHECK(mapped_physical==0x20fe0000000ULL);
 uint32 value=0;scratch[0]=0x1234;CHECK(k40_os_read32(&os,0,&value)==B_OK&&value==0x1234);
 CHECK(k40_os_read32(&os,4,&value)==B_BAD_VALUE);CHECK(k40_os_map_readonly(&os,&info,1,B_PAGE_SIZE)==B_BAD_VALUE);
 k40_os_close(&os);CHECK(deleted==1&&put_count==1);k40_os_close(&os);CHECK(deleted==1&&put_count==1);
 CHECK(k40_os_init(&os)==B_OK);info.u.h0.base_register_flags[1]=PCI_address_space;
 CHECK(k40_os_map_readonly(&os,&info,1,B_PAGE_SIZE)==B_BAD_VALUE&&maps==1);
 info.u.h0.base_register_flags[1]=PCI_address_type_64;map_ok=0;
 CHECK(k40_os_map_readonly(&os,&info,1,B_PAGE_SIZE)==B_ERROR&&os.mapping==-1);map_ok=1;k40_os_close(&os);
 k40_host_allocation allocation;CHECK(k40_os_allocate(1,&allocation)==B_OK&&allocation.bytes==B_PAGE_SIZE);
 CHECK(allocation.guest_physical==0x12345000);unsigned prior=deleted;k40_os_free(&allocation);CHECK(deleted==prior+1);
 k40_os_free(&allocation);CHECK(deleted==prior+1);memory_map_ok=0;
 CHECK(k40_os_allocate(1,&allocation)==B_ERROR&&allocation.area==-1);CHECK(deleted==prior+2);memory_map_ok=1;short_map=1;
 CHECK(k40_os_allocate(1,&allocation)==B_BAD_DATA&&allocation.area==-1);short_map=0;create_ok=0;
 CHECK(k40_os_allocate(1,&allocation)==B_ERROR&&allocation.area<0);create_ok=1;
 prior=creates;CHECK(k40_os_allocate(SIZE_MAX,&allocation)==B_BAD_VALUE&&creates==prior);
 CHECK(k40_os_init(&os)==B_OK);CHECK(k40_os_map_readonly(&os,&info,1,B_PAGE_SIZE)==B_OK);
 delete_ok=0;prior=put_count;CHECK(k40_os_close(&os)==B_ERROR&&os.mapping>=0&&os.pci!=NULL&&put_count==prior);
 delete_ok=1;CHECK(k40_os_close(&os)==B_OK&&os.mapping==-1&&os.pci==NULL);
 CHECK(k40_os_allocate(1,&allocation)==B_OK);delete_ok=0;CHECK(k40_os_free(&allocation)==B_ERROR&&allocation.area>=0);
 delete_ok=1;CHECK(k40_os_free(&allocation)==B_OK&&allocation.area==-1);
 memory_map_ok=0;delete_ok=0;CHECK(k40_os_allocate(1,&allocation)==B_ERROR&&allocation.area>=0);
 memory_map_ok=1;delete_ok=1;CHECK(k40_os_free(&allocation)==B_OK);
 CHECK(k40_os_init(&os)==B_OK);put_ok=0;CHECK(k40_os_close(&os)==B_ERROR&&os.pci!=NULL);
 put_ok=1;CHECK(k40_os_close(&os)==B_OK&&os.pci==NULL);
 expected_lock=B_32_BIT_CONTIGUOUS;
 CHECK(k40_os_allocate_dma32(B_PAGE_SIZE,&allocation)==B_OK);
 CHECK(allocation.guest_physical==allocated_physical&&allocation.bytes==B_PAGE_SIZE);
 CHECK(k40_os_free(&allocation)==B_OK);
 allocated_physical=(uint64)UINT32_MAX+1-B_PAGE_SIZE;
 CHECK(k40_os_allocate_dma32(B_PAGE_SIZE,&allocation)==B_OK);
 CHECK(k40_os_free(&allocation)==B_OK);
 allocated_physical=(uint64)UINT32_MAX+1;
 CHECK(k40_os_allocate_dma32(B_PAGE_SIZE,&allocation)==B_BAD_DATA&&allocation.area==-1);
 allocated_physical=0x12345001;
 CHECK(k40_os_allocate_dma32(B_PAGE_SIZE,&allocation)==B_BAD_DATA&&allocation.area==-1);
 prior=creates;
 CHECK(k40_os_allocate_dma32((size_t)UINT32_MAX+1+B_PAGE_SIZE,&allocation)==B_BAD_VALUE&&creates==prior);
 expected_lock=B_CONTIGUOUS;allocated_physical=0x12345000;
 printf("Haiku backend host fault injection: %u checks, %u failures; NOT native ABI evidence\n",checks,failed);
 return failed?1:0;
}
