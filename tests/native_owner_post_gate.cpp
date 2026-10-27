// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Compile only with tools/haiku/kcc. This is not a driver or executable probe.
#ifndef _KERNEL_MODE
#error "Compile this gate against the native kernel headers"
#endif
#include "os/NativeOwner.h"
#include <type_traits>
template<class T,class=void> struct HasSimulation : std::false_type {};
template<class T> struct HasSimulation<T,std::void_t<decltype(&T::simulatePost)>> : std::true_type {};
static_assert(!HasSimulation<k40::os::NativeOwner>::value,"Host simulation escaped into native API");
static_assert(!std::is_copy_constructible<k40::os::NativeOwner>::value,"Resident owner cannot be copied");
