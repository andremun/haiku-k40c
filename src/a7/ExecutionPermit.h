// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
namespace k40::a7 {
class Owner;
// The resident A7 owner alone activates this permit for its synchronous run.
// It has no public constructor or setter and grants no DMA payload visibility.
class ExecutionPermit {
    friend class Owner;
    ExecutionPermit()=default;
    bool active_=false;
public:
    bool active() const { return active_; }
};
inline bool permitted(bool simulation,const ExecutionPermit* permit)
{ return simulation || (permit && permit->active()); }
}

namespace k40::a7 {
inline bool compatible(bool leftSimulation,const ExecutionPermit* left,
                       bool rightSimulation,const ExecutionPermit* right)
{
    return (leftSimulation && rightSimulation)
        || (!leftSimulation && !rightSimulation && left==right && permitted(false,left));
}
}
