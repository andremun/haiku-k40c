// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "os/OwnerClient.h"
#include <cstring>
namespace k40::os {
int32 OwnerClient::open()
{
    if (module_) return K40_OWNER_INPUT;
    module_info* info = nullptr;
    if (get_module(K40_OWNER_MODULE_NAME, &info) != B_OK) return K40_OWNER_IO;
    auto* module = reinterpret_cast<k40_owner_module*>(info);
    if (!module || !info->name || std::strcmp(info->name, K40_OWNER_MODULE_NAME)
        || !(info->flags & B_KEEP_LOADED) || module->abi_version != 1
        || !module->acquire || !module->detach || !module->allocate || !module->write
        || !module->read || !module->release || !module->publish || !module->begin
        || !module->finish || !module->inspect || !module->describe) {
        put_module(K40_OWNER_MODULE_NAME);
        return K40_OWNER_INPUT;
    }
    uint64 lease = 0;
    const auto result = module->acquire(&lease);
    if (result != K40_OWNER_OK || !lease) {
        put_module(K40_OWNER_MODULE_NAME);
        return result == K40_OWNER_OK ? K40_OWNER_INPUT : result;
    }
    module_ = module;
    lease_ = lease;
    return K40_OWNER_OK;
}
int32 OwnerClient::close()
{
    if (!module_) return K40_OWNER_OK;
    const auto result = module_->detach(lease_);
    if (result != K40_OWNER_OK && result != K40_OWNER_RETAINED) return result;
    // A detached lease is invalid even if module-reference release fails.
    module_ = nullptr;
    lease_ = 0;
    const auto status = put_module(K40_OWNER_MODULE_NAME);
    return status == B_OK ? result : K40_OWNER_IO;
}
}
