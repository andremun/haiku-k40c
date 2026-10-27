// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#ifdef _KERNEL_MODE
#error "OwnerPostSimulation is a host fixture and must not enter a kernel build"
#endif
#include "os/NativeOwner.h"
#include "devinit/BoundPost.h"
namespace k40::os {
OwnerError NativeOwner::simulatePost(uint64_t lease, devinit::Backend& registers,
                                   devinit::BoardTransport& ports, devinit::Limits limits)
{
    Guard guard(lock_);
    if (!guard.held) return OwnerError::Busy;
    if (!valid(lease)) return OwnerError::Lease;
    if (!fresh()) return OwnerError::Startup;
    if (memory_.quarantinedCount()) return OwnerError::Retained;
    if (!postInfo_.bound || !post_ || !limits.steps || !limits.depth || !limits.timeoutUs)
        return OwnerError::Input;
    if (!registers.hostSimulation() || !ports.hostSimulation()) return OwnerError::Input;
    if (!startup_.begin()) return OwnerError::Startup;
    // Finish even if a faulty host fixture throws. No callback enters this guard.
    struct Attempt {
        NativeOwner& owner;
        ~Attempt() {
            owner.startup_.finish(owner.postInfo_.result.error==devinit::Error::None);
            for (auto& allocation : owner.allocations_)
                if (allocation.id) owner.memory_.quarantine(allocation);
        }
    } attempt{*this};
    // The resident latch is consumed before even the simulated strap read.
    postInfo_.executionAttempted=true;
    postInfo_.selectionAttempted=true;
    postInfo_.selection=devinit::Error::Io;
    postInfo_.result={devinit::Error::Io,0,0};
    postInfo_.selection=post_->selectRam(registers);
    postInfo_.ramSelected=post_->ramSelected();
    postInfo_.ramIndex=post_->ramIndex();
    postInfo_.result={postInfo_.selection,0,0};
    if (postInfo_.selection==devinit::Error::None) {
        // All references, helper callbacks and transport state die before return.
        devinit::BoundPost executor(*post_,registers,ports,devinit::PostI2c::DedicatedPins);
        postInfo_.result.error=devinit::Error::Io;
        const auto prepared=executor.prepareI2c();
        postInfo_.result.error=prepared;
        if (prepared==devinit::Error::None) {
            postInfo_.result.error=devinit::Error::Io;
            postInfo_.result=executor.runPost(limits);
        }
    }

    return OwnerError::None; // inspectPost contains the simulation outcome.
}
}
