# Macro task S1OWNERPOST: persistent owner POST binding

## Why

S1HELPERS cross-links the immutable bound executor and guarded helpers without
hosted storage. It still lacks permanent owner placement and the guest-wide
startup latch. Connect those lifetimes on the host before a physical stage exists.

## Inputs

Read docs/STATUS.md, docs/NATIVE-OWNER.md, docs/POST-BINDING.md,
work/S1HELPERS/RESULT.md and docs/decisions/007*.
Use NativeOwner/HaikuOwnerModule/OwnerClient, BootState, PostImage/BoundPost,
and their current tests. Read docs/HAIKU_BUILD_TEST.md before Haiku changes.
Do not reopen hardware research or extend the six board permissions.

## Outputs

- Record the ownership/API plan before implementation. Give the immutable image
  and execution state permanent owner storage. No large kernel-stack objects.
- Validate the lease and bind one exact ROM snapshot. Reject replacement and
  wrong identity. Cache selection and bind execution to the existing boot latch.
- Consume the guest-wide startup attempt before any simulated preinit/POST effect.
  Retain failed state and quarantine across detach/reload. No new adapter/image
  may reset the attempt. Keep default-denied DMA publication intact.
- Permit host simulation only. Do not retain client callback/provider pointers
  after a call. Native ABI changes must fail closed without physical transports.
  Separate host fixtures from anything callable by a native client.
- Test ownership, detach/reacquire, wrong lease/ROM, failed initialization,
  one-shot selection/startup, callback lifetimes and quarantine. Cross-link the
  affected native units. Linking is not execution or GPU evidence.
- Update source-bound reports as needed, licensing/provenance, status and work
  records. Run make check and commit small working steps on main.

## Limits

Host/source and native compile/link only. No VM, hardware, root, PCI/BAR, reset,
binding or push. No new stage permission or hardware backend. Keep guest-wide
ownership separate from verified DMA/visibility, owned VRAM and readiness gates.
Do not expose a production startup entry point or claim A7 readiness.
