// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <Drivers.h>
#include "memnative/Module.h"
extern "C" status_t init_driver();
extern "C" void uninit_driver();
extern "C" device_hooks* find_device(const char*);
static unsigned checks=0,prepares=0,submits=0,detaches=0,modulePuts=0;
static bool copyFail=false,moduleFail=false;
#define REQUIRE(x) do{++checks;if(!(x)){std::fprintf(stderr,"line %u: %s\n",__LINE__,#x);std::exit(1);}}while(0)
static int prepare(uint64* lease,uint8* request){++prepares;if(prepares>1)return B_ENTRY_NOT_FOUND;*lease=1;std::memset(request,0x55,256);return B_OK;}
static int submit(uint64 lease,const uint8*,size_t bytes){++submits;REQUIRE(lease==1 && bytes==320);return B_OK;}
static int detach(uint64 lease){++detaches;REQUIRE(lease==1);return B_OK;}
static unsigned observations=0;
static int observe(){++observations;return B_OK;}
static k40_memory_module api={{K40_MEMORY_OWNER_NAME,B_KEEP_LOADED,nullptr},1,prepare,submit,detach,observe};
extern "C" status_t get_module(const char* name,module_info** out){REQUIRE(!std::strcmp(name,K40_MEMORY_OWNER_NAME));if(moduleFail)return B_ERROR;*out=&api.info;return B_OK;}
extern "C" status_t put_module(const char*){++modulePuts;return B_OK;}
status_t user_memcpy(void* out,const void* in,size_t bytes){if(copyFail)return B_BAD_ADDRESS;std::memcpy(out,in,bytes);return B_OK;}
int k40_a7_mock_log(const char*,...){return 0;}
int main()
{
 REQUIRE(init_driver()==B_OK);uninit_driver();REQUIRE(init_driver()==B_OK);uninit_driver();
 REQUIRE(observations==2 && prepares==0 && submits==0 && modulePuts==2);modulePuts=0;
 auto* hooks=find_device("misc/k40_mem_stage");REQUIRE(hooks && !find_device("misc/other"));void* cookie=nullptr;
 moduleFail=true;REQUIRE(hooks->open("misc/k40_mem_stage",0,&cookie)==B_ERROR && prepares==0 && modulePuts==0);moduleFail=false;
 REQUIRE(hooks->open("misc/k40_mem_stage",0,&cookie)==B_OK);void* other=nullptr;REQUIRE(hooks->open("misc/k40_mem_stage",0,&other)==B_BUSY);
 uint8 bytes[321]{};size_t size=1;REQUIRE(hooks->write(cookie,0,bytes,&size)==B_BAD_VALUE);
 size=255;REQUIRE(hooks->read(cookie,0,bytes,&size)==B_BAD_VALUE);copyFail=true;size=256;REQUIRE(hooks->read(cookie,0,bytes,&size)==B_BAD_ADDRESS);
 copyFail=false;REQUIRE(hooks->read(cookie,0,bytes,&size)==B_OK && size==256 && bytes[0]==0x55);REQUIRE(hooks->read(cookie,0,bytes,&size)==B_OK && !size);
 size=321;REQUIRE(hooks->write(cookie,0,bytes,&size)==B_BAD_VALUE);size=100;REQUIRE(hooks->write(cookie,0,bytes,&size)==B_OK && !submits);
 copyFail=true;size=220;REQUIRE(hooks->write(cookie,0,bytes,&size)==B_BAD_ADDRESS);copyFail=false;
 REQUIRE(hooks->write(cookie,0,bytes,&size)==B_OK && submits==1);REQUIRE(hooks->write(cookie,0,bytes,&size)==B_BAD_VALUE);
 REQUIRE(hooks->control(cookie,0,nullptr,0)==B_NOT_ALLOWED);REQUIRE(hooks->close(cookie)==B_OK && detaches==1);REQUIRE(hooks->free_cookie(cookie)==B_OK && modulePuts==1);
 REQUIRE(hooks->open("misc/k40_mem_stage",0,&cookie)==B_ENTRY_NOT_FOUND && prepares==2 && modulePuts==2);REQUIRE(submits==1);
 std::printf("Memory actual client: %u checks pass (host mocks only)\n",checks);
}
