// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "os/HaikuOwnerModule.h"
namespace k40::os {
// Legacy driver owns this reference, not the permanent state. Caller drains and
// serializes its calls before close/uninit. No provider pointer crosses this API.
class OwnerClient {
public:
    OwnerClient() = default;
    ~OwnerClient() { close(); }
    OwnerClient(const OwnerClient&) = delete;
    OwnerClient& operator=(const OwnerClient&) = delete;
    int32 open();
    int32 close();
    const k40_owner_module* api() const { return module_; }
    uint64 lease() const { return lease_; }
private:
    k40_owner_module* module_ = nullptr;
    uint64 lease_ = 0;
};
}
