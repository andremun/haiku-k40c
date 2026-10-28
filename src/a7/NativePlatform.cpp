// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "a7/NativePlatform.h"
#include <KernelExport.h>
namespace k40::a7 {
bool NativeStorage::reserveZeroed(memory::ArmAllocation& out)
{
    out={};if(attempted_)return false;attempted_=true;
    if(!memory_.allocate(4096,4096,memory::Placement::Host,allocation_)) {
        if(allocation_.id){out.token=allocation_.id;memory_.quarantine(allocation_);}return false;
    }
    os::HaikuMemory::Info info;
    if(!memory_.describe(0,info) || !info.physicalKnown || info.mappingVerified
        || allocation_.deviceAddressVerified) {out.token=allocation_.id;memory_.quarantine(allocation_);return false;}
    out={info.token,info.bytes,info.physical};
    const uint8_t zeros[256]={};
    for(unsigned offset=0;offset<4096;offset+=sizeof(zeros))
        if(!memory_.write(allocation_,offset,zeros,sizeof(zeros))) {memory_.quarantine(allocation_);return false;}
    // CPU access ends here. The type exposes no data API, and pool quarantine
    // also rejects native read/write/release. No recovery API is exported.
    memory_.quarantine(allocation_);return true;
}
void NativeStorage::retain(const memory::ArmAllocation& allocation)
{if(allocation.token==allocation_.id && allocation_.id)memory_.quarantine(allocation_);}
bool NativePlatform::initialize()
{
    if(pci_ || registers_)return false;
    if(get_module(B_PCI_MODULE_NAME,reinterpret_cast<module_info**>(&pci_))!=B_OK)return false;
    unsigned matches=0;bool terminated=false;
    for(unsigned index=0;index<256;++index) {
        pci_info info{};
        if(pci_->get_nth_pci_info(index,&info)!=B_OK){terminated=true;break;}
        if(info.vendor_id==0x10de && info.device_id==0x1024){card_=info;++matches;} // no source: software PCI identity comparison; KNOWN capture hardware/record.json:4.
    }
    if(!terminated || matches!=1 || (card_.header_type&0x7f)!=0)return false; // no source: software type-0-only guard; Haiku PCI.h lines 727,733 define the mask and type.
    // PCI.h:159-164 supplies a cooperative exclusive reservation. Keep it for
    // the module lifetime. Never take a device reserved by another guest driver.
    if(!pci_->reserve_device || pci_->reserve_device(card_.bus,card_.device,card_.function,"k40_a7_stage",this)!=B_OK)return false;
    // Haiku nvidia/driver.c:674-695 and PCI.h BAR fields, same reconstruction
    // as the identity backend. This separate A7 artifact alone maps writable.
    const uint8_t flags=card_.u.h0.base_register_flags[0];
    if(flags&PCI_address_space)return false;
    uint64_t physical=card_.u.h0.base_registers_pci[0];
    if((flags&PCI_address_type)==PCI_address_type_64)physical|=uint64_t(card_.u.h0.base_registers_pci[1])<<32;
    bytes_=card_.u.h0.base_register_sizes[0];
    // no source: software mapping ceiling, not a hardware aperture assertion.
    if(!physical || physical%B_PAGE_SIZE || bytes_<0x800000 || bytes_>0x1000000
        || bytes_%B_PAGE_SIZE || bytes_>UINT64_MAX-physical)return false;
    void* address=nullptr;
    mapping_=map_physical_memory("k40 A7 fixed stage",physical,bytes_,B_ANY_KERNEL_ADDRESS,
        B_KERNEL_READ_AREA|B_KERNEL_WRITE_AREA,&address);
    if(mapping_<0)return false;
    registers_=static_cast<volatile uint8_t*>(address);return true;
}
bool NativePlatform::pciCommand(uint16_t& command)
{
    if(!pci_)return false;
    command=uint16_t(pci_->read_pci_config(card_.bus,card_.device,card_.function,PCI_command,2));return true;
}
uint64_t NativePlatform::nowUs(){return uint64_t(system_time());}
bool NativePlatform::delayUs(uint64_t us)
{
    if(us>1000000)return false;
    if(us<=20)spin(bigtime_t(us));else if(snooze(bigtime_t(us))!=B_OK)return false;
    return true;
}
bool NativePlatform::read32(uint32_t offset,uint32_t& value)
{if(!registers_ || (offset&3) || offset>bytes_-4)return false;value=*reinterpret_cast<volatile uint32_t*>(registers_+offset);return true;}
bool NativePlatform::write32(uint32_t offset,uint32_t value)
{if(!writesAuthorized() || !registers_ || (offset&3) || offset>bytes_-4)return false;*reinterpret_cast<volatile uint32_t*>(registers_+offset)=value;return true;}
bool NativePlatform::read8(uint32_t offset,uint8_t& value)
{if(!registers_ || offset>=bytes_)return false;value=registers_[offset];return true;}
bool NativePlatform::write8(uint32_t offset,uint8_t value)
{if(!writesAuthorized() || !registers_ || offset>=bytes_)return false;registers_[offset]=value;return true;}
void NativePlatform::log(const char* event,uint64_t first,uint64_t second)
{dprintf("k40_a7: %s a=0x%llx b=0x%llx\n",event,(unsigned long long)first,(unsigned long long)second);}
}
