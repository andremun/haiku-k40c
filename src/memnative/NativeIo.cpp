// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#ifdef _KERNEL_MODE
#include "memnative/NativeIo.h"
namespace k40::memnative {
status_t NativeIo::initialize()
{
    if(attempted_ || !policy_)return B_BUSY;
    attempted_=true;
    if(get_module(B_PCI_MODULE_NAME,reinterpret_cast<module_info**>(&pci_))!=B_OK)return B_NO_INIT;
    unsigned matches=0;bool ended=false;
    for(unsigned i=0;i<256;++i) { // no source: bounded software PCI inventory.
        pci_info card{};if(pci_->get_nth_pci_info(i,&card)!=B_OK){ended=true;break;}
        if(card.vendor_id==0x10de && card.device_id==0x1024){card_=card;++matches;} // no source: fixed PCI identity, hardware/record.json.
    }
    if(ended && !matches){dprintf("k40_mem: NO_CARD before reservation or mapping\n");return B_ENTRY_NOT_FOUND;}
    if(!ended || matches!=1 || (card_.header_type&0x7f))return B_BAD_DATA; // no source: type-0-only software profile, Haiku PCI.h lines 727,733.
    const auto command=pci_->read_pci_config(card_.bus,card_.device,card_.function,PCI_command,2);
    if(!(command&PCI_command_memory))return B_NOT_ALLOWED;
    // The original A7 KEEP_LOADED owner holds the sole reservation. Never call
    // reserve_device here, and never change PCI command or any BAR sizing bits.
    const auto resource=[&](unsigned index,uint64_t& address,uint64_t& bytes) {
        const auto flags=card_.u.h0.base_register_flags[index];
        if(flags&PCI_address_space)return false;
        address=card_.u.h0.base_registers_pci[index];
        if((flags&PCI_address_type)==PCI_address_type_64) {
            if(index==5)return false;
            address|=uint64_t(card_.u.h0.base_registers_pci[index+1])<<32;
        } else if((flags&PCI_address_type)!=PCI_address_type_32)return false;
        bytes=card_.u.h0.base_register_sizes[index];
        return address && bytes && !(address%B_PAGE_SIZE) && !(bytes%B_PAGE_SIZE)
            && !(bytes&(bytes-1)) && bytes<=UINT64_MAX-address;
    };
    // A 64-bit BAR0 consumes slot 1 and cannot coexist with the selected BAR1
    // resource. Slot 2 is BAR1's possible upper word, not NVIDIA BAR2.
    if((card_.u.h0.base_register_flags[0]&PCI_address_type)==PCI_address_type_64
        || !resource(0,bar0_,bar0Bytes_) || !resource(1,bar1_,bar1Bytes_))return B_BAD_DATA;
    if(bar0Bytes_<8388608 || bar0Bytes_>16777216 || bar1Bytes_<8192
        || bar1Bytes_>(uint64_t(1)<<40) || (bar0_<bar1_+bar1Bytes_ && bar1_<bar0_+bar0Bytes_))return B_BAD_DATA; // no source: finite aperture software profile.
    void* address=nullptr;
    area0_=map_physical_memory("k40 memory BAR0 UC",bar0_,8388608,
        B_ANY_KERNEL_ADDRESS|B_UNCACHED_MEMORY,B_KERNEL_READ_AREA|B_KERNEL_WRITE_AREA,&address);
    dprintf("k40_mem: MAP bar=0 base=%llx resource=%llu mapped=8388608 flags=explicit-UC status=%ld\n",
        (unsigned long long)bar0_,(unsigned long long)bar0Bytes_,long(area0_));
    if(area0_<0)return area0_;
    view0_=static_cast<volatile uint8_t*>(address);address=nullptr;
    // Writable for the single policy-checked GP_PUT word (Policy::barWrite).
    area1_=map_physical_memory("k40 memory BAR1 UC",bar1_,8192,
        B_ANY_KERNEL_ADDRESS|B_UNCACHED_MEMORY,B_KERNEL_READ_AREA|B_KERNEL_WRITE_AREA,&address);
    dprintf("k40_mem: MAP bar=1 base=%llx resource=%llu mapped=8192 flags=explicit-UC read-write status=%ld\n",
        (unsigned long long)bar1_,(unsigned long long)bar1Bytes_,long(area1_));
    if(area1_<0)return area1_;
    view1_=static_cast<volatile uint8_t*>(address);profile_=true;policy_->aperture(bar1Bytes_);return B_OK;
}
bool NativeIo::now(uint64_t& value)
{const auto time=system_time();if(time<0)return false;value=uint64_t(time);return true;}
void NativeIo::activate(){uint64_t value=0;live_=profile_ && now(value);start_=value;}
void NativeIo::revoke(){live_=false;}
bool NativeIo::deny(unsigned kind,uint32_t offset,uint32_t value)
{live_=false;if(!denial_){denial_=kind;denialOffset_=offset;denialValue_=value;}return false;}
bool NativeIo::active() const
{
    const auto time=system_time();return live_ && time>=0 && uint64_t(time)>=start_
        && uint64_t(time)-start_<30000000; // no source: independent aggregate memory-stage deadline, microseconds.
}
memstage::CacheProfile NativeIo::profile() const
{return profile_?memstage::CacheProfile::ExplicitUncached:memstage::CacheProfile::Unknown;}
bool NativeIo::acquire(memstage::Lock lock)
{
    const unsigned index=unsigned(lock);if(index>=2 || !active())return false;
    const auto start=system_time();if(start<0)return deny();
    for(unsigned count=0;count<100000;++count) { // no source: finite lock-acquisition software bound.
        const auto time=system_time();
        if(time<start || time-start>=2000000 || !active())return deny(); // no source: two-second software lock budget.
        if(!locks_[index].test_and_set(std::memory_order_acquire)){held_[index]=true;return true;}
    }
    return deny();
}
void NativeIo::release(memstage::Lock lock)
{const auto index=unsigned(lock);if(index<2 && held_[index]){held_[index]=false;locks_[index].clear(std::memory_order_release);}}
bool NativeIo::read32(uint32_t offset,uint32_t& value)
{
    value=0;if(!active() || !view0_ || offset>8388608-4 || !policy_->read(offset,held_[0]))return deny(2,offset); // no source: explicit BAR0 mapping extent.
    value=*reinterpret_cast<volatile uint32_t*>(view0_+offset);policy_->observed(offset,value);return true;
}
bool NativeIo::write32(uint32_t offset,uint32_t value)
{
    if(!active() || !view0_ || offset>8388608-4 || !policy_->write(offset,value,held_[0],held_[1]))return deny(3,offset,value); // no source: explicit BAR0 mapping extent.
    *reinterpret_cast<volatile uint32_t*>(view0_+offset)=value;return true;
}
bool NativeIo::barRead32(uint64_t offset,uint32_t& value)
{
    value=0;if(!active() || !view1_ || !policy_->barRead(offset,held_[1]))return deny(4,uint32_t(offset));
    value=*reinterpret_cast<volatile uint32_t*>(view1_+offset);return true;
}
bool NativeIo::barWrite32(uint64_t offset,uint32_t value)
{
    if(!active() || !view1_ || offset>8192-4 || !policy_->barWrite(offset,value,held_[1]))return deny(5,uint32_t(offset),value);
    *reinterpret_cast<volatile uint32_t*>(view1_+offset)=value;return true;
}
bool NativeIo::storeFence(){if(!active())return deny();asm volatile("sfence":::"memory");return true;} // atomic.h:17-26 x86 ordering.
bool NativeIo::loadFence(){if(!active())return deny();asm volatile("mfence; lfence":::"memory");return true;} // atomic.h:17-26 x86 ordering.
}
#endif
