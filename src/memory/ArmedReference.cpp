// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#include "memory/ArmedReference.h"
namespace k40::memory {
void ArmedReference::retain()
{ if(owned_.token && !retained_) { storage_.retain(owned_);retained_=true; } }
ArmedReference::~ArmedReference() { retain(); }
void ArmedReference::fail() { retain();state_=State::Failed; }
bool ArmedReference::prepare()
{
    if(state_!=State::Empty)return false;
    state_=State::Failed;
    const bool ready=storage_.reserveZeroed(owned_);
    retain(); // Retain before exposing a challenge, including a partial failure.
    if(!ready || !owned_.token || !owned_.physical.value || owned_.bytes!=4096 || (owned_.physical.value&4095)
        || owned_.physical.value>uint64_t(UINT32_MAX)-4095)return false;
    state_=State::Prepared;return true;
}
bool ArmedReference::bind(const ArmGrant& grant)
{
    if(state_!=State::Prepared)return false;
    if(grant.token_!=owned_.token || grant.gpa_.value!=owned_.physical.value
        || grant.bytes_!=owned_.bytes || grant.iova_.value!=owned_.physical.value
        || (grant.iova_.value&4095) || grant.iova_.value>uint64_t(UINT32_MAX)-4095
        || (grant.iova_.value>>8)>UINT32_MAX) { fail();return false; }
    address_=grant.iova_;state_=State::Bound;return true;
}
bool ArmedReference::beginArm(DeviceIova& address)
{
    if(state_!=State::Bound)return false;
    state_=State::Armed;address=address_;return true;
}
}
