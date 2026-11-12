// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Host test of the GR program runner. The generated program must reproduce the
// accesses of the Linux reference run (fixture written by tools/gr/program.py)
// one by one, with the run data of that run. Failure cases use small programs.
// HOST_ONLY, not card evidence.
#include "gr/Runner.h"
#include <cassert>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
using namespace k40::gr;
struct Access {char op;uint32_t addr,value;};
struct Replay:Port {
    std::vector<Access> rows;size_t next=0;uint64_t clock=0;unsigned hooks=0,delays=0;bool mismatch=false;
    int flip=-1; // index of one read whose value is changed
    bool read32(uint32_t addr,uint32_t& value) override {
        if(next>=rows.size() || rows[next].op!='R' || rows[next].addr!=addr){mismatch=true;return false;}
        value=rows[next].value^(int(next)==flip?0x10u:0u);++next;return true;
    }
    bool write32(uint32_t addr,uint32_t value) override {
        if(next>=rows.size() || rows[next].op!='W' || rows[next].addr!=addr || rows[next].value!=value){mismatch=true;return false;}
        ++next;return true;
    }
    bool now(uint64_t& t) override{clock+=1000;t=clock;return true;}
    bool delay(uint32_t) override{++delays;return true;}
    bool hook(uint32_t number) override{++hooks;return number==contextPointerHook;}
};
struct Fixture {uint64_t inputs[InputCount]{};std::vector<Access> gating,start,golden;};
static Fixture load(const char* path)
{
    Fixture f;std::ifstream in(path);assert(in);std::string line;std::vector<Access>* current=nullptr;
    while(std::getline(in,line)) {
        std::istringstream s(line);char tag;s>>tag;
        if(tag=='I'){for(auto& v:f.inputs)s>>std::hex>>v;}
        else if(tag=='S'){std::string name;s>>name;current=name=="gating"?&f.gating:name=="start"?&f.start:&f.golden;}
        else {Access a{tag,0,0};s>>std::hex>>a.addr>>a.value;assert(current);current->push_back(a);}
    }
    assert(f.gating.size()==72 && f.start.size()>2000 && f.golden.size()>4000);
    return f;
}
static void whole(const Fixture& f)
{
    Replay port;Runner runner(port);
    for(unsigned i=0;i<InputCount;++i)runner.input(Input(i),f.inputs[i]);
    const std::pair<const Stage*,const std::vector<Access>*> stages[]={{&gating,&f.gating},{&start,&f.start},{&golden,&f.golden}};
    size_t total=0;
    for(const auto& s:stages) {
        port.rows=*s.second;port.next=0;
        const bool ok=runner.run(*s.first);
        if(!ok)std::printf("failure error=%u index=%u addr=%x value=%x\n",unsigned(runner.failure().error),runner.failure().index,runner.failure().addr,runner.failure().value);
        assert(ok && !port.mismatch && port.next==port.rows.size());
        total+=port.rows.size();
    }
    assert(port.hooks==1 && port.delays==3 && runner.reads()+runner.writes()==total);
    // Patch list with the run data of the reference run: page pool first (ctxgf100.c:1021-1027).
    assert(patchCount==36 && patchList[0].addr==0x40800c && runner.patchValue(patchList[0])==uint32_t(f.inputs[PagePool]>>8));
    std::printf("GR runner: %zu trace accesses reproduced by the native runner, 0 differences; ",total);
}
static void failures(const Fixture& f)
{
    // A card that answers differently at the first unit-count read stops the stage before any engine write.
    {
        Replay port;port.rows=f.start;port.flip=0;Runner runner(port);
        assert(!runner.run(start) && runner.failure().error==Error::Expect && runner.failure().index==0 && runner.writes()==0);
        assert(!runner.run(start) && runner.failure().error==Error::Expect); // no second attempt
    }
    // A poll that never matches ends at the time bound; a wrong write is refused by the port.
    {
        static const Op ops[]={{Kind::Write,noSlot,0,0x100,1,0},{Kind::Poll,noSlot,0,0x104,0x80000000,0},{Kind::Write,noSlot,0,0x108,2,0}};
        Replay port;port.rows.push_back({'W',0x100,1});
        for(int i=0;i<3000;++i)port.rows.push_back({'R',0x104,0x80000000});
        Runner runner(port);
        assert(!runner.run({ops,3}) && runner.failure().error==Error::Poll && runner.failure().index==1 && runner.writes()==1);
        assert(port.clock>=2000000 && port.clock<2100000);
    }
    {
        static const Op ops[]={{Kind::WriteSlot,0,8,0x200,0xffffffff,0x80000000},{Kind::Mask,7,0,0x204,0xf,0x3},{Kind::WriteSlot,7,0,0x208,0xffffffff,0},
            {Kind::Read,8,0,0x20c,0,0},{Kind::MaskSlot,8,0,0x210,0xf,0},{Kind::Hook,noSlot,0,0,2,0}};
        Replay port;port.rows={{'W',0x200,0x80123456},{'R',0x204,0xabcd},{'W',0x204,0xabc3},{'W',0x208,0xabcd},{'R',0x20c,6},{'R',0x210,0x34},{'W',0x210,0x36}};
        Runner runner(port);runner.input(Instance,0x12345678ull);
        assert(!runner.run({ops,6}) && runner.failure().error==Error::Hook && runner.done()==5 && port.next==port.rows.size() && !port.mismatch);
    }
    {
        static const Op ops[]={{Kind::WaitIdle,noSlot,0,0,0,0}};
        Replay port;for(int i=0;i<3000;++i){port.rows.push_back({'R',0x400700,0});port.rows.push_back({'R',0x200,0x1000});
            port.rows.push_back({'R',0x2640,0});port.rows.push_back({'R',0x40060c,1});}
        Runner runner(port);
        assert(!runner.run({ops,1}) && runner.failure().error==Error::Idle);
    }
}
int main(int argc,char** argv)
{
    assert(argc==2);
    const auto fixture=load(argv[1]);
    whole(fixture);failures(fixture);
    std::puts("expect, poll, idle, hook and slot cases pass; HOST_ONLY");
}
