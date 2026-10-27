/* Copyright 2026 Mario Andrés Muñoz.
 * Distributed under the terms of the MIT License. */
#include "HaikuBackend.h"
#include <Drivers.h>

/* PMC_BOOT_0 of the development card (K40c 0000:04:00.0): hardware/record.json:37. */
#define K40_EXPECTED_BOOT0 0x0f1240a1u

int32 api_version=B_CUR_DRIVER_API_VERSION;
static const char* devices[]={NULL};
static k40_os os;
static k40_host_allocation allocation={.area=-1};
status_t init_hardware(void) { return B_OK; }
status_t init_driver(void)
{
#ifndef K40_CARDLESS_TEST
    dprintf("k40_stage: B5_IDENTITY_READ_ONLY\n");
#endif
    status_t status=k40_os_init(&os);
    if (status!=B_OK) return status;
    status=k40_os_allocate(B_PAGE_SIZE,&allocation);
    if (status!=B_OK) goto failed;
    ((volatile uint32*)allocation.address)[0]=0x13579bdf;
    if (((volatile uint32*)allocation.address)[0]!=0x13579bdf) status=B_BAD_DATA;
    dprintf("k40_os: host allocation bytes %lu, guest physical 0x%llx; IOVA unverified\n",
        (unsigned long)allocation.bytes,(unsigned long long)allocation.guest_physical);
    status_t released=k40_os_free(&allocation);
    if (status==B_OK) status=released;
    if (status!=B_OK) goto failed;
    bigtime_t before=system_time();
    snooze(1000);
    if (system_time()<=before) { status=B_BAD_DATA; goto failed; }
    pci_info info; bool found=false;
    for (int32 index=0;os.pci->get_nth_pci_info(index,&info)==B_OK;++index) {
#ifdef K40_CARDLESS_TEST
        /* Emulated VGA identity and read-only BAR test: docs/HAIKU_BUILD_TEST.md. */
        if (info.vendor_id!=0x1234 || info.device_id!=0x1111) continue;
        found=true;
        status=k40_os_map_readonly(&os,&info,2,B_PAGE_SIZE);
        if (status!=B_OK) goto failed;
        uint16 id=*(volatile const uint16*)(os.registers+0x500);
        if (id<0xb0c0 || id>0xb0c5) { status=B_BAD_DATA; goto failed; }
        dprintf("k40_os: emulated VGA read-only MMIO id 0x%04x\n",id);
#else
        /* Recorded K40c PCI identity: hardware/record.json; no PCI writes. */
        if (info.vendor_id!=0x10de || info.device_id!=0x1024) continue;
        found=true;
        /* Read the command register only. Haiku's nvidia driver turns memory decode on before it maps
         * the BAR (src/add-ons/kernel/drivers/graphics/nvidia/driver.c:543-550). This probe must not
         * write PCI configuration, so it refuses instead. */
        uint16 command=(uint16)os.pci->read_pci_config(info.bus,info.device,info.function,PCI_command,2);
        dprintf("k40_os: PCI command 0x%04x\n",(unsigned)command);
        if ((command & PCI_command_memory)==0) {
            dprintf("k40_os: memory decode off; not mapped\n");
            status=B_NOT_ALLOWED;
            goto failed;
        }
        status=k40_os_map_readonly(&os,&info,0,B_PAGE_SIZE);
        uint32 identity=0;
        if (status==B_OK) status=k40_os_read32(&os,0,&identity);
        if (status!=B_OK) goto failed;
        if (identity==0xffffffffu) {
            dprintf("k40_os: BAR0 does not answer\n");
            status=B_IO_ERROR;
            goto failed;
        }
        if (identity!=K40_EXPECTED_BOOT0) {
            dprintf("k40_os: unexpected identity 0x%08lx\n",(unsigned long)identity);
            status=B_BAD_DATA;
            goto failed;
        }
        dprintf("k40_os: GPU identity 0x%08lx; no bring-up or DMA\n",(unsigned long)identity);
#endif
        break;
    }
#ifdef K40_CARDLESS_TEST
    if (!found) { status=B_ENTRY_NOT_FOUND; goto failed; }
#else
    if (!found) {
        dprintf("k40_os: no K40c; B5 identity unavailable\n");
        status=B_ENTRY_NOT_FOUND;
        goto failed;
    }
#endif
    status=k40_os_close(&os);
    if (status!=B_OK) goto failed;
#ifdef K40_CARDLESS_TEST
    dprintf("k40_os: PASS native OS mechanics only\n");
#else
    dprintf("k40_os: PASS B5 identity reads only\n");
#endif
    return B_OK;
failed:
    dprintf("k40_os: FAIL status %ld\n",(long)status);
    status_t memory_cleanup=k40_os_free(&allocation);
    status_t os_cleanup=k40_os_close(&os);
    if (memory_cleanup!=B_OK || os_cleanup!=B_OK)
        dprintf("k40_os: cleanup failed; retained area %ld, MMIO %ld\n",(long)allocation.area,(long)os.mapping);
    return status;
}
void uninit_driver(void)
{
    status_t memory_cleanup=k40_os_free(&allocation);
    status_t os_cleanup=k40_os_close(&os);
    if (memory_cleanup!=B_OK || os_cleanup!=B_OK) dprintf("k40_os: uninit cleanup failed\n");
}
const char** publish_devices(void) { return devices; }
device_hooks* find_device(const char* name) { (void)name; return NULL; }
