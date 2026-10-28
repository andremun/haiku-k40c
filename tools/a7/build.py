#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Build the fixed A7 package without starting a guest or touching a device.

Reads the exact private ROM, pinned verifier and matching Haiku toolchain.
Creates one private package key and build-only config. --check compares generated
config, inventories and public metadata exactly, writes nothing and starts nothing.
"""
import argparse
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import stat
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tools/haiku"))
from tools.a7 import crypto_sources, omissions
import devinit_preflight
import post_policy
import probe_stage
from board_trace import read_policy, ADR

PACKAGE = ROOT / "build/a7/package-review-nits"
PUBLIC = ROOT / "work/S1A7NITS/package.json"
INVENTORY = ROOT / "work/S1A7NITS/write-inventory.json"
ROM = Path(
    os.environ.get(
        "K40_VBIOS",
        str(Path.home() / "mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom"),
    )
).expanduser()
CORE = (
    "src/devinit/PostImage.cpp",
    "src/devinit/BoardPolicy.cpp",
    "src/devinit/Sha256.cpp",
    "src/devinit/BoundPost.cpp",
    "src/devinit/BoardCore.cpp",
    "src/devinit/Interpreter.cpp",
    "src/devinit/I2c.cpp",
    "src/runtime/PreStart.cpp",
    "src/runtime/Bootstrap.cpp",
    "src/memory/ArmedReference.cpp",
)
OWNER = (
    *CORE,
    "src/os/HaikuBackend.c",
    "src/os/HaikuMemory.cpp",
    "src/a7/ArmAuthority.cpp",
    "src/a7/Owner.cpp",
    "src/a7/NativePlatform.cpp",
    "src/a7/Module.cpp",
)
CLIENT = ("tools/haiku/selftest/a7_client.cpp",)
ARTIFACTS = {
    "license": PACKAGE / "ed25519-license.txt",
    "owner": ROOT / "build/haiku/k40_a7_owner_module",
    "client": ROOT / "build/haiku/k40_a7_stage",
    "identity": ROOT / "build/haiku/k40_identity_probe",
    "observer": ROOT / "build/observer/strace-source/src/strace",
    "qemu": Path("/usr/bin/qemu-system-x86_64"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(value):
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def inputs():
    data = ROM.read_bytes()
    if (
        len(data) != 181760
        or hashlib.sha256(data).hexdigest() != devinit_preflight.EXPECTED
    ):
        raise ValueError("wrong approved ROM")
    capture = ROOT / "reference/linux-run-debug/dmesg.txt.xz"
    totals = set(
        int(x)
        for x in re.findall(r"fb: Total:\s*(\d+) MiB", lzma.open(capture, "rt").read())
    )
    if len(totals) != 1:
        raise ValueError("physical FB size capture missing/ambiguous")
    return data, totals.pop() * 1024**2, capture


def key_inputs():
    private = PACKAGE / "host-key.pem"
    info = private.lstat()
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o600
    ):
        raise ValueError("host signing key must be a private owned regular file")
    der = subprocess.check_output(
        ["openssl", "pkey", "-in", str(private), "-pubout", "-outform", "DER"]
    )
    # RFC 8410 Ed25519 SubjectPublicKeyInfo, no private bytes are printed.
    if len(der) != 44 or der[:12] != bytes.fromhex("302a300506032b6570032100"):
        raise ValueError("wrong signing key type")
    if der[12:] == bytes.fromhex(
        "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
    ):
        raise ValueError("public test key forbidden in production package")
    nonce = (PACKAGE / "nonce.bin").read_bytes()
    if len(nonce) != 32 or not any(nonce):
        raise ValueError("wrong package nonce")
    return der[12:], nonce


def config(data, public, nonce, total):
    def array(name, values):
        rows = [
            ",".join("0x%02x" % b for b in values[i : i + 24])
            for i in range(0, len(values), 24)
        ]
        return (
            "static constexpr uint8_t " + name + "[]={\n" + ",\n".join(rows) + "\n};\n"
        )

    return (
        "// Private generated A7 build input. Do not distribute firmware or keys.\n#include <cstdint>\n"
        + array("a7PublicKey", public)
        + array("a7PackageNonce", nonce)
        + array("a7Rom", data)
        + "static constexpr uint64_t a7ExpectedVram="
        + str(total)
        + "ULL;\n"
    )


def inventory(data):
    policy = read_policy(ADR.read_text())
    approved = {
        (pc, op)
        for identity, pc, op in policy
        if identity == devinit_preflight.EXPECTED
    }
    allowed, code = post_policy.permissions(data, approved)
    potential, _ = post_policy.permissions(
        data, {(pc, op) for pc, op in code.items() if op in (0x69, 0x3A, 0x4D)}
    )
    if any(reg == 0x100C10 and write for _, reg, _, write in potential):
        raise ValueError("ROM can write flush target; reviewed premise differs")
    script = [
        dict(
            pc=hex(pc),
            opcode=hex(code[pc]),
            register=hex(reg),
            width=width,
            authorized=(pc, reg, width, write) in allowed,
            value="derived by opcode from immutable ROM/current register state",
        )
        for pc, reg, width, write in sorted(potential)
        if write
    ]
    pin_regs = sorted(
        {
            reg
            for pc, reg, width, write in allowed
            if code[pc] == 0x4D and write and width == 4
        }
    )
    if len(pin_regs) != 1:
        raise ValueError("dedicated I2C preinit pin ambiguous")
    driver = [
        dict(
            register="0x140/0x144",
            width=4,
            values="0",
            phase="interrupt unarm",
            source="mc/nv04.c:87-90",
        ),
        dict(
            register="0x6013d4/0x6013d5",
            width=1,
            values="index 0x1f, index 0x3f, data 0x57",
            phase="CRTC unlock",
            source="disp/vga.c:97-107,130-135",
        ),
        dict(
            register="0x122318/0x12231c/0x122310/0x122348/0x1223b0/0x122358",
            width=4,
            values="source-backed masked private-ring settings",
            phase="private ring",
            source="privring/gk104.c:103-109",
        ),
        dict(
            register=hex(pin_regs[0]),
            width=4,
            values="7",
            phase="dedicated I2C initialization",
            source="i2c/busgf119.c:69,93",
        ),
        dict(
            register="0x100c10",
            width=4,
            values="current witnessed IOVA >> 8",
            phase="before POST AND after POST readback",
            source="fb/base.c:227,204; fb/gf100.c:83",
        ),
        dict(
            register="0x200",
            width=4,
            values="mask bit 0x100 off then on",
            phase="FIFO preinit reset",
            source="mc/nv04.c:39,47,49; mc/gk104.c:28",
        ),
        dict(
            register="0x1700",
            width=4,
            values="0",
            phase="owned scratch selector",
            source="instmem/nv50.c:62-91; fb/ramgf100.c:497",
        ),
        dict(
            register="0x740000/0x740100/0x740ffc",
            width=4,
            values="two software pattern passes",
            phase="owned scratch",
            source="instmem/nv50.c:62-91; fb/ramgf100.c:497,555-558",
        ),
        dict(
            register="0x70000",
            width=4,
            values="1, poll bit 1 clear",
            phase="post-POST scratch flush",
            source="bar/g84.c:29-40",
        ),
    ]
    driver[2]["values"] = [
        dict(register=hex(reg), mask="0x3ffff", value=hex(value))
        for reg, value in (
            (0x122318, 0x1000),
            (0x12231C, 0x200),
            (0x122310, 0x800),
            (0x122348, 0x100),
            (0x1223B0, 0xFFF),
            (0x122348, 0x200),
            (0x122358, 0x2880),
        )
    ]
    driver[7][
        "values"
    ] = "pattern = uint32((VRAM_address >> 2) xor (VRAM_address >> 34)) * 0x9e3779b9 modulo 2^32; second pass complements every word"
    return dict(
        rom_sha256=devinit_preflight.EXPECTED,
        scope="conservative possible writes, not an executed path",
        script=script,
        driver=driver,
        deliberate_linux_preinit_omissions=omissions.inventory(data, pin_regs[0]),
        script_flush_target_writes=0,
        dedicated_pin=hex(pin_regs[0]),
        denied_script_writes=sum(not row["authorized"] for row in script),
    )


def source_names():
    names = set(
        (
            *OWNER,
            *CLIENT,
            "tools/a7/build.py",
            "tools/a7/run.py",
            "tools/a7/crypto_sources.py",
            "tools/a7/omissions.py",
            "tools/a7/teardown_sources.py",
            "tools/a7/host_check.py",
            "tests/a7_owner_probe.cpp",
            "tests/native_arm_gate.cpp",
            "tests/test_a7_native.cpp",
            "tests/test_a7_client.cpp",
            "tests/test_a7_run.py",
            "tests/test_a7_omissions.py",
            "tools/devinit_preflight.py",
            "tools/post_policy.py",
            "tools/board_trace.py",
            "docs/decisions/004-board-operations-and-review.md",
            "tools/haiku/d0_run.py",
            "tools/haiku/d0_evidence.py",
            "tools/haiku/probe_stage.py",
            "tools/haiku/build-driver.sh",
            "tools/haiku/kcc",
            "tools/haiku/config.sh",
            "tools/haiku/qemu_hmp.py",
            "tools/haiku/card_run.py",
            "tools/haiku/vm_guard.py",
            "tools/haiku/d0_monitor.py",
            "tools/haiku/d0_topology.py",
            "tools/haiku/d0_kernel_log.py",
            "tools/observer/task_stream.py",
            "tools/observer/task_proof.inc",
            "tools/observer/binding.py",
            "tools/observer/normalize.py",
            "tools/observer/supervise.py",
            "tools/observer/build.py",
            "tools/observer/vfio_decode.inc",
            "tools/dma_model.py",
        )
    )
    for folder in ("src/a7", "src/memory", "src/devinit", "src/runtime"):
        names.update(str(p.relative_to(ROOT)) for p in (ROOT / folder).glob("*.h"))
    names.update(("src/os/HaikuBackend.h", "src/os/HaikuMemory.h"))
    names.update(str(p.relative_to(ROOT)) for p in (ROOT / "tests/a7_shim").glob("*.h"))
    names.update(str(p.relative_to(ROOT)) for p in (ROOT / "tests/os_shim").glob("*.h"))
    return sorted(names)


def manifest():
    data, total, capture = inputs()
    public, nonce = key_inputs()
    crypto = crypto_sources.validate()
    if (PACKAGE / "a7_config.h").read_text() != config(data, public, nonce, total):
        raise ValueError("generated config differs")
    if (PACKAGE / "ed25519-license.txt").read_bytes() != (
        crypto_sources.CACHE / "license.txt"
    ).read_bytes():
        raise ValueError("external notice differs")
    identity = probe_stage.validate(ARTIFACTS["identity"])
    for role, tag in (
        ("owner", b"generic/k40c_a7_owner/v1"),
        ("client", b"A7_ARM_ONLY_POST_WRITE"),
    ):
        raw = ARTIFACTS[role].read_bytes()
        if raw[:6] != b"\x7fELF\x02\x01" or raw[18:20] != b"\x3e\x00" or tag not in raw:
            raise ValueError("wrong A7 artifact role")
    symbols = subprocess.check_output(["nm", "-D", str(ARTIFACTS["owner"])], text=True)
    if (
        "simulatePost" in symbols
        or "ed25519_sign" in symbols
        or "create_keypair" in symbols
        or "_GLOBAL__sub_I_" in symbols
    ):
        raise ValueError("forbidden owner artifact capability")
    return dict(
        stage="A7_ARM_ONLY_POST_WRITE",
        approval="explicit yes required for ONE run",
        public_key_hex=public.hex(),
        package_nonce_hex=nonce.hex(),
        kernel_sha256=identity["kernel_sha256"],
        artifacts={
            name: dict(path=str(path.resolve()), sha256=sha(path))
            for name, path in sorted(ARTIFACTS.items())
        },
        source_sha256={name: sha(ROOT / name) for name in source_names()},
        rom_sha256=devinit_preflight.EXPECTED,
        physical_vram_bytes=total,
        physical_vram_source=dict(
            path=str(capture.relative_to(ROOT)),
            sha256=sha(capture),
            field="fb: Total: MiB",
        ),
        config_sha256=sha(PACKAGE / "a7_config.h"),
        verifier=crypto,
        host_check_sha256=sha(ROOT / "work/S1A7NITS/host-check.json"),
        teardown_sources_sha256=sha(ROOT / "work/S1A7NATIVE/teardown-sources.json"),
        inventory_sha256=hashlib.sha256(dump(inventory(data)).encode()).hexdigest(),
        production_dma_publication=False,
        payload_visibility_claim=False,
        physical_run_completed=False,
    )


def validate():
    expected = dump(manifest())
    if not PUBLIC.is_file() or PUBLIC.read_text() != expected:
        raise ValueError("A7 suite differs; rebuild/review before approval")
    if INVENTORY.read_text() != dump(inventory(inputs()[0])):
        raise ValueError("A7 write inventory differs")
    return json.loads(expected)


def build():
    if os.geteuid() == 0:
        raise ValueError("root execution forbidden")
    crypto_sources.validate()
    data, total, _ = inputs()
    subprocess.run(
        [sys.executable, str(ROOT / "tools/a7/host_check.py"), "--check"],
        cwd=ROOT,
        check=True,
    )
    PACKAGE.mkdir(mode=0o700, parents=True, exist_ok=True)
    if (PACKAGE / "consumed.json").exists():
        raise ValueError(
            "single-use package consumed; preserve it and prepare a new reviewed package"
        )
    key = PACKAGE / "host-key.pem"
    if not key.exists():
        old_mask = os.umask(0o077)
        try:
            subprocess.run(
                ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key)],
                check=True,
            )
            with (PACKAGE / "nonce.bin").open("xb") as out:
                out.write(os.urandom(32))
        finally:
            os.umask(old_mask)
    public, nonce = key_inputs()
    shutil.copyfile(
        crypto_sources.CACHE / "license.txt", PACKAGE / "ed25519-license.txt"
    )
    (PACKAGE / "a7_config.h").write_text(config(data, public, nonce, total))
    flags = (
        "-Werror -Wframe-larger-than=4096 -fwrapv -fno-strict-aliasing -Isrc -I"
        + str(PACKAGE)
    )
    env = dict(os.environ, KCFLAGS=flags)
    frozen = {name: sha(ROOT / name) for name in source_names()}
    frozen_config = sha(PACKAGE / "a7_config.h")
    sources = [
        *OWNER,
        *(str(crypto_sources.CACHE / "src" / name) for name in crypto_sources.SOURCES),
    ]
    subprocess.run(
        ["bash", "tools/haiku/build-driver.sh", "k40_a7_owner_module", *sources],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        ["bash", "tools/haiku/build-driver.sh", "k40_a7_stage", *CLIENT],
        cwd=ROOT,
        env=env,
        check=True,
    )
    if frozen != {
        name: sha(ROOT / name) for name in source_names()
    } or frozen_config != sha(PACKAGE / "a7_config.h"):
        raise ValueError("A7 source inputs changed during build; no manifest generated")
    PUBLIC.parent.mkdir(parents=True, exist_ok=True)
    INVENTORY.write_text(dump(inventory(data)))
    PUBLIC.write_text(dump(manifest()))
    print("A7 package built. NO hardware run approved or performed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        validate()
        print("A7 package/source record matches; this grants no run approval")
    else:
        build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
