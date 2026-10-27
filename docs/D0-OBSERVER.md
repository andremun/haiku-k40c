# D0 host observer boundary

The installed strace 5.16-0ubuntu3 lacks a VFIO argument decoder. Its generic
ioctl code can print a pointer instead of the requested map/unmap fields.
The separate observer build adds an original narrow decoder to the exact Ubuntu
source. No system strace is changed or installed. No host root is used.

Source reconstruction uses the official Ubuntu strace DSC and its two archives.
Their SHA-256/size checks pass. The signature was not checked. Originals remain
in /tmp/k40-observer-sources/. The build copies that source into ignored
build/observer/strace-source/. Existing LGPL source notices remain intact.
The added tools/observer/vfio_decode.inc is original MIT code.

build.py validates the original ioctl.c content hash, inserts the include and
one unique decoder dispatch, and builds userspace strace. --check compares the
exact generated source/include text without writing. Binary identity is captured
separately in the task evidence. A source-text check alone is not a binary check.

The decoder preserves input argsz, flags, HVA, IOVA and size. It obtains the actual
returned unmap size on syscall exit. Other requests keep ordinary strace handling.
Type1 interpretation is allowed only after observed successful Type1/Type1v2 setup.
Unsupported flags and layouts remain closed by the normalizer. The decoder does
not issue an ioctl itself or claim that an input pointer proves mapping success.

The fixed source-checked output mode is -f -qq -y -X raw with selected path/operation
filters. The normalizer accepts complete newline records with one process ID,
matching opens/closes, raw request IDs and the decoder's exact fields. An FD
reopened after close gets a new container/generation identity. Unknown or duplicated
FDs, failed closes, unproved shared-fd processes, truncated lines, unfinished/resumed
calls, injections, interruptions and unsupported requests invalidate the stream.
Benign version/extension/info requests add no mapping coverage. After setup they
advance the model cutoff. This is a strict subset, not a general strace parser.

The only successful authority here is structural coverage in supplied histories.
It does not bind a container to the physical card, authenticate a log, prove
GPA/IOVA equality, identify effective cache behavior or enable publication. The
GPA is an independent query input. Fixed launcher/device/group identity and a
trusted live handoff remain separate requirements.

The inert C fixture opens only /dev/null, then issues the three requests. All
return ENOTTY. It cannot touch VFIO or a GPU. The built observer captured those
failures with full input fields. Unit success histories modify return strings
in memory only; they are never reported as actual successful ioctls. Production
mode rejects the /dev/null path. Tests perform no ioctl or process tracing.

Reproduce the source build and host tests:

```sh
python3 tools/observer/build.py
python3 tools/observer/build.py --check
python3 tests/test_observer.py
```

A fresh source reconstruction requires the files/URLs in the task source pins.
The owned-child trace command and binary/source hashes are retained in the task
records. The fixture has no guest or hardware role.

The next D0 package must prove group/device association, the realized DMA address
space, ordered live map coverage while the page remains owned, complete observer
output and unchanged topology. It must handle the strict single-process/FD subset
or close its gate before a run. Capture faults and retain native storage until
safe guest termination. Verify the instrumented observer binary and decoder hash,
not just the installed version string. Never accept missing events as evidence of
no changes. The user approved planned hardware stages under ADR 008, but this
host observer alone supplies no S1 success or physical visibility evidence.
