// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include <KernelExport.h>
struct device_hooks {
 status_t (*open)(const char*,uint32,void**);
 status_t (*close)(void*);
 status_t (*free_cookie)(void*);
 status_t (*control)(void*,uint32,void*,size_t);
 status_t (*read)(void*,off_t,void*,size_t*);
 status_t (*write)(void*,off_t,const void*,size_t*);
 void* select;void* deselect;void* readv;void* writev;
};
