// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memstage/ChannelImage.h"
#include "memstage/Tables.h"
namespace k40::memstage::channel {
using namespace memory::vram;
bool resolve(const Arena& arena,Addresses& out)
{
    out={};unsigned found=0;
    for(unsigned i=0;i<arena.count();++i) {
        Record r;if(!arena.at(i,r))return false;
        uint64_t* slot=nullptr;
        switch(r.role) {
        case Role::ChanDirectory:slot=&out.directory;break;
        case Role::ChanSmall:slot=&out.small;break;
        case Role::ChanInstance:slot=&out.instance;break;
        case Role::Userd:slot=&out.userd;break;
        case Role::Gpfifo:slot=&out.gpfifo;break;
        case Role::Push:slot=&out.push;break;
        case Role::Runlist:slot=&out.runlist;break;
        default:break;
        }
        if(slot){if(*slot)return false;*slot=r.physical.value;++found;}
    }
    return found==7;
}
bool userdPte(uint64_t physical,uint64_t& out)
{
    out=0;
    if((physical&4095) || physical>=(uint64_t(1)<<40))return false; // vmmgf100.c:313-316 address bits below VOL.
    out=(physical>>8)|1;return true; // vmmgf100.c:313-316 valid; RO bit 2 clear for CPU GP_PUT writes.
}
unsigned image(Role role,const Addresses& a,Word out[],unsigned capacity)
{
    unsigned n=0;
    const auto add=[&](uint32_t offset,uint64_t value){if(n<capacity)out[n]={offset,value};++n;};
    uint64_t value=0,base=0,limit=0;
    switch(role) {
    case Role::ChanDirectory:
        if(!tables::smallDirectory({a.small},value))return 0;
        add(uint32_t(gpfifoVa>>27)*8,value);break; // vmmgk104.c:39-43 PDE index.
    case Role::ChanSmall:
        if(!tables::pte({a.gpfifo},value))return 0;
        add(uint32_t((gpfifoVa>>12)&32767)*8,value); // vmmgk104.c:39-43 SPT index.
        if(!tables::pte({a.push},value))return 0;
        add(uint32_t((pushVa>>12)&32767)*8,value);break;
    case Role::ChanInstance: {
        // fifo/gk104.c:88-102 RAMFC; values match trace lines 562271-562285.
        const uint64_t userd=a.userd+userdSlot;
        add(0x08,userd); // fifo/gk104.c:84,88-89 USERD physical address.
        add(0x10,0x0000face); // fifo/gk104.c:90.
        add(0x30,0xfffff902); // fifo/gk104.c:91.
        const uint64_t limit2=9; // fifo/gk104.c:85 ilog2(4096/8).
        add(0x48,(gpfifoVa&0xffffffff)|((uint64_t(gpfifoVa>>32)|(limit2<<16))<<32)); // fifo/gk104.c:92-93.
        add(0x80,uint64_t(0x20400000)<<32); // fifo/gk104.c:94 offset 0x84.
        add(0x90,uint64_t(0x30000001)<<32); // fifo/gk104.c:95 offset 0x94; devm 1, trace 562278.
        add(0x98,uint64_t(0x00000100)<<32); // fifo/gk104.c:96 offset 0x9c.
        add(0xa8,uint64_t(0x0000001f)<<32); // fifo/gk104.c:97 offset 0xac.
        add(0xb8,0xf8000000); // fifo/gk104.c:100.
        add(0xe0,uint64_t(0x00000020)<<32); // fifo/gk104.c:98 offset 0xe4, priv.
        add(0xe8,chid); // fifo/gk104.c:99.
        add(0xf8,0x10003080|(uint64_t(0x10000010)<<32)); // fifo/gk104.c:101-102.
        if(!tables::instance({a.directory},uint64_t(1)<<40,base,limit))return 0; // vmmgf100.c:346-360; trace 562253-562256.
        add(0x200,base);add(0x208,limit);break; // mmu/vmmgf100.c:346-360.
    }
    case Role::Gpfifo:
        add(0,(pushVa&0xffffffff)|((uint64_t(pushVa>>32)|(8u<<8))<<32));break; // nouveau_dma.c:83-84, 8 bytes.
    case Role::Push:add(0,nopHeader);break; // second word, NOP data, stays 0.
    case Role::Runlist:add(0,chid);break; // fifo/gk104.c:454-455 channel ID, then 0.
    case Role::Userd:break; // all zero: GP_GET and GP_PUT start at 0 (gf100_chan_userd_clear).
    default:return 0;
    }
    return n;
}
bool expected(Role role,const Addresses& a,uint64_t offset,uint32_t& value)
{
    value=0;
    if(offset&3)return false;
    Word words[16];
    const auto n=image(role,a,words,16);
    if(n>16 || (!n && role!=Role::Userd))return false;
    for(unsigned i=0;i<n;++i)if(offset>=words[i].offset && offset<words[i].offset+8) {
        value=uint32_t(words[i].value>>((offset-words[i].offset)*8));return true;
    }
    return true;
}
}
