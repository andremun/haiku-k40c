/* Copyright 2026 Mario Andrés Muñoz.
 * Distributed under the terms of the MIT License. */
#include "HaikuBackend.h"
#include <string.h>

status_t k40_os_init(k40_os* os)
{
    memset(os,0,sizeof(*os)); os->mapping=-1;
    return get_module(B_PCI_MODULE_NAME,(module_info**)&os->pci);
}
status_t k40_os_close(k40_os* os)
{
    if (os->mapping>=0) {
        status_t status=delete_area(os->mapping);
        if (status!=B_OK) return status; /* Retain ownership on failure. */
        os->mapping=-1;os->registers=NULL;os->mapped_bytes=0;
    }
    if (os->pci) {
        status_t status=put_module(B_PCI_MODULE_NAME);
        if (status!=B_OK) return status;
        os->pci=NULL;
    }
    return B_OK;
}
status_t k40_os_map_readonly(k40_os* os,const pci_info* info,unsigned bar,size_t bytes)
{
    /* PCI.h base/flags and nvidia/driver.c:674-695: reconstruct high word. */
    if (!os->pci || os->mapping>=0 || bar>=6 || !bytes || bytes%B_PAGE_SIZE
        || (info->header_type & 0x7f)!=0 || bytes>info->u.h0.base_register_sizes[bar]) return B_BAD_VALUE;
    uint8 flags=info->u.h0.base_register_flags[bar];
    if (flags & PCI_address_space) return B_BAD_VALUE; /* memory BAR only */
    uint64 physical=info->u.h0.base_registers_pci[bar];
    if ((flags & PCI_address_type)==PCI_address_type_64) {
        if (bar==5) return B_BAD_VALUE;
        physical|=(uint64)info->u.h0.base_registers_pci[bar+1]<<32;
    }
    if (!physical || physical%B_PAGE_SIZE || bytes>UINT64_MAX-physical) return B_BAD_VALUE;
    void* address=NULL;
    area_id mapping=map_physical_memory("k40 read-only probe",physical,bytes,
        B_ANY_KERNEL_ADDRESS,B_KERNEL_READ_AREA,&address);
    if (mapping<0) return mapping;
    os->mapping=mapping; os->registers=address; os->mapped_bytes=bytes;
    return B_OK;
}
status_t k40_os_read32(k40_os* os,size_t offset,uint32* value)
{
    /* Stage zero read policy: identity only, not an arbitrary MMIO endpoint. */
    if (!value || !os->registers || offset!=0 || os->mapped_bytes<sizeof(uint32)) return B_BAD_VALUE;
    *value=*(volatile const uint32*)(os->registers+offset);
    return B_OK;
}
static status_t allocate_host(size_t bytes,k40_host_allocation* result,uint32 locking)
{
    if (!result || !bytes || bytes>SIZE_MAX-(B_PAGE_SIZE-1)) return B_BAD_VALUE;
    size_t rounded=(bytes+B_PAGE_SIZE-1)&~(size_t)(B_PAGE_SIZE-1);
    if (locking==B_32_BIT_CONTIGUOUS && rounded>(uint64)UINT32_MAX+1) return B_BAD_VALUE;
    memset(result,0,sizeof(*result)); result->area=-1;
    /* nvidia/driver.c:939-957; kernel OS.h area locking, KernelExport.h map. */
    result->area=create_area("k40 host scratch",&result->address,B_ANY_KERNEL_ADDRESS,
        rounded,locking,B_KERNEL_READ_AREA|B_KERNEL_WRITE_AREA);
    if (result->area<0) return result->area;
    physical_entry entry;
    status_t status=get_memory_map(result->address,rounded,&entry,1);
    const bool bad_extent=status==B_OK && (entry.size<rounded || entry.address%B_PAGE_SIZE
        || rounded>UINT64_MAX-entry.address
        || (locking==B_32_BIT_CONTIGUOUS && (entry.address>UINT32_MAX
            || rounded>((uint64)UINT32_MAX+1)-entry.address)));
    if (status!=B_OK || bad_extent) {
        status_t cleanup=delete_area(result->area);
        if (cleanup!=B_OK) return cleanup; /* Partial allocation stays owned. */
        result->area=-1; result->address=NULL;
        return status!=B_OK ? status : B_BAD_DATA;
    }
    result->bytes=rounded; result->guest_physical=entry.address;
    memset(result->address,0,rounded);
    return B_OK;
}
status_t k40_os_allocate(size_t bytes,k40_host_allocation* result)
{
    return allocate_host(bytes,result,B_CONTIGUOUS);
}
status_t k40_os_allocate_dma32(size_t bytes,k40_host_allocation* result)
{
    /* Haiku nvidia/driver.c:939-957, OS.h:77: contiguous below 4 GiB.
     * This is a conservative host allocation limit, not a claim about GK110 DMA width. */
    return allocate_host(bytes,result,B_32_BIT_CONTIGUOUS);
}
status_t k40_os_free(k40_host_allocation* allocation)
{
    if (!allocation) return B_BAD_VALUE;
    if (allocation->area>=0) {
        status_t status=delete_area(allocation->area);
        if (status!=B_OK) return status;
    }
    memset(allocation,0,sizeof(*allocation)); allocation->area=-1;
    return B_OK;
}
