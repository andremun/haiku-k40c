#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Test real memory grant verification with a public test key, never package keys."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.a7 import crypto_sources
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

PROBE = ROOT / "build/tests/mem_session_probe"
# The report follows the current sources. The S1 run kept its own copy in
# work/S1CHANNEL3/host-check.json (a record, not checked again).
OUTPUT = ROOT / "work/S2COPY/host-check.json"
TEST_SEED = bytes.fromhex(
    "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
)
TESTS = (
    "test_mem_client",
    "test_mem_policy",
    "test_mem_channel",
    "test_mem_copy",
    "test_mem_experiment",
    "test_mem_mmu",
    "test_mem_upload",
    "test_mem_faults",
    "test_vram_arena",
)


def sources():
    names = []
    for directory in ("src/memauth", "src/memnative", "src/memstage"):
        names.extend(
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / directory).glob("*")
            if p.suffix in (".h", ".cpp")
        )
    names.extend(
        (
            "src/memory/VramArena.h",
            "src/memory/VramArena.cpp",
            "tests/mem_session_probe.cpp",
            "tests/memstage_device.h",
            "tests/memstage_fifo.h",
            "tools/haiku/selftest/memory_client.cpp",
            "tools/haiku/selftest/memory_preflight.cpp",
            "tools/memstage/host_check.py",
        )
    )
    names.extend("tests/" + name + ".cpp" for name in TESTS)
    return {
        name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        for name in sorted(set(names))
    }


def compile_probe():
    crypto_sources.validate()
    PROBE.parent.mkdir(parents=True, exist_ok=True)
    folder = ROOT / "build/memstage/crypto-host"
    folder.mkdir(parents=True, exist_ok=True)
    objects = []
    for name in crypto_sources.SOURCES:
        target = folder / (name + ".o")
        objects.append(str(target))
        subprocess.run(
            [
                "cc",
                "-O2",
                "-fwrapv",
                "-fno-strict-aliasing",
                "-I" + str(crypto_sources.CACHE / "src"),
                "-c",
                str(crypto_sources.CACHE / "src" / name),
                "-o",
                str(target),
            ],
            check=True,
        )
    subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-Isrc",
            "-fsanitize=undefined",
            "-fno-sanitize-recover=all",
            "tests/mem_session_probe.cpp",
            "src/memauth/Session.cpp",
            "src/memory/VramArena.cpp",
            *objects,
            "-o",
            str(PROBE),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        ["make", "-s", "-C", "tests", *("../build/tests/" + name for name in TESTS)],
        cwd=ROOT,
        check=True,
    )


def report():
    key = Ed25519PrivateKey.from_private_bytes(TEST_SEED)
    public = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    request = subprocess.check_output([str(PROBE), "request"], input=public, timeout=10)
    if len(request) != 256 or request[:16] != b"K40MEMREQ\x01" + bytes(6):
        raise ValueError("unexpected request framing")

    def grant(message):
        return bytes(message) + key.sign(bytes(message))

    message = bytearray(request)
    message[:16] = b"K40MEMRUN\x01" + bytes(6)
    message[192:224] = hashlib.sha256(b"PUBLIC TEST current A7 witness").digest()

    def exercise(raw, fail=-1):
        output = (
            subprocess.check_output(
                [str(PROBE), str(fail)], input=public + raw, timeout=10
            )
            .decode()
            .strip()
        )
        match = re.fullmatch(
            r"passed=(\d) state=(\d) calls=(\d) effects=(\d) retry=0 detached=1 prepared_again=0",
            output,
        )
        if not match:
            raise ValueError("session retry/retention differs: " + output)
        return tuple(map(int, match.groups()))

    good = grant(message)
    if exercise(good) != (1, 3, 1, 8):
        raise ValueError("valid session failed")
    cases = 1
    for offset in (
        0,
        9,
        16,
        48,
        80,
        96,
        104,
        112,
        120,
        128,
        136,
        144,
        152,
        160,
        168,
        176,
        224,
        255,
    ):
        changed = bytearray(message)
        changed[offset] ^= 1
        if exercise(grant(changed)) != (0, 4, 0, 0):
            raise ValueError("accepted stale/wrong/reserved field")
        cases += 1
    changed = bytearray(message)
    changed[192:224] = bytes(32)
    bad = [good[:-1], bytes(320), grant(changed)]
    for offset in (0, 192, 256, 288, 319):
        raw = bytearray(good)
        raw[offset] ^= 128
        bad.append(bytes(raw))
    # Canonicality denial also with otherwise correctly signed message framing.
    raw = bytearray(good)
    raw[288:320] = bytes([255]) * 32
    bad.append(bytes(raw))
    for raw in bad:
        if exercise(raw) != (0, 4, 0, 0):
            raise ValueError("accepted invalid grant")
        cases += 1
    for fail in range(8):
        if exercise(good, fail) != (0, 4, 1, fail):
            raise ValueError("continued effects after runtime failure")
        cases += 1
    outputs = {
        name: subprocess.check_output(
            [str(ROOT / "build/tests" / name)], text=True, timeout=60
        ).strip()
        for name in TESTS
    }
    return dict(
        scope="HOST_ONLY actual crypto/session/client/value-policy/controller; public RFC test seed only",
        signature_cases=cases,
        compiled_exercises=outputs,
        source_sha256=sources(),
        crypto=crypto_sources.validate(),
        claims=dict(
            native_execution=False,
            hardware_execution=False,
            DMA_publication=False,
            S1_complete=False,
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    compile_probe()
    text = json.dumps(report(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if OUTPUT.read_text() != text:
            raise ValueError("memory host report differs")
    else:
        OUTPUT.write_text(text)


if __name__ == "__main__":
    main()
