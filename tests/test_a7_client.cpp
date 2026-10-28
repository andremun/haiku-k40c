// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <Drivers.h>
#include "a7/Module.h"
extern "C" device_hooks* find_device(const char*);
static unsigned checks=0,prepares=0,submits=0,detaches=0,modulePuts=0;
static bool copyFail=false,moduleFail=false;
#define REQUIRE(x) do{++checks;if(!(x)){std::fprintf(stderr,"line %u: %s\n",__LINE__,#x);std::exit(1);}}while(0)
static int prepare(uint64* lease,uint8* request){++prepares;if(prepares>1)return K40_A7_RETAINED;*lease=1;std::memset(request,0x55,128);return K40_A7_OK;}
static int submit(uint64 lease,const uint8*,size_t bytes){++submits;REQUIRE(lease==1 && bytes==192);return K40_A7_OK;}
static int detach(uint64 lease){++detaches;REQUIRE(lease==1);return K40_A7_RETAINED;}
static k40_a7_module api={{K40_A7_OWNER_NAME,B_KEEP_LOADED,nullptr},1,prepare,submit,detach};
extern "C" status_t get_module(const char* name,module_info** out){REQUIRE(!std::strcmp(name,K40_A7_OWNER_NAME));if(moduleFail)return B_ERROR;*out=&api.info;return B_OK;}
extern "C" status_t put_module(const char*){++modulePuts;return B_OK;}
status_t user_memcpy(void* out,const void* in,size_t bytes){if(copyFail)return B_BAD_ADDRESS;std::memcpy(out,in,bytes);return B_OK;}
int k40_a7_mock_log(const char*,...){return 0;}
int main()
{
 auto* hooks=find_device("misc/k40_a7_stage");REQUIRE(hooks && !find_device("misc/other"));void* cookie=nullptr;
 moduleFail=true;REQUIRE(hooks->open("misc/k40_a7_stage",0,&cookie)==B_ERROR && prepares==0 && modulePuts==0);moduleFail=false;
 REQUIRE(hooks->open("misc/k40_a7_stage",0,&cookie)==B_OK);void* other=nullptr;REQUIRE(hooks->open("misc/k40_a7_stage",0,&other)==B_BUSY);
 uint8 bytes[193]{};size_t size=1;REQUIRE(hooks->write(cookie,0,bytes,&size)==B_BAD_VALUE);
 size=127;REQUIRE(hooks->read(cookie,0,bytes,&size)==B_BAD_VALUE);copyFail=true;size=128;REQUIRE(hooks->read(cookie,0,bytes,&size)==B_BAD_ADDRESS);
 copyFail=false;REQUIRE(hooks->read(cookie,0,bytes,&size)==B_OK && size==128 && bytes[0]==0x55);REQUIRE(hooks->read(cookie,0,bytes,&size)==B_OK && !size);
 size=193;REQUIRE(hooks->write(cookie,0,bytes,&size)==B_BAD_VALUE);size=100;REQUIRE(hooks->write(cookie,0,bytes,&size)==B_OK && !submits);
 copyFail=true;size=92;REQUIRE(hooks->write(cookie,0,bytes,&size)==B_BAD_ADDRESS);copyFail=false;
 REQUIRE(hooks->write(cookie,0,bytes,&size)==B_OK && submits==1);REQUIRE(hooks->write(cookie,0,bytes,&size)==B_BAD_VALUE);
 REQUIRE(hooks->control(cookie,0,nullptr,0)==B_NOT_ALLOWED);REQUIRE(hooks->close(cookie)==B_OK && detaches==1);REQUIRE(hooks->free_cookie(cookie)==B_OK && modulePuts==1);
 REQUIRE(hooks->open("misc/k40_a7_stage",0,&cookie)==B_ERROR && prepares==2 && modulePuts==2);REQUIRE(submits==1);
 std::printf("A7 actual client: %u checks pass (host mocks only)\n",checks);
}
