# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Stage of the combined memory package: S1 (host NOP) or S2 (NOP, then one copy).

The environment variable K40_MEM_STAGE selects it: "s1" (default), "s2", "s2d"
(the diagnostic variant of s2), "s3a"
(GR engine start and golden context) or "s3b" (also one compute job).
One stage has one package folder, one work folder and one pass marker. The
native owner receives the choice through the generated mem_config.h.
"""
import os

STAGES = {
    "s1": dict(
        package="package-s1c",
        work="S1CHANNEL3",
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
        allocations=26,
        title="Combined S3 golden-context run",
        scope="S3a: GR engine started, FECS and GPCCS running, golden context generated and attached to one channel of the GR runlist, no fault, clean teardown; no compute job",
    ),
    "s3b": dict(
        package="package-s3b",
        work="S3LAUNCH",
        copy=False,
        number=3,
        marker="PASS S3_COMPUTE",
        allocations=26,
        title="Combined S3 compute run",
        scope="S3: one compute job on the card, out[i] = in[i] + 1 for 1024 elements, every element checked by slow-window readback, no fault, clean teardown; no host DMA payload proof",
    ),
}
NAME = os.environ.get("K40_MEM_STAGE", "s1")
if NAME not in STAGES:
    raise ValueError("K40_MEM_STAGE must be s1, s2, s2d, s3a or s3b")
CURRENT = STAGES[NAME]
