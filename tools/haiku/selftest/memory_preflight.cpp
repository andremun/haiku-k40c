// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Read-only G0. It never reserves the device or writes PCI/MMIO state.
#include <Drivers.h>
#include <KernelExport.h>
#include <PCI.h>
#include <cstring>
namespace {
const char* devices[]={"misc/k40_mem_preflight",nullptr};
status_t result=B_NO_INIT;
status_t openDevice(const char*,uint32,void** cookie){dprintf("k40_mem_preflight: OPEN result=%08lx\n",static_cast<unsigned long>(uint32(result)));if(result==B_OK)*cookie=nullptr;return result;}
status_t closeDevice(void*){return B_OK;}status_t controlDevice(void*,uint32,void*,size_t){return B_NOT_ALLOWED;}
status_t readDevice(void*,off_t,void*,size_t* bytes){*bytes=0;return B_OK;}
status_t writeDevice(void*,off_t,const void*,size_t*){return B_NOT_ALLOWED;}
device_hooks hooks={openDevice,closeDevice,closeDevice,controlDevice,readDevice,writeDevice,nullptr,nullptr,nullptr,nullptr};
status_t inspect()
{
    pci_module_info* pci=nullptr;
    auto loaded=get_module(B_PCI_MODULE_NAME,reinterpret_cast<module_info**>(&pci));if(loaded!=B_OK)return loaded;
    pci_info card{};unsigned count=0;bool ended=false;
    for(unsigned i=0;i<256;++i){pci_info found{};if(pci->get_nth_pci_info(i,&found)!=B_OK){ended=true;break;}
        if(found.vendor_id==0x10de && found.device_id==0x1024){card=found;++count;}} // no source: fixed PCI identity from hardware/record.json.
    status_t status=B_BAD_DATA;
    if(ended && !count)status=B_ENTRY_NOT_FOUND;
    else if(ended && count==1 && !(card.header_type&0x7f) && !(card.u.h0.base_register_flags[0]&PCI_address_space)) { // no source: type-0 memory-BAR software profile, PCI.h.
        const auto command=pci->read_pci_config(card.bus,card.device,card.function,PCI_command,2);
        uint64 physical=card.u.h0.base_registers_pci[0];
        if((card.u.h0.base_register_flags[0]&PCI_address_type)==PCI_address_type_64)physical|=uint64(card.u.h0.base_registers_pci[1])<<32;
        if((command&PCI_command_memory) && physical && physical%B_PAGE_SIZE==0 && card.u.h0.base_register_sizes[0]>=B_PAGE_SIZE) {
            void* address=nullptr;const auto area=map_physical_memory("k40 G0 UC read-only",physical,B_PAGE_SIZE,
                B_ANY_KERNEL_ADDRESS|B_UNCACHED_MEMORY,B_KERNEL_READ_AREA,&address);
            if(area>=0){const auto pending=*reinterpret_cast<volatile uint32*>(static_cast<uint8*>(address)+0x100); // fb/gf100.c:37 raw MC status read only.
                dprintf("k40_mem_preflight: G0 raw_mc=%08x requested=explicit-UC read-only\n",pending);
                status=pending?B_BAD_DATA:B_OK;if(delete_area(area)!=B_OK)status=B_ERROR;
            }else status=area;
        }
    }
    if(put_module(B_PCI_MODULE_NAME)!=B_OK)return B_ERROR;
    return status;
}
}
extern "C" {
int32 api_version=B_CUR_DRIVER_API_VERSION;
status_t init_hardware(){return B_OK;}
status_t init_driver(){result=inspect();dprintf("k40_mem_preflight: LOAD result=%08lx\n",static_cast<unsigned long>(uint32(result)));return B_OK;}
void uninit_driver(){dprintf("k40_mem_preflight: UNLOAD\n");}
const char** publish_devices(){return devices;}
device_hooks* find_device(const char* name){return name && !std::strcmp(name,devices[0])?&hooks:nullptr;}
}
