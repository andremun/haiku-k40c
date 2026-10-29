#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Verify and report the one approved batch-1 capture. Never launches or signs."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/haiku"))
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from tools.memstage import evidence, pci
from tools.a7.run import serial_valid
from tools.observer.task_stream import TaskStream

CAPTURE = ROOT / "results/20261030-batch1-a7-bar1-ec8db47d"
OUTPUT = ROOT / "work/S1BATCH1RUN/report.json"
DOCUMENT = ROOT / "docs/S1-BATCH1-RUN-REVIEW.md"
RECEIPT = ROOT / "work/S1BATCH1RUN/consumed.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(value):
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def report():
    folder = CAPTURE
    launch = json.loads((folder / "launch.json").read_text())
    suite = launch["suite"]
    result = json.loads((folder / "result.json").read_text())
    teardown = json.loads((folder / "teardown.json").read_text())
    require(
        result["status"] == "pass"
        and not result["error"]
        and not result["S1_complete"],
        "launcher did not pass finite scope",
    )
    require(
        launch["source_commit"] == "acb2aca3cca9f168ae0927ba0269042cc652ad59",
        "wrong approved source commit",
    )
    require(
        (
            launch["host"]["bdf"] == "0000:04:00.0"
            if "bdf" in launch["host"]
            else "vfio-pci,host=0000:04:00.0" in launch["args"]
        ),
        "wrong card",
    )
    require(
        launch["timeout_seconds"] == 600 and result["elapsed_seconds"] < 600,
        "guest deadline",
    )
    require(
        teardown["host_pci_command_after"] == 2
        and teardown["bus_master_enable"] is False,
        "bus mastering/teardown not confirmed",
    )
    before = (folder / "kernel-before.log").read_bytes()
    after = (folder / "kernel-after.log").read_bytes()
    require(
        before == after and result["allowed_kernel_lines"] == [],
        "R5 selected stream changed or allowance used",
    )
    serial = (folder / "serial.log").read_text(errors="replace")
    request = (folder / "a7/request.bin").read_bytes()
    grant = (folder / "a7/grant.bin").read_bytes()
    serial_valid(serial, True, request, suite["A7"])
    require(
        len(grant) == 192 and grant[:16] == b"K40A7ARM\x01" + bytes(7),
        "A7 grant framing",
    )
    require(
        grant[16:72] == request[16:72]
        and grant[72:80] == request[56:64]
        and grant[112:128] == request[112:128],
        "A7 grant binding",
    )
    require(
        grant[80:112]
        == hashlib.sha256((folder / "a7/cutoff.json").read_bytes()).digest(),
        "A7 mapping proof digest",
    )
    Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(suite["A7"]["public_key_hex"])
    ).verify(grant[128:], grant[:128])
    cutoff = json.loads((folder / "a7/cutoff.json").read_text())
    trace = (folder / "trace.log").read_bytes()
    require(trace.endswith(b"\n"), "partial final observer trace")
    require(
        cutoff["trace_prefix_sha256"]
        == hashlib.sha256(trace[: cutoff["trace_prefix_bytes"]]).hexdigest(),
        "arm cutoff trace changed",
    )
    monitor = launch["args"][launch["args"].index("-monitor") + 1]
    root = Path(monitor.removeprefix("unix:").split(",")[0]).parent.name
    processes = json.loads((folder / "processes.json").read_text())
    stream = TaskStream(
        root,
        processes["qemu_pid"],
        int(launch["host"]["group"]),
        target=str(Path(suite["qemu"]["path"]).resolve()),
    )
    prefix = trace[: cutoff["trace_prefix_bytes"]]
    require(prefix.endswith(b"\n"), "partial arm trace cutoff")
    for line in prefix.splitlines(keepends=True):
        require(
            stream.feed(line.decode("ascii")), "arm trace replay: " + str(stream.error)
        )
    witness = stream.coverage(
        gpa=cutoff["gpa"], iova=cutoff["iova"], size=cutoff["bytes"]
    )
    require(
        witness is not None
        and witness.mapping.identity.generation == cutoff["generation"],
        "arm coverage replay differs",
    )
    attestation = json.loads((folder / "memory-attestation.json").read_text())
    memory_prefix = attestation["trace_prefix_bytes"]
    require(
        memory_prefix >= len(prefix)
        and trace[:memory_prefix].endswith(b"\n")
        and hashlib.sha256(trace[:memory_prefix]).hexdigest()
        == attestation["trace_prefix_sha256"],
        "memory trace cutoff changed",
    )
    for line in trace[len(prefix) : memory_prefix].splitlines(keepends=True):
        require(
            stream.feed(line.decode("ascii")),
            "memory trace replay: " + str(stream.error),
        )
    require(stream.current(witness), "arm extent not current at memory grant")
    for line in trace[memory_prefix:].splitlines(keepends=True):
        require(
            stream.feed(line.decode("ascii")),
            "final trace replay: " + str(stream.error),
        )
    raw = (folder / "request.bin").read_bytes()
    signed = (folder / "grant.bin").read_bytes()
    resources = pci.resources(json.loads((folder / "pci-before.json").read_text()))
    fields = evidence.request_fields(raw, suite, serial, resources)
    require(
        pci.resources(json.loads((folder / "pci-after.json").read_text()))
        == resources
        == attestation["pci"],
        "BAR resources changed",
    )
    require(
        attestation["native"] == fields
        and attestation["plan_sha256"] == suite["plan_sha256"],
        "memory resource/plan binding",
    )
    for name, path in (
        ("a7_request_sha256", "a7/request.bin"),
        ("a7_grant_sha256", "a7/grant.bin"),
        ("cutoff_sha256", "a7/cutoff.json"),
        ("a7_serial_prefix_sha256", "a7-serial-prefix.txt"),
        ("memory_request_sha256", "request.bin"),
        ("pci_raw_sha256", "pci-before.json"),
    ):
        require(
            attestation[name] == sha(folder / path),
            "attestation file mismatch: " + name,
        )
    require(
        attestation["kernel_selected_sha256"] == hashlib.sha256(before).hexdigest(),
        "R5 attestation snapshot differs",
    )
    require(
        len(signed) == 320
        and signed[:16] == b"K40MEMRUN\x01" + bytes(6)
        and signed[16:192] == raw[16:192]
        and signed[224:256] == raw[224:256],
        "memory grant framing/binding",
    )
    require(
        signed[192:224]
        == hashlib.sha256((folder / "memory-attestation.json").read_bytes()).digest(),
        "memory attestation digest",
    )
    Ed25519PublicKey.from_public_bytes(bytes.fromhex(suite["public_key_hex"])).verify(
        signed[256:], signed[:256]
    )
    observed = evidence.memory_final(serial, suite, raw)
    require(
        observed == json.loads((folder / "memory-observations.json").read_text()),
        "memory observations differ",
    )
    marker = json.loads(RECEIPT.read_text())
    require(
        Path(marker["evidence"]).name == folder.name
        and marker["stage"] == result["stage"]
        and marker["package_sha256"]
        == hashlib.sha256(dump(suite).encode()).hexdigest(),
        "consumed marker missing/different",
    )

    def pair(name):
        matches = re.findall(
            r"^k40_a7: " + re.escape(name) + r" a=0x([0-9a-f]+) b=0x([0-9a-f]+)\r?$",
            serial,
            re.M,
        )
        require(len(matches) == 1, "missing/repeated A7 value " + name)
        return [int(v, 16) for v in matches[0]]

    mappings = re.findall(r"^k40_mem: MAP ([^\r\n]+)", serial, re.M)
    witnesses = re.findall(
        r"^k40_mem: EVENT phase=(\d+) error=0 offset=([0-9a-f]+) value=([0-9a-f]+) polls=0 elapsed=(\d+) operation=7 role=(\d+) detail=1\r?$",
        serial,
        re.M,
    )
    return dict(
        status="PASS",
        verification="KNOWN / HARDWARE_VERIFIED on 04:00.0 under Haiku for the finite A7/BAR1 scope",
        source_commit=launch["source_commit"],
        package_sha256=marker["package_sha256"],
        elapsed_seconds=result["elapsed_seconds"],
        command="python3 tools/memstage/run.py --run-approved-batch1-once",
        A7=dict(
            post=pair("POST_RESULT"),
            arm_before=pair("ARM_BEFORE"),
            post_readback=pair("ARM_READBACK"),
            arm_after=pair("ARM_AFTER"),
            timer=pair("TIMER"),
            vram_bytes=pair("VRAM_BYTES"),
            scratch=pair("SCRATCH_PASS"),
        ),
        memory=observed,
        mapping_requests=mappings,
        pci=resources,
        witness_records=[
            dict(
                phase=int(p),
                virtual=int(v, 16),
                fingerprint=int(h, 16),
                elapsed_us=int(t),
                role=int(r),
            )
            for p, v, h, t, r in witnesses
        ],
        kernel=dict(
            scope="R5 selected classes only; not full kernel log cleanliness",
            before_bytes=len(before),
            after_bytes=len(after),
            delta_bytes=0,
            allowed_kernel_lines=[],
            sha256=hashlib.sha256(before).hexdigest(),
        ),
        teardown=teardown,
        bounds=dict(
            S1_complete=False,
            channel_translation=False,
            PBDMA_fetch=False,
            DMA_payload_visibility=False,
            UC_effective_type_measured=False,
            Q7="open",
            Q11="open",
        ),
        source_sha256=sha(Path(__file__)),
        consumed_receipt_sha256=sha(RECEIPT),
        capture_sha256={
            p.relative_to(folder).as_posix(): sha(p)
            for p in sorted(folder.rglob("*"))
            if p.is_file()
        },
    )


