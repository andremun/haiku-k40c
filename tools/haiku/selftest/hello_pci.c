/*
 * Copyright 2026 Mario Andrés Muñoz. Distributed under the terms of the MIT License.
 *
 * Toolchain test driver (not project code). On load it finds the first
 * display-class PCI device, maps its MMIO BAR and reads one register.
 * In the QEMU test VM that device is the Bochs VGA (1234:1111): BAR2 is
 * MMIO, and the 16-bit ID register at offset 0x500 reads 0xB0C0..0xB0C5.
 */
#include <KernelExport.h>
#include <Drivers.h>
#include <PCI.h>

#define TAG "hello_pci: "

int32 api_version = B_CUR_DRIVER_API_VERSION;
static pci_module_info* sPCI;
static const char* sDevices[] = { NULL };

status_t
init_hardware(void)
{
	return B_OK;
}

status_t
init_driver(void)
{
	pci_info info;
	int32 i;

	dprintf(TAG "init_driver\n");
	if (get_module(B_PCI_MODULE_NAME, (module_info**)&sPCI) != B_OK)
		return B_ERROR;

	for (i = 0; sPCI->get_nth_pci_info(i, &info) == B_OK; i++) {
		int bar;
		void* regs;
		area_id area;

		if (info.class_base != PCI_display)
			continue;
		dprintf(TAG "display device %04x:%04x at %02x:%02x.%x\n",
			info.vendor_id, info.device_id, info.bus, info.device,
			info.function);
		for (bar = 0; bar < 6; bar++) {
			if (info.u.h0.base_register_sizes[bar] != 0) {
				dprintf(TAG "  BAR%d base 0x%" B_PRIx32 " size 0x%" B_PRIx32
					" flags 0x%x\n", bar, info.u.h0.base_registers[bar],
					info.u.h0.base_register_sizes[bar],
					info.u.h0.base_register_flags[bar]);
			}
		}
		if (info.vendor_id == 0x1234 && info.device_id == 0x1111) {
			area = map_physical_memory("hello_pci mmio",
				info.u.h0.base_registers[2], B_PAGE_SIZE, B_ANY_KERNEL_ADDRESS,
				B_KERNEL_READ_AREA, &regs);
			if (area < 0) {
				dprintf(TAG "  map failed: %d\n", (int)area);
			} else {
				dprintf(TAG "  MMIO read16 [BAR2+0x500] = 0x%04x\n",
					*(volatile uint16*)((uint8*)regs + 0x500));
				delete_area(area);
			}
		}
		break;
	}
	return B_OK;
}

void
uninit_driver(void)
{
	dprintf(TAG "uninit_driver\n");
	put_module(B_PCI_MODULE_NAME);
}

const char**
publish_devices(void)
{
	return sDevices;
}

device_hooks*
find_device(const char* name)
{
	return NULL;
}
