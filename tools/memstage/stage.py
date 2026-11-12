# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Stage of the combined memory package: S1 (host NOP) or S2 (NOP, then one copy).

The environment variable K40_MEM_STAGE selects it: "s1" (default) or "s2".
One stage has one package folder, one work folder and one pass marker. The
native owner receives the choice through the generated mem_config.h.
"""
import os

STAGES = {
    "s1": dict(
        package="package-s1c",
        work="S1CHANNEL3",
        copy=False,
        marker="PASS S1_CHANNEL_NOP",
        allocations=14,
        title="Combined S1 channel run",
        scope="S1: one host NOP consumed on one CE0-runlist channel (GP_GET 0->1), no fault, clean teardown; no DMA payload proof",
    ),
    "s2": dict(
        package="package-s2",
        work="S2COPY",
        copy=True,
        marker="PASS S2_COPY",
        allocations=16,
        title="Combined S2 copy run",
        scope="S2: after the S1 NOP, one 4096-byte copy between two owned VRAM pages on the same CE0-runlist channel, destination equal to source, no fault, clean teardown; no host DMA payload proof",
    ),
}
NAME = os.environ.get("K40_MEM_STAGE", "s1")
if NAME not in STAGES:
    raise ValueError("K40_MEM_STAGE must be s1 or s2")
CURRENT = STAGES[NAME]
