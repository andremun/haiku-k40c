# Cardless native owner reload — 2026-10-27

PASS in 52.57 seconds. Source commit: 45923d6.
No GPU or host device was attached. This is Haiku OS evidence only.

Command:

```sh
python3 tools/haiku/cardless_run.py --kvm \
  --driver build/haiku/k40_owner_probe --owner-module build/haiku/k40_owner_module
```

The probe verified host pattern readback, aligned GPA, clean release and denied
publication. Client 1 then consumed the software startup latch and retained
allocation token 2. Its uninit detached lease 1 into quarantine. A separate
client initialization acquired lease 2 and observed token 2, Failed state,
one owned record and one quarantine record. A second startup/allocation was
refused. Its uninit detached successfully while retaining the record.
Serial lines record both actual init/uninit pairs and the legacy reload.

The uploaded guest kernel matches the link kernel's source image. Binary and
kernel hashes are in launch.json and hashes.log. The raw kernel and binaries
remain in the ignored run folder, not this archive. Launch options, guest job,
environment, HTTP transfers and serial output are preserved here.

This proves the tested module/client lifetime path on hrev60207. It does not
prove DMA, device IOVA, failed delete_area recovery, arbitrary client concurrency,
GPU access or a production executor integration. No retry was performed.
