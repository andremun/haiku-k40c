# Persistent owner POST binding (S1OWNERPOST)

NativeOwner now reserves aligned resident storage for one PostImage and retains
copied POST status beside its existing boot latch and allocation pool. Host tests
connect the complete bound interpreter to that owner. Native compile/link checks
establish source compatibility only. This revision has not been loaded or executed
in Haiku, and no physical transport or production startup API exists.

## Binding and ownership

bindPost requires the current exclusive lease, Fresh startup state and no
quarantine. Null pointers and wrong sizes fail before constructing an image.
The caller must supply a readable extent for the synchronous copy. An exact-size
binding attempt constructs PostImage in owner storage, including its private ROM
snapshot and derived layout. SHA rejection consumes the binding slot. Approved
and rejected bindings both survive detach/reacquire. Replacement is always denied.
The API exposes no image pointer, table pointer, raw view or mutable storage.

inspectPost validates the lease and returns copied OwnerPostInfo diagnostics.
It records binding, selection, RAM index and the final simulation result. It grants
no execution permission. Other owner operations keep their existing contracts.
No DMA provider installation was added, and publication remains denied.

## Host simulation and the shared latch

simulatePost exists only in non-kernel builds. Its implementation lives in
OwnerPostSimulation.cpp, which rejects _KERNEL_MODE compilation. It is absent
from the native header API and linked module symbols. The version 1 C module ABI
and OwnerClient are unchanged. A native client cannot upload firmware or pass
simulation callbacks through that ABI. bindPost/inspectPost are internal C++
facilities, not new module-table operations.

Simulation validates the lease, binding, budgets, backend gates and Fresh state.
It then consumes the same OncePerBoot latch used by begin. The latch is consumed
before the cached strap read, dedicated I2C preparation or any POST effect.
Existing begin calls therefore conflict with simulation attempts. No detach,
client recreation or reconstructed adapter can supply another attempt.

The nonblocking owner guard remains held throughout the synchronous simulation.
Reentrant owner calls return Busy, including detach. A temporary BoundPost uses
DedicatedPins mode, explicit bus preparation and current-instruction pin policy.
It holds callback references only within that call. The owner retains the image,
selection, result and boot latch, not the callback-bearing executor. No client
vtable or provider pointer is retained. This split makes permanent state compatible
with short client lifetimes without placing the large image on a kernel stack.

OwnerError::None means the simulation call was admitted and returned normally.
Read inspectPost.result.error to determine POST success. Every admitted attempt
finishes Complete or Failed and immediately quarantines all owned allocations.
Complete means only that this host simulation completed. It is not independent
readiness evidence. A scope guard also finalizes and quarantines if a host fixture
throws. That exception propagates to the host caller. Failed selection prevents
bus preparation. Failed preparation prevents POST. No retry or recovery exists.

Both successful and failed outcomes survive callback destruction and client
replacement. Subsequent runs fail before reaching replacement callbacks. Existing
read/write/release restrictions and conservative detach retention remain intact.
The dedicated transport's source-only timings and Linux algorithm selection
uncertainty remain as described in docs/POST-BINDING.md.

## Evidence and reproduction

Host fixtures use simulated boots and OS allocation stubs. They do not load a
kernel module. Nine exact-ROM scenarios perform 6,388 assertions. They cover
wrong identity, binding replacement, source mutation, fresh-client execution,
stale leases, reentrancy, concurrent calls, hardware refusal, invalid budgets, cached selection,
selection/preinit/NACK/exception failure, immediate quarantine and latch conflict.
The synthetic owner suite adds rejected-binding tests without the private ROM.
It passes 177 checks. The existing owner-client probe suite still passes 13.

The simulated register 0x101000 can also occur as an explicit decoded POST
operand. The selection counter distinguishes the one cached pre-interpreter read
from those separately permitted script accesses. It does not prohibit all later
reads of that register.

Generate aggregate evidence without writing firmware bytes:

```sh
make -s -C tests ../build/tests/owner_post_probe
python3 tools/owner_post_check.py
python3 tools/owner_post_check.py --check
```

The generated work/S1OWNERPOST/host-check.json binds source hashes and ROM identity.
--check compares exact text and writes nothing. make check includes this tool under
the existing private-ROM skip rule. The report always denies production eligibility.

Cross-link against the matching Haiku kernel without loading it:

```sh
HAIKU_CROSS="$HOME/haiku-cross" \
KCFLAGS='-Werror -Wframe-larger-than=4096 -Isrc' \
bash tools/haiku/build-driver.sh k40_owner_post_module \
  src/os/HaikuBackend.c src/os/HaikuMemory.cpp src/os/NativeOwner.cpp \
  src/os/HaikuOwnerModule.cpp src/os/OwnerClient.cpp \
  src/devinit/PostImage.cpp src/devinit/BoardPolicy.cpp src/devinit/Sha256.cpp \
  src/devinit/BoundPost.cpp src/devinit/BoardCore.cpp \
  src/devinit/Interpreter.cpp src/devinit/I2c.cpp
HAIKU_CROSS="$HOME/haiku-cross" tools/haiku/kcc -std=c++17 -Werror -Isrc \
  -c tests/native_owner_post_gate.cpp -o build/haiku/owner_post_gate.o
nm -C build/haiku/k40_owner_post_module
```

The native header assertion confirms simulation is unavailable. Compiling the
host fixture with kcc deliberately fails. The linked module has no simulatePost
symbol or global constructor. Native evidence and hashes are in work/S1OWNERPOST/.
The earlier S1OWNERTEST cardless lifetime result covers its recorded revision,
not this enlarged resident owner or native POST execution.

Verified IOVA/visibility, physical lifetime/quiescence, owned VRAM and readiness
remain open. No root, VM, physical card, PCI/BAR, reset, binding or push occurred.
A7 permission and reviewed physical integration remain separate gates.
