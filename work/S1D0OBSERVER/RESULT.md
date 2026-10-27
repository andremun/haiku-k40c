# S1D0OBSERVER result — 2026-10-27

DONE for host observer/source/fixture boundary. Grouped review pending.

- Installed strace lacks VFIO payload decoding; exact Ubuntu source was reconstructed.
- Built a separate pinned userspace observer with an original narrow Type1 decoder.
  No system tool changed or installed. No source file was copied into the driver.
- Actual owned-child /dev/null SETUP/MAP/UNMAP calls all returned ENOTTY, with full
  decoded inputs. The decoder reads returned unmap size on successful syscall exit;
  that success path has source/unit evidence only.
- Strict bounded normalization tracks FD opens/closes/reuse, fixed process identity,
  setup, syscall outcomes and actual unmap result sizes before model handoff.
- Unsupported/injected/interrupted/unfinished/unreadable/ambiguous input closes
  coverage. Other processes require additional shared-fd proof and are rejected.
- Source/binary/capture metadata has exact --check support and six external pins.

Validation: eight source-format/model tests pass. Full make check passes.
Observer build and exact generated-source --check pass; six external hashes pass.
The actual trace supplies no successful VFIO ioctl or mapping coverage. Positive
unit histories change strings only in memory and are explicitly synthetic.

No guest, VFIO device, physical GPU, PCI/BAR, root, binding, reset or push occurred.
No provider/publication or cache-visibility authority was added. Q7 stays open.
Next: S1D0PACKAGE concrete closed stage and supervision, device/container binding,
realized address space, live cutoff and fault baselines. Hardware approval persists
under ADR 008; the physical D0 run is a separate later task, after prerequisites.
