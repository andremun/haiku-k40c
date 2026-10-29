// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memstage/Tables.h"
namespace k40::memstage::tables {
bool pte(memory::VramPhysical address,uint64_t& out)
{
    out=0;
    if((address.value&4095) || address.value>=(uint64_t(1)<<40))return false; // mmu/gk104.c:29; vmmgf100.c:35,314-319 address bits below VOL.
    out=(address.value>>8)|5;return true; // vmmgf100.c:35,314-316 valid + read-only VRAM, no PRIV/VOL/kind.
}
bool smallDirectory(memory::VramPhysical address,uint64_t& out)
{
    out=0;
    if((address.value&4095) || address.value>=(uint64_t(1)<<40))return false; // vmmgf100.c:129-140 high-half SPT address layout.
    out=(address.value<<24)|(uint64_t(1)<<32);return true; // vmmgf100.c:129-140 VRAM target; low LPT half absent.
}
bool instance(memory::VramPhysical directory,uint64_t aperture,uint64_t& base,uint64_t& limit)
{
    base=limit=0;
    if(!directory.value || (directory.value&4095) || directory.value>=(uint64_t(1)<<40))return false; // vmmgf100.c:216 PDB selector width is 32 bits after shifting.
    if(aperture<8192 || aperture>(uint64_t(1)<<40) || (aperture&(aperture-1)))return false; // no source: software PCI power-of-two aperture profile; gk104 geometry is 40 bits.
    base=directory.value;limit=aperture-1;return true; // vmmgf100.c:346-360 VRAM target zero, instance fields.
}
bool indices(memory::vram::BarVirtual va,uint64_t aperture,uint32_t& directory,uint32_t& small)
{
    directory=small=0;
    if((va.value&4095) || !aperture || aperture>(uint64_t(1)<<40) || va.value>=aperture)return false; // vmmgk104.c:39-43 small-page geometry 12+15+13.
    directory=uint32_t(va.value>>27);small=uint32_t((va.value>>12)&32767);return true; // vmmgk104.c:39-43.
}
void littleEndian(uint64_t value,uint8_t bytes[8])
{for(unsigned i=0;i<8;++i)bytes[i]=uint8_t(value>>(i*8));}
}
