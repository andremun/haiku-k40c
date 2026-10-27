/* Copyright 2026 Mario Andrés Muñoz.
 * Distributed under the terms of the MIT License. */
#pragma once
#include <KernelExport.h>
#include <PCI.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Native OS mechanics only. No allocation here is verified as device IOVA. */
typedef struct {
    area_id area;
    void* address;
    size_t bytes;
    phys_addr_t guest_physical;
} k40_host_allocation;
typedef struct {
    pci_module_info* pci;
    area_id mapping;
    volatile uint8* registers;
    size_t mapped_bytes;
} k40_os;
status_t k40_os_init(k40_os* os);
status_t k40_os_close(k40_os* os);
status_t k40_os_map_readonly(k40_os*,const pci_info*,unsigned bar,size_t bytes);
status_t k40_os_read32(k40_os*,size_t offset,uint32* value);
status_t k40_os_allocate(size_t bytes,k40_host_allocation*);
/* Native DMA storage choice: Haiku nvidia/driver.c:939-957, OS.h:77.
 * This returns a guest physical extent, not a verified device IOVA. */
status_t k40_os_allocate_dma32(size_t bytes,k40_host_allocation*);
status_t k40_os_free(k40_host_allocation*);
#ifdef __cplusplus
}
#endif
