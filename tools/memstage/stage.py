# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Stage of the combined memory package: S1 (host NOP) or S2 (NOP, then one copy).

The environment variable K40_MEM_STAGE selects it: "s1" (default), "s2", "s2d"
(the diagnostic variant of s2), "s3a"
(GR engine start and golden context) or "s3b" (also one compute job). "s3c" and
"s3d" fetch only a prefix of the s3b push buffer: the object bind, or the set-up
without the launch (work/S3DIAG/PLAN.md). "s3g" is s3a with the golden image
printed (work/S3DIAG/REPORT.md). "s3o" is s3e with the progress after GP_PUT
observed without BAR1 access (work/S3DIAG/REPORT.md, approach B).
One stage has one package folder, one work folder and one pass marker. The
native owner receives the choice through the generated mem_config.h.
"""
import os

STAGES = {
    "s1": dict(
        # Ladder rung 2 repeats S1 with a new package. package-s1c and
        # work/S1CHANNEL3 hold the consumed package of the S1 pass of
        # 2026-10-31: keep them unchanged (build.py refuses a consumed package).
        package="package-s1-ladder",
        work="LADDER/s1",
        copy=False,
        number=0,
        marker="PASS S1_CHANNEL_NOP",
        allocations=14,
        title="Combined S1 channel run",
        scope="S1: one host NOP consumed on one CE0-runlist channel (GP_GET 0->1), no fault, clean teardown; no DMA payload proof",
    ),
    "s2": dict(
        package="package-s2",
        work="S2COPY",
        copy=True,
        number=1,
        marker="PASS S2_COPY",
        allocations=16,
        title="Combined S2 copy run",
        scope="S2: after the S1 NOP, one 4096-byte copy between two owned VRAM pages on the same CE0-runlist channel, destination equal to source, no fault, clean teardown; no host DMA payload proof",
    ),
    "s2d": dict(
        package="package-s2d",
        work="S2COPY/diagnostic",
        copy=True,
        number=4,
        marker="PASS S2_COPY_DIAGNOSTIC",
        allocations=16,
        title="Combined S2 copy run, diagnostic variant",
        scope="S2 diagnostic: as S2, but the copy-engine busy bit is recorded and not part of the pass rule; destination equal to source by slow-window readback",
    ),
    "s3a": dict(
        package="package-s3a",
        work="S3GR",
        copy=False,
        number=2,
        marker="PASS S3_GOLDEN",
        allocations=27,
        title="Combined S3 golden-context run",
        scope="S3a: GR engine started, FECS and GPCCS running, golden context generated and attached to one channel of the GR runlist, no fault, clean teardown; no compute job",
    ),
    "s3b": dict(
        # The rung 5 package (package-s3b, work/S3LAUNCH) is consumed: keep it
        # unchanged. This package adds the live progress lines (work/S3DIAG/PLAN.md).
        package="package-s3b-diag",
        work="S3DIAG/s3b",
        copy=False,
        number=3,
        marker="PASS S3_COMPUTE",
        allocations=27,
        title="Combined S3 compute run",
        scope="S3: one compute job on the card, out[i] = in[i] + 1 for 1024 elements, every element checked by slow-window readback, no fault, clean teardown; no host DMA payload proof",
    ),
    "s3c": dict(
        package="package-s3c",
        work="S3DIAG/s3c",
        copy=False,
        number=5,
        marker="PASS S3_BIND",
        allocations=27,
        title="Combined S3 object-bind run",
        scope="S3c: as S3a, then one GPFIFO entry of 2 push words (compute object bind) consumed (GP_GET 0->1), no fault, clean teardown; no launch",
    ),
    "s3e": dict(
        package="package-s3e",
        work="S3DIAG/s3e",
        copy=False,
        number=7,
        marker="PASS S3_BIND",
        allocations=27,
        title="Combined S3 object-bind run, aligned with the Linux reference run",
        scope="S3e: as S3c, with the channel's own copy of the golden image, PRIV PTEs for page pool, bundle and register list, and a user channel (RAMFC 0xe4 = 0); object bind consumed (GP_GET 0->1), no fault, clean teardown; no launch",
    ),
    "s3g": dict(
        package="package-s3g",
        work="S3DIAG/s3g",
        copy=False,
        number=8,
        marker="PASS S3_IMAGE",
        allocations=27,
        title="Combined S3 golden-context run with the image printed",
        scope="S3g: as S3a, and the golden image (0x4ea00 bytes) read by slow window and printed for the comparison with the Linux reference image; no submission, no fault, clean teardown; no compute job",
    ),
    "s3o": dict(
        package="package-s3o",
        work="S3DIAG/s3o",
        copy=False,
        number=9,
        marker="PASS S3_OBSERVE",
        allocations=27,
        title="Combined S3 object-bind run, observed through BAR0",
        scope="S3o: as S3e, and after GP_PUT the progress read through BAR0 status registers and the slow window only, each group printed at once; one BAR1 read of GP_GET as the last action; object bind consumed (GP_GET 0->1), no fault, clean teardown; no launch",
    ),
    "s3d": dict(
        package="package-s3d",
        work="S3DIAG/s3d",
        copy=False,
        number=6,
        marker="PASS S3_SETUP",
        allocations=27,
        title="Combined S3 compute set-up run",
        scope="S3d: as S3a, then one GPFIFO entry of the 100 set-up push words (no launch) consumed (GP_GET 0->1), no fault, clean teardown; no launch",
    ),
}
NAME = os.environ.get("K40_MEM_STAGE", "s1")
if NAME not in STAGES:
    raise ValueError("K40_MEM_STAGE must be one of: " + ", ".join(STAGES))
CURRENT = STAGES[NAME]
