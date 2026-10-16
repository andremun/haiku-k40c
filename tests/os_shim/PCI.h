/* Copyright 2026 Mario Andrés Muñoz.
 * Distributed under the terms of the MIT License. Host mock types only. */
#pragma once
#include <KernelExport.h>
#define B_PCI_MODULE_NAME "host-test-pci"
/* PCI memory-BAR flag facts: reference/haiku/headers/os/drivers/PCI.h. */
#define PCI_address_space 1
#define PCI_address_type 6
#define PCI_address_type_64 4
typedef struct {
 uint8 header_type;
 union {struct {uint32 base_registers_pci[6];uint32 base_register_sizes[6];uint8 base_register_flags[6];}h0;}u;
} pci_info;
typedef struct {int unused;}pci_module_info;
