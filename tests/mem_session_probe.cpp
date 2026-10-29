// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memauth/Session.h"
#include "memory/VramArena.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
using namespace k40::memauth;
struct FakeRuntime:Runtime {
    int fail=-1;unsigned calls=0,effects=0;
    bool execute() override{++calls;for(int phase=0;phase<8;++phase){if(phase==fail)return false;++effects;}return true;}
};
int main(int argc,char** argv)
{
    if(argc!=2)return 2;
    Binding binding;for(unsigned i=0;i<32;++i){binding.nonce[i]=i+1;binding.plan[i]=i+33;}
    for(unsigned i=0;i<16;++i)binding.challenge[i]=i+65;
    binding.epoch=41;binding.owner=17;binding.bar0=268435456;binding.bar0Bytes=16777216;
    binding.bar1=536870912;binding.bar1Bytes=268435456;binding.vram=11520ULL*1048576;
    k40::memory::vram::Probe layout;layout.parts=layout.units=6;for(auto& amount:layout.mib)amount=1920;
    k40::memory::vram::Arena arena;if(!arena.configure(layout,binding.vram,binding.owner,binding.epoch))return 6;
    binding.begin=arena.begin();binding.end=arena.end();
    if(std::fread(binding.key,1,32,stdin)!=32)return 3;
    FakeRuntime runtime;Session session(binding,runtime);uint8_t request[requestBytes];
    if(!session.prepare(request))return 4;
    if(!std::strcmp(argv[1],"request")){return std::fwrite(request,1,sizeof(request),stdout)==sizeof(request)?0:5;}
    runtime.fail=std::atoi(argv[1]);uint8_t grant[grantBytes];const auto size=std::fread(grant,1,sizeof(grant),stdin);
    const bool result=session.submit(grant,size);const bool retry=session.submit(grant,size);
    const bool detached=session.detach();const bool preparedAgain=session.prepare(request);
    std::printf("passed=%u state=%u calls=%u effects=%u retry=%u detached=%u prepared_again=%u\n",result,unsigned(session.state()),runtime.calls,runtime.effects,retry,detached,preparedAgain);
}
