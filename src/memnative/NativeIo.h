// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#ifdef _KERNEL_MODE
#include "memnative/Policy.h"
#include <KernelExport.h>
#include <PCI.h>
#include <atomic>
namespace k40::memnative {
class NativeOwner;
class NativeIo final:public memstage::Io {
public:
    NativeIo()=default;
    status_t initialize();
    bool active() const override;
    memstage::CacheProfile profile() const override;
    bool acquire(memstage::Lock) override;
    void release(memstage::Lock) override;
    bool now(uint64_t&) override;
    bool read32(uint32_t,uint32_t&) override;
    bool write32(uint32_t,uint32_t) override;
    bool storeFence() override;
    bool loadFence() override;
    bool barRead32(uint64_t,uint32_t&) override;
    unsigned denialKind() const{return denial_;}
    uint32_t denialOffset() const{return denialOffset_;}uint32_t denialValue() const{return denialValue_;}
    uint64_t bar0() const{return bar0_;}uint64_t bar1() const{return bar1_;}
    uint64_t bar0Bytes() const{return bar0Bytes_;}uint64_t bar1Bytes() const{return bar1Bytes_;}
private:
    friend class NativeOwner;
    void activate();void revoke();bool deny(unsigned kind=1,uint32_t offset=0,uint32_t value=0);
    Policy* policy_=nullptr;pci_module_info* pci_=nullptr;pci_info card_{};
    uint64_t bar0_=0,bar1_=0,bar0Bytes_=0,bar1Bytes_=0,start_=0;
    area_id area0_=-1,area1_=-1;volatile uint8_t* view0_=nullptr;const volatile uint8_t* view1_=nullptr;
    std::atomic_flag locks_[2]={ATOMIC_FLAG_INIT,ATOMIC_FLAG_INIT};bool held_[2]{};
    bool attempted_=false,live_=false,profile_=false;
    unsigned denial_=0;uint32_t denialOffset_=0,denialValue_=0;
};
}
#endif
