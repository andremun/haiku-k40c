// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Synthetic parser/policy failures; no firmware or hardware access.
#include "devinit/PostImage.h"
#include "board_fake.h"
#include <cstdio>
#include <memory>
#include <type_traits>
#include <vector>
using namespace k40::devinit;
static unsigned checks=0,failed=0;
#define CHECK(c) do { ++checks; if (!(c)) { ++failed; std::printf("FAIL %d: %s\n",__LINE__,#c); } } while(0)
static std::vector<uint8_t> image()
{
    std::vector<uint8_t> r(2048);
    r[32]=255;r[33]=184;r[34]='B';r[35]='I';r[36]='T';r[41]=6;r[42]=2;
    r[44]='I';r[45]=1;r[46]=18;r[48]=80;
    r[50]='M';r[51]=2;r[52]=3;r[54]=112;
    r[80]=144;r[112]=2;r[144]=0;r[145]=1;
    r[256]=0x7a;r[257]=0;r[258]=2;r[265]=0x71;
    return r;
}
int main()
{
    static_assert(!std::is_copy_constructible<PostImage>::value);
    static_assert(!std::is_move_constructible<PostImage>::value);
    auto rom=image(); PostLayout layout;
    CHECK(layout.inspect(rom.data(),uint32_t(rom.size()))==Error::None);
    CHECK(layout.count()==2 && layout.roots()==1 && layout.root(0)==256 && !layout.root(1));
    CHECK(layout.allow(256,0x200,4,true) && !layout.allow(256,0x200,4,false));
    CHECK(!layout.allow(256,0x204,4,true) && !layout.allow(257,0x200,4,true));
    CHECK(!layout.allow(256,0x200,1,true) && !layout.allow(256,0x80000200,4,true));
    uint8_t group=99;CHECK(layout.group(1,group) && group==1);CHECK(!layout.group(2,group));
    for (unsigned problem=0;problem<10;++problem) {
        rom=image();
        if(problem==0)rom[41]=5;
        if(problem==1)rom[50]='I';
        if(problem==2)rom[45]=2;
        if(problem==3)rom[144]=255,rom[145]=255;
        if(problem==4)rom[256]=0xfe;
        if(problem==5)rom[260]=0x80; // Encoded display context in register.
        if(problem==6)rom[256]=0x36;
        if(problem==7)rom[256]=0x33,rom[257]=0;
        if(problem==8)rom[256]=0x5b,rom[257]=1,rom[258]=1; // Target enters instruction payload.
        if(problem==9)rom[256]=0x75,rom[257]=1,rom[258]=0x71,rom[86]=250,rom[87]=7;
        CHECK(layout.inspect(rom.data(),uint32_t(rom.size()))!=Error::None);
        CHECK(layout.count()==0 && !layout.allow(256,0x200,4,true));
    }
    CHECK(layout.inspect(nullptr,2048)==Error::Input);
    rom=image();rom[256]=0x75;rom[257]=0;rom[258]=0x71;
    CHECK(layout.inspect(rom.data(),uint32_t(rom.size()))==Error::None);
    CHECK(!layout.allow(256,0,4,false)); // Missing conditions are false, not a register read.
    rom[86]=244; // Condition entry overlaps root bytes at 256 only for index 1.
    rom[257]=1;
    CHECK(layout.inspect(rom.data(),uint32_t(rom.size()))!=Error::None);
    rom=image();rom[52]=7;rom[115]=0x20;rom[116]=3; // M0203 pointer 800.
    rom[800]=0x10;rom[801]=7;rom[802]=2;rom[803]=2;
    rom[807]=0x33;rom[808]=1;rom[809]=0x33;rom[810]=0;
    CHECK(layout.inspect(rom.data(),uint32_t(rom.size()))==Error::None);
    CHECK(layout.group(3,group) && group==1); // First match wins.
    CHECK(!layout.group(2,group)); // Invalid fallback is not reduced modulo groups.
    rom[802]=1;CHECK(layout.inspect(rom.data(),uint32_t(rom.size()))!=Error::None);
    // Rejected images never reach the simulated strap callback.
    auto rejected=std::make_unique<PostImage>(rom.data(),uint32_t(rom.size()));
    BoardFake backend;
    CHECK(!rejected->approved() && rejected->selectRam(backend)==Error::Denied && backend.events.empty());
    backend.simulation=false;
    CHECK(rejected->selectRam(backend)==Error::HardwareDisabled && backend.events.empty());
    std::printf("immutable POST parser: %u checks, %u failures (HOST_ONLY)\n",checks,failed);
    return failed?1:0;
}
