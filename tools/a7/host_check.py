#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Exercise the real arm authority/owner with simulated MMIO and a PUBLIC test key.

No production key is read. --check runs existing binaries with in-memory frames,
compares deterministic evidence and writes nothing. Generation compiles host
fixtures and writes one source-bound report. No VM, device or hardware access.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
from tools.a7 import crypto_sources
from tools.a7 import build
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

PROBE = ROOT / "build/tests/a7_owner_probe"
OUTPUT = ROOT / "work/S1A7BUFFER/host-check.json"
# Public RFC 8032 TEST 1 seed. Never used by package creation or the live signer.
TEST_SEED = bytes.fromhex(
    "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
)
SOURCES = (
    *build.CORE,
    "src/a7/Owner.cpp",
    "src/a7/ArmAuthority.cpp",
    "tests/a7_owner_probe.cpp",
    "tests/native_arm_gate.cpp",
    "tools/a7/host_check.py",
)


def compile_probe():
    crypto_sources.validate()
    subprocess.run(
        [
            "make",
            "-s",
            "-C",
            "tests",
            "../build/tests/test_a7_native",
            "../build/tests/test_a7_client",
        ],
        cwd=ROOT,
        check=True,
    )
    objects = []
    folder = ROOT / "build/a7/crypto-host"
    folder.mkdir(parents=True, exist_ok=True)
    for name in crypto_sources.SOURCES:
        obj = folder / (name + ".o")
        objects.append(str(obj))
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
                str(obj),
            ],
            check=True,
        )
    subprocess.run(
        [
            "g++",
            "-std=c++17",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-fsanitize=undefined",
            "-fno-sanitize-recover=all",
            "-Isrc",
            "-Itests",
            "tests/a7_owner_probe.cpp",
            *[x for x in SOURCES if x.endswith(".cpp") and not x.startswith("tests/")],
            *objects,
            "-o",
            str(PROBE),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            "tools/haiku/kcc",
            "-Werror",
            "-Isrc",
            "-c",
            "tests/native_arm_gate.cpp",
            "-o",
            "build/a7/native-arm-gate.o",
        ],
        cwd=ROOT,
        check=True,
    )


def run(mode, grant=None, profile=0, strap=0):
    return subprocess.check_output(
        [str(PROBE), str(build.ROM), mode, str(profile), str(strap)], input=grant
    )


def render():
    boundaries = {
        name: subprocess.check_output(
            [str(ROOT / "build/tests" / name)], text=True
        ).strip()
        for name in ("test_a7_native", "test_a7_client")
    }
    request = run("request")
    if len(request) != 128 or request[:8] != b"K40A7REQ":
        raise ValueError("native arm request differs")
    base = bytearray(request)
    base[:8] = b"K40A7ARM"
    base[72:80] = base[56:64]
    base[80:112] = hashlib.sha256(b"SYNTHETIC HOST PROOF; NO VFIO").digest()
    key = Ed25519PrivateKey.from_private_bytes(TEST_SEED)

    def signed(message):
        return bytes(message) + key.sign(bytes(message))

    valid = signed(base)
    scenarios = []
    for profile in range(2):
        for strap in range(16):
            result = run("run", valid, profile, strap).decode().strip()
            scenarios.append(dict(profile=profile, strap=strap, result=result))
    successful = [x for x in scenarios if x["result"].startswith("status 0 ")]
    if not successful:
        raise ValueError("no physical-permit owner fixture completed")
    chosen = successful[0]
    for offset in range(192):
        changed = bytearray(valid)
        changed[offset] ^= 1
        result = run("reject", bytes(changed)).decode()
        if not result.startswith("status 4 ") or " writes 0 " not in result:
            raise ValueError("mutated grant admitted")
    for offset in (16, 48, 56, 64, 72, 112):
        changed = bytearray(base)
        changed[offset] ^= 1
        result = run("reject", signed(changed)).decode()
        if not result.startswith("status 4 ") or " writes 0 " not in result:
            raise ValueError("wrong scoped grant admitted")
    changed = bytearray(base)
    changed[80:112] = bytes(32)
    if not run("reject", signed(changed)).startswith(b"status 4 "):
        raise ValueError("empty proof admitted")
    changed = bytearray(valid)
    scalar = (
        int.from_bytes(changed[160:192], "little")
        + 2**252
        + 27742317777372353535851937790883648493
    )
    changed[160:192] = scalar.to_bytes(32, "little")
    if not run("reject", bytes(changed)).startswith(b"status 4 "):
        raise ValueError("noncanonical signature admitted")
    faults = {
        name: run(name, valid, chosen["profile"], chosen["strap"]).decode().strip()
        for name in ("pins-fail", "clock-fail", "trace-overflow")
    }
    if any(value.startswith("status 0 ") for value in faults.values()):
        raise ValueError("fault fixture passed")
    i2c_cases = {
        name: run(name, valid, chosen["profile"], chosen["strap"]).decode().strip()
        for name in (
            "sensor-address-nack",
            "sensor-register-nack",
            "sensor-value-nack",
            "sensor-stop-fail",
            "sensor-stretch",
            "sensor-timeout",
            "other-address-nack",
            "sensor-io",
        )
    }
    if not i2c_cases["sensor-address-nack"].startswith("status 0 ") or any(
        value.startswith("status 0 ")
        for name, value in i2c_cases.items()
        if name != "sensor-address-nack"
    ):
        raise ValueError("I2C policy fixture outcome differs")
    names = set(SOURCES) | {
        "tests/i2c_wire.h",
        "tests/board_fake.h",
        "tests/test_a7_native.cpp",
        "tests/test_a7_client.cpp",
        "src/a7/NativePlatform.cpp",
        "src/os/HaikuMemory.cpp",
        "src/os/HaikuMemory.h",
        "src/os/HaikuBackend.h",
        "tools/haiku/selftest/a7_client.cpp",
        "tests/Makefile",
    }
    for folder in ("tests/a7_shim", "tests/os_shim"):
        names.update(str(p.relative_to(ROOT)) for p in (ROOT / folder).glob("*.h"))
    for folder in ("src/a7", "src/memory", "src/devinit", "src/runtime"):
        names.update(str(p.relative_to(ROOT)) for p in (ROOT / folder).glob("*.h"))
    return (
        json.dumps(
            dict(
                scope="HOST simulation of physical-permit code; NO hardware proof",
                native_boundaries=boundaries,
                verifier=crypto_sources.validate(),
                boundary_binary_sha256={
                    name: build.sha(ROOT / "build/tests" / name)
                    for name in sorted(boundaries)
                },
                successful_cases=len(successful),
                scenarios=scenarios,
                mutation_rejections=192,
                signed_scope_rejections=7,
                noncanonical_signature_rejections=1,
                faults=faults,
                i2c_policy_cases=i2c_cases,
                fixture_key="RFC 8032 public TEST 1; never a production key",
                source_sha256={name: build.sha(ROOT / name) for name in sorted(names)},
                probe_sha256=build.sha(PROBE),
                native_gate_object_sha256=build.sha(
                    ROOT / "build/a7/native-arm-gate.o"
                ),
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        compile_probe()
    expected = render()
    if args.check:
        return 0 if OUTPUT.is_file() and OUTPUT.read_text() == expected else 1
    OUTPUT.write_text(expected)
    print("A7 owner/authentication host checks pass; no physical execution")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
