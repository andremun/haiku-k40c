// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memory/ArmedReference.h"
#include "a7/ExecutionPermit.h"
#include <type_traits>
template<class T,class=void>struct HasFixture:std::false_type{};
template<class T>struct HasFixture<T,std::void_t<decltype(&T::hostFixture)>>:std::true_type{};
static_assert(!HasFixture<k40::memory::ArmGrant>::value,"host fixture leaked into kernel");
static_assert(!std::is_default_constructible<k40::a7::ExecutionPermit>::value,"public execution permit");
static_assert(!std::is_convertible<k40::memory::ArmedReference*,k40::memory::Buffer*>::value,"arm became payload");
