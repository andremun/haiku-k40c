/* Copyright 2026 Mario Andrés Muñoz.
 * Distributed under the terms of the MIT License. Host mock types only. */
#pragma once
#include <KernelExport.h>
#define B_PCI_MODULE_NAME "host-test-pci"
/* PCI memory-BAR flag facts: reference/haiku/headers/os/drivers/PCI.h. */
#define PCI_address_space 1
#define PCI_address_type 6
#define PCI_address_type_64 4
#define PCI_command 4
#define PCI_command_memory 2
typedef struct {
 uint16 vendor_id,device_id;
 uint8 bus,device,function;
 uint8 header_type;
 union {struct {uint32 base_registers_pci[6];uint32 base_register_sizes[6];uint8 base_register_flags[6];}h0;}u;
} pci_info;
typedef struct {
 status_t (*get_nth_pci_info)(int32,pci_info*);
 uint32 (*read_pci_config)(uint8,uint8,uint8,uint8,uint8);
} pci_module_info;
