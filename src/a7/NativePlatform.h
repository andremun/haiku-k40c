// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "a7/Owner.h"
#include "os/HaikuMemory.h"
namespace k40::a7 {
class NativeStorage final:public memory::ArmStorage {
public:
    bool reserveZeroed(memory::ArmAllocation&) override;
    void retain(const memory::ArmAllocation&) override;
private:
    os::NativePool pool_;
    os::HaikuMemory memory_{pool_}; // No provider and no production publication.
    memory::Allocation allocation_{};
    bool attempted_=false;
};
class NativePlatform final:public Platform {
public:
    bool initialize() override;
    bool pciCommand(uint16_t&) override;
    uint64_t nowUs() override;
    bool delayUs(uint64_t) override;
    bool read32(uint32_t,uint32_t&) override;
    bool write32(uint32_t,uint32_t) override;
    bool read8(uint32_t,uint8_t&) override;
    bool write8(uint32_t,uint8_t) override;
    void log(const char*,uint64_t,uint64_t=0) override;
private:
    pci_module_info* pci_=nullptr;
    pci_info card_{};
    area_id mapping_=-1;
    volatile uint8_t* registers_=nullptr;
    size_t bytes_=0;
};
}