def document(value):
    a = value["A7"]
    return f"""# Approved batch-1 run: A7 and BAR1 pass

2026-10-30. One approved launch of package acb2aca. Result: PASS in
{value['elapsed_seconds']} seconds. No retry. The consumed marker remains.
Capture: `results/{CAPTURE.name}/`. Public package SHA-256:
`{value['package_sha256']}`. Command:
`{value['command']}`.

## KNOWN / HARDWARE_VERIFIED scope under Haiku

A7 completed POST and readiness with its unchanged run7 code. The timer advanced,
VRAM size was {a['vram_bytes'][0]//1048576} MiB and scratch passed. The owned host
flush page was armed at `0x{a['arm_before'][0]:x}`. Post-POST 0x100c10 readback
was `0x{a['post_readback'][0]:x}`; the original re-arm ran. Q11 remains open.

The distinct memory grant passed current A7/mapping/resource checks. Public-key
signature checks and observer replay pass offline. BAR0 requested explicit UC
for its 8 MiB view; BAR1 requested explicit UC/read-only for an 8 KiB prefix of
the discovered 256 MiB aperture. Accepted requests are recorded; effective
PAT/MTRR/cache type was not independently measured.

The source-derived arena retained seven owned objects, including both zeroed
debug allocations and its PGD/SPT/instance. Full physical patterns/complements
passed. The gk104 BAR1 context then verified these complete pages:

| Check | VA 0 | VA 0x1000 |
|---|---|---|
| Initial mapping | A at VRAM 0x81000 | B at VRAM 0x82000 |
| Remap and targeted invalidate | B | B |
| Restore and targeted invalidate | A | B |

Six per-page checksum records follow full word-by-word comparisons. There were
three PDB-specific invalidations and 17 sourced BAR flushes. BAR1 context writes
were `0x800000d3` (enable) and `0x000000d3` (owned enable cleared).
All per-phase selected guest fault snapshots passed, the IO policy reported no
rejection, and all allocations remained staged/referenced/retained through exit.
BAR2 was not used. This witnesses this BAR1 path and mapping update on this card.

## Host closure and limits

The selected R5 stream is byte-identical before/after ({value['kernel']['before_bytes']}
bytes each). Delta: zero bytes; allowed kernel lines: none. This is selected-class
coverage, not proof of a clean full kernel log. Owned QEMU/tracer termination
passed. Host PCI command after exit was `0x0002`: bus mastering was off. No manual
reset, binding change or other-card access was performed.

S1 is still incomplete. No channel translation, PBDMA fetch, command submission,
compute job, generic host DMA publication or live reuse/retire contract is proven.
Q7 and Q11 remain open. S2/S3 success prerequisites are not met. Another write
stage/run requires a separately reviewed package and explicit user approval.

## Review inputs

`work/S1BATCH1RUN/report.json` binds the raw captures and deterministic offline
verification. Its `consumed.json` preserves a copy of the launch receipt; the live
marker is unchanged. `launch.json` records the exact command, source/artifact/kernel/ROM
hashes, fixed card and host prerequisites. The immutable `a7/` capture records
its fresh structural witness; `memory-attestation.json`, `pci-before/after.json`
and `memory-observations.json` bind the separate BAR1 phase. Raw serial, observer,
kernel before/after and teardown records are retained unchanged.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check and not RECEIPT.exists():
        # Preserve the receipt for offline review. Never change the live marker.
        marker = ROOT / "build/memstage/package/consumed.json"
        with RECEIPT.open("xb") as target:
            target.write(marker.read_bytes())
    value = report()
    outputs = {OUTPUT: dump(value), DOCUMENT: document(value)}
    for path, text in outputs.items():
        if args.check:
            require(path.read_text() == text, "result report differs: " + str(path))
        else:
            path.write_text(text)
    print(
        "Approved batch-1 capture, signatures, replay and finite BAR1 observations pass; S1 remains open."
    )


if __name__ == "__main__":
    main()
