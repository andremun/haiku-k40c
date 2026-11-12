#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Build the distinct combined package. --check writes nothing and requires rehearsal."""
import argparse
import hashlib
import json
import lzma
import re
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools/haiku"))
from tools.a7 import build as a7, crypto_sources, runtime_export
from tools.a7.guest_job import job as a7_job
from tools.memstage import contract, pci, stage
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

# K40_MEM_STAGE selects the stage (tools/memstage/stage.py). Each stage has its
# own package, key, nonce and records. The S1 names stay as they were.
PACKAGE = ROOT / "build/memstage" / stage.CURRENT["package"]
WORK = ROOT / "work" / stage.CURRENT["work"]
PUBLIC = WORK / "package.json"
PLAN = WORK / "phase-plan.json"
INVENTORY = WORK / "write-inventory.json"
STAGE = "BATCH1_A7_BAR1_VRAM" if stage.NAME == "s1" else "S2_A7_BAR1_CHANNEL_COPY"
ROM = Path(
    os.environ.get(
        "K40_VBIOS",
        str(
            Path.home() / "haiku-cross/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom"
        ),
    )
).expanduser()
CORE = tuple(
    p.relative_to(ROOT).as_posix()
    for p in sorted((ROOT / "src/memstage").glob("*.cpp"))
)
OWNER = (
    "src/memory/VramArena.cpp",
    *CORE,
    "src/memauth/Session.cpp",
    "src/memnative/Policy.cpp",
    "src/memnative/NativeIo.cpp",
    "src/memnative/NativeOwner.cpp",
    "src/memnative/Module.cpp",
)
ROLES = (
    "preflight",
    "preflight_helper",
    "memory_owner",
    "memory_client",
    "memory_helper",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(value):
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def inputs():
    data = ROM.read_bytes()
    if (
        len(data) != 181760
        or hashlib.sha256(data).hexdigest() != a7.devinit_preflight.EXPECTED
    ):
        raise ValueError("approved ROM differs")
    capture = ROOT / "reference/linux-run-debug/dmesg.txt.xz"
    totals = set(
        int(value)
        for value in re.findall(
            r"fb: Total:\s*(\d+) MiB", lzma.open(capture, "rt").read()
        )
    )
    if len(totals) != 1:
        raise ValueError("captured physical VRAM amount ambiguous")
    return data, totals.pop() * 1048576, capture


def external_inputs():
    cross = Path.home() / "haiku-cross"
    headers = cross / "haiku/headers"
    paths = [
        headers / name
        for name in (
            "os/drivers/KernelExport.h",
            "os/drivers/module.h",
            "os/drivers/PCI.h",
            "os/drivers/Drivers.h",
            "os/support/Errors.h",
            "private/kernel/util/Random.h",
            "private/kernel/arch/x86/64/atomic.h",
        )
    ]
    paths.extend(
        (
            cross / "lib/kernel.so",
            cross / "generated.x86_64/cross-tools-x86_64/bin/x86_64-unknown-haiku-gcc",
            cross / "generated.x86_64/cross-tools-x86_64/bin/x86_64-unknown-haiku-g++",
        )
    )
    return dict(
        scope="local build/link identity; full running kernel source identity unestablished",
        sha256={str(path): sha(path) for path in sorted(paths)},
    )


def source_names():
    names = set(contract.frozen()["source_sha256"])
    names.update(a7.source_names())
    names.update(
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "tests").glob("*mem*")
        if p.suffix in (".cpp", ".h", ".py")
    )
    for directory in ("src/memory", "src/memauth", "src/memnative", "src/memstage"):
        names.update(
            p.relative_to(ROOT).as_posix()
            for p in (ROOT / directory).glob("*")
            if p.suffix in (".h", ".cpp")
        )
    names.update(
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "tools/memstage").glob("*")
        if p.suffix in (".py", ".c")
    )
    names.update(
        (
            "tools/haiku/selftest/memory_client.cpp",
            "tools/haiku/selftest/memory_preflight.cpp",
            "tools/haiku/build-driver.sh",
            "tools/haiku/kcc",
            "tools/haiku/config.sh",
            "tools/a7/build.py",
            "tools/a7/run.py",
            "tools/a7/crypto_sources.py",
            "tools/a7/runtime_export.py",
            "tools/haiku/card_run.py",
            "tools/haiku/d0_run.py",
            "tools/haiku/d0_monitor.py",
            "tools/haiku/d0_topology.py",
            "tools/haiku/d0_kernel_log.py",
            "tools/haiku/vm_guard.py",
            "tools/observer/task_stream.py",
            "tools/observer/supervise.py",
            "docs/S1-MEMORY-CONTRACT.md",
        )
    )
    return tuple(sorted(names))


def key(folder):
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = folder / "host-key.pem"
    nonce = folder / "nonce.bin"
    if not path.exists():
        private = Ed25519PrivateKey.generate()
        data = private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as out:
            out.write(data)
        descriptor = os.open(nonce, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as out:
            out.write(os.urandom(32))
    for file in (path, nonce):
        info = file.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o600
        ):
            raise ValueError("private package input permissions")
    private = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(private, Ed25519PrivateKey):
        raise ValueError("wrong package key type")
    public = private.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    raw = nonce.read_bytes()
    if len(raw) != 32:
        raise ValueError("package nonce size")
    return public, raw


def compile_driver(name, sources, include):
    # Preserve original A7 SONAME/flags while keeping every new artifact in this
    # private package. Historical run7 build/haiku files are never overwritten.
    sonames = {
        "k40_batch_a7_owner": "k40_a7_owner_module",
        "k40_batch_a7_stage": "k40_a7_stage",
        "k40_batch_mem_owner": "k40c_memory_owner",
        "k40_batch_mem_stage": "k40_mem_stage",
        "k40_batch_mem_preflight": "k40_mem_preflight",
    }
    folder = PACKAGE / "objects" / name
    folder.mkdir(parents=True, exist_ok=True)
    objects = []
    for source in sources:
        obj = folder / (Path(source).stem + ".o")
        objects.append(str(obj))
        subprocess.run(
            [
                "tools/haiku/kcc",
                "-O2",
                "-Werror",
                "-Wframe-larger-than=4096",
                "-fwrapv",
                "-fno-strict-aliasing",
                "-Isrc",
                "-I" + str(include),
                "-c",
                source,
                "-o",
                str(obj),
            ],
            cwd=ROOT,
            check=True,
        )
    target = PACKAGE / name
    compiler = (
        Path.home()
        / "haiku-cross/generated.x86_64/cross-tools-x86_64/bin/x86_64-unknown-haiku-gcc"
    )
    subprocess.run(
        [
            str(compiler),
            "-shared",
            "-nostdlib",
            "-z",
            "max-page-size=0x1000",
            "-z",
            "noseparate-code",
            "-z",
            "norelro",
            "-Wl,--no-undefined",
            "-Wl,-soname=" + sonames[name],
            "-o",
            str(target),
            *objects,
            "-L" + str(Path.home() / "haiku-cross/lib"),
            "-l:kernel.so",
        ],
        check=True,
    )
    return target


def compile_helper(name, preflight=False):
    obj = PACKAGE / (name + ".o")
    subprocess.run(
        [
            "tools/haiku/kcc",
            "-U_KERNEL_MODE",
            "-Werror",
            "-O2",
            *(["-DMEMORY_PREFLIGHT"] if preflight else []),
            "-c",
            "tools/memstage/open_phase.c",
            "-o",
            str(obj),
        ],
        cwd=ROOT,
        check=True,
    )
    compiler = (
        Path.home()
        / "haiku-cross/generated.x86_64/cross-tools-x86_64/bin/x86_64-unknown-haiku-gcc"
    )
    target = PACKAGE / name
    subprocess.run(
        [
            str(compiler),
            "-shared",
            "-nostdlib",
            "-Wl,-e,_start",
            "-Wl,--no-undefined",
            "-Wl,-z,max-page-size=0x1000",
            str(obj),
            str(runtime_export.LIBRARY),
            "-o",
            str(target),
        ],
        check=True,
    )
    return target


def details(path):
    return dict(path=str(path.resolve()), bytes=path.stat().st_size, sha256=sha(path))


def plan(child, sources):
    return dict(
        stage=STAGE,
        version=1,
        A7_source_freeze=contract.frozen(),
        A7_guest_artifacts=child["guest_artifacts"],
        A7_job_sha256=hashlib.sha256(
            a7_job(0, child["guest_artifacts"]).encode()
        ).hexdigest(),
        kernel_sha256=child["kernel_sha256"],
        rom_sha256=child["rom_sha256"],
        vram_bytes=child["physical_vram_bytes"],
        sequence=[
            "G0 read-only preflight",
            "unchanged run7 A7 child, fresh arm witness",
            "distinct memory grant bound to current A7 transcript/witness",
            "normal arena and raw post-A7 baselines",
            "debug zero/retain and physical A/B pattern/complement",
            "gk104 17/12 BAR1 tables/mode/PDB invalidate",
            "BAR1 A/B -> B/B -> A/B witness",
            "owned BAR1 disable, retained guest/VFIO termination",
        ],
        mappings=dict(
            BAR0=dict(bytes=16777216, access="kernel read/write explicit UC"),
            BAR1=dict(
                bytes=8192,
                access="kernel read-only explicit UC",
                vmm_range="discovered full aperture",
            ),
        ),
        limits=dict(
            guest_seconds=600,
            memory_us=30000000,
            bulk_us=5000000,
            poll_us=2000000,
            polls=100000,
            events=4096,
            arena_records=32,
        ),
        exclusions=[
            "BAR2",
            "D1/G2",
            "new 0x100c10 operation",
            "channel/PBDMA/scheduler",
            "host DMA payload proof",
            "live free/reuse",
            "manual reset",
        ],
        source_sha256=sources,
        external_build_inputs=external_inputs(),
        readback="original G1 observation only; Q11 open; A7 success not S1 success",
    )


def config(public, nonce, digest, vram):
    def array(name, data):
        return (
            "static const uint8_t "
            + name
            + "[32]={"
            + ",".join(str(x) for x in data)
            + "};\n"
        )

    return (
        "#pragma once\n#include <cstdint>\n"
        + array("memoryPublicKey", public)
        + array("memoryNonce", nonce)
        + array("memoryPlan", digest)
        + f"static const uint64_t memoryVram={vram}ULL;\n"
        + f"static const bool memoryCopy={'true' if stage.CURRENT['copy'] else 'false'};\n"
    )


def generated_inventory(data):
    return dict(
        stage=STAGE,
        A7=a7.inventory(data),
        memory=json.loads((ROOT / "work/S1MEMMMU/host-check.json").read_text()),
        reads=json.loads((ROOT / "work/S1MEMFAULTS/catalog.json").read_text()),
        physical_window=dict(
            selector="0x1700 = owned 1 MiB window >> 16",
            data="0x700000 + owned physical low 20 bits",
            debug="two zeroed retained 128 KiB objects",
            data_pages="two 4096-byte owned address-pattern/complement pages; all writes before all reads",
            tables="zero full PGD/SPT/instance, then exact derived PDE/SPTE/instance fields; retained SPT update entry 0 only",
        ),
        extra_read_scope="G0 raw MC; after grant FB partition/unit/disabled/amount discovery; source-backed raw fault catalog; no writes to PCI config",
    )


def build():
    if os.geteuid() == 0:
        raise ValueError("root forbidden")
    if (PACKAGE / "consumed.json").exists():
        raise ValueError("consumed package must be preserved")
    frozen = contract.frozen()
    crypto_sources.validate()
    pci.source_record()
    data, total, _ = inputs()
    PACKAGE.mkdir(parents=True, exist_ok=True, mode=0o700)
    childFolder = PACKAGE / "a7"
    public, nonce = key(childFolder)
    (childFolder / "a7_config.h").write_text(a7.config(data, public, nonce, total))
    crypto = [
        str(crypto_sources.CACHE / "src" / name) for name in crypto_sources.SOURCES
    ]
    childOwner = compile_driver("k40_batch_a7_owner", [*a7.OWNER, *crypto], childFolder)
    childClient = compile_driver("k40_batch_a7_stage", list(a7.CLIENT), childFolder)
    # Original fixed helper and identity were exercised by run7; validate exact bytes.
    old = json.loads((ROOT / "results/20261029-a7-069cb71b/launch.json").read_text())[
        "suite"
    ]
    childPaths = dict(
        owner=childOwner,
        client=childClient,
        identity=Path(old["artifacts"]["identity"]["path"]),
        helper=Path(old["artifacts"]["helper"]["path"]),
    )
    for role in ("identity", "helper"):
        if sha(childPaths[role]) != old["guest_artifacts"][role]["sha256"]:
            raise ValueError("run7 helper/identity bytes differ")
    if sha(childClient) != old["guest_artifacts"]["client"]["sha256"]:
        raise ValueError("unchanged A7 client differs from run7")
    child = dict(
        stage="A7_ARM_ONLY_POST_WRITE",
        public_key_hex=public.hex(),
        package_nonce_hex=nonce.hex(),
        kernel_sha256=old["kernel_sha256"],
        rom_sha256=old["rom_sha256"],
        physical_vram_bytes=total,
        artifacts={role: details(path) for role, path in sorted(childPaths.items())},
        guest_artifacts={
            role: {k: v for k, v in details(path).items() if k != "path"}
            for role, path in sorted(childPaths.items())
        },
    )
    snapshot = {name: sha(ROOT / name) for name in source_names()}
    compiledPlan = plan(child, snapshot)
    digest = hashlib.sha256(dump(compiledPlan).encode()).digest()
    memoryPublic, memoryNonce = key(PACKAGE)
    (PACKAGE / "mem_config.h").write_text(
        config(memoryPublic, memoryNonce, digest, total)
    )
    paths = dict(
        memory_owner=compile_driver("k40_batch_mem_owner", [*OWNER, *crypto], PACKAGE),
        memory_client=compile_driver(
            "k40_batch_mem_stage", ["tools/haiku/selftest/memory_client.cpp"], PACKAGE
        ),
        preflight=compile_driver(
            "k40_batch_mem_preflight",
            ["tools/haiku/selftest/memory_preflight.cpp"],
            PACKAGE,
        ),
        memory_helper=compile_helper("memory_open"),
        preflight_helper=compile_helper("preflight_open", True),
    )
    for role in ("memory_owner",):
        symbols = subprocess.check_output(["nm", "-D", str(paths[role])], text=True)
        if any(
            name in symbols
            for name in (
                "hostSimulation",
                "simulatePost",
                "ed25519_sign",
                "create_keypair",
                "_GLOBAL__sub_I_",
            )
        ):
            raise ValueError("forbidden native capability/initializer")
    shutil.copyfile(
        crypto_sources.CACHE / "license.txt", PACKAGE / "ed25519-license.txt"
    )
    suite = dict(
        stage=STAGE,
        approval="Claude review and explicit yes for one launch; no approval supplied by build",
        A7=child,
        public_key_hex=memoryPublic.hex(),
        package_nonce_hex=memoryNonce.hex(),
        plan_sha256=digest.hex(),
        plan=compiledPlan,
        artifacts={role: details(path) for role, path in sorted(paths.items())},
        guest_artifacts={
            role: {k: v for k, v in details(path).items() if k != "path"}
            for role, path in sorted(paths.items())
        },
        kernel_sha256=old["kernel_sha256"],
        rom_sha256=old["rom_sha256"],
        source_sha256=snapshot,
        observer=old["artifacts"]["observer"],
        qemu=old["artifacts"]["qemu"],
        crypto=crypto_sources.validate(),
        runtime_library=details(runtime_export.LIBRARY),
        license=details(PACKAGE / "ed25519-license.txt"),
        config_sha256=dict(
            memory=sha(PACKAGE / "mem_config.h"), A7=sha(childFolder / "a7_config.h")
        ),
        Q7="open",
        Q11="open; original observational readback only",
        S1_complete=False,
    )
    from tools.memstage.guest_job import job

    suite["job_sha256"] = hashlib.sha256(job(0, 0, suite).encode()).hexdigest()
    if (
        snapshot != {name: sha(ROOT / name) for name in source_names()}
        or contract.frozen() != frozen
    ):
        raise ValueError("sources changed during build")
    PUBLIC.write_text(dump(suite))
    PLAN.write_text(dump(compiledPlan))
    INVENTORY.write_text(dump(generated_inventory(data)))
    print("Combined package built; no card run approved or performed.")


def validate_public(require_rehearsal=True):
    suite = json.loads(PUBLIC.read_text())
    if PUBLIC.read_text() != dump(suite) or suite["stage"] != STAGE:
        raise ValueError("package role/canonical form")
    current = {name: sha(ROOT / name) for name in source_names()}
    if (
        current != suite["source_sha256"]
        or contract.frozen() != suite["plan"]["A7_source_freeze"]
    ):
        raise ValueError("package source/frozen A7 differs")
    if (
        PLAN.read_text() != dump(suite["plan"])
        or hashlib.sha256(dump(suite["plan"]).encode()).hexdigest()
        != suite["plan_sha256"]
    ):
        raise ValueError("compiled phase plan differs")
    data, total, _ = inputs()
    if total != suite["plan"]["vram_bytes"] or INVENTORY.read_text() != dump(
        generated_inventory(data)
    ):
        raise ValueError("write/read scope differs")
    expected = dict(
        memory_owner=PACKAGE / "k40_batch_mem_owner",
        memory_client=PACKAGE / "k40_batch_mem_stage",
        preflight=PACKAGE / "k40_batch_mem_preflight",
        memory_helper=PACKAGE / "memory_open",
        preflight_helper=PACKAGE / "preflight_open",
    )
    childExpected = dict(
        owner=PACKAGE / "k40_batch_a7_owner",
        client=PACKAGE / "k40_batch_a7_stage",
        identity=ROOT / "build/haiku/k40_identity_probe",
        helper=ROOT / "build/haiku/k40_a7_open",
    )
    for group, paths, guest in (
        (suite["artifacts"], expected, suite["guest_artifacts"]),
        (suite["A7"]["artifacts"], childExpected, suite["A7"]["guest_artifacts"]),
    ):
        if set(group) != set(paths) or guest != {
            role: {k: v for k, v in info.items() if k != "path"}
            for role, info in group.items()
        }:
            raise ValueError("artifact role/framing differs")
        if any(
            info["path"] != str(paths[role].resolve()) for role, info in group.items()
        ):
            raise ValueError("artifact path differs")
        for role, info in group.items():
            path = Path(info["path"])
            if details(path) != info:
                raise ValueError("artifact differs: " + role)
    for info in (suite["observer"], suite["qemu"]):
        if sha(Path(info["path"])) != info["sha256"]:
            raise ValueError("observer/QEMU differs")
    if suite["crypto"] != crypto_sources.validate():
        raise ValueError("crypto pin differs")
    if (
        details(runtime_export.LIBRARY) != suite["runtime_library"]
        or details(PACKAGE / "ed25519-license.txt") != suite["license"]
    ):
        raise ValueError("runtime/notice differs")
    memory = bytes.fromhex(suite["public_key_hex"])
    nonce = bytes.fromhex(suite["package_nonce_hex"])
    if (PACKAGE / "mem_config.h").read_text() != config(
        memory, nonce, bytes.fromhex(suite["plan_sha256"]), total
    ):
        raise ValueError("memory config differs")
    child = suite["A7"]
    if plan(child, current) != suite["plan"]:
        raise ValueError("phase plan inputs differ")
    if suite["config_sha256"] != dict(
        memory=sha(PACKAGE / "mem_config.h"), A7=sha(PACKAGE / "a7/a7_config.h")
    ):
        raise ValueError("compiled config hash differs")
    if (PACKAGE / "a7/a7_config.h").read_text() != a7.config(
        data,
        bytes.fromhex(child["public_key_hex"]),
        bytes.fromhex(child["package_nonce_hex"]),
        total,
    ):
        raise ValueError("A7 config differs")
    for role, values in (
        (
            suite["artifacts"]["memory_owner"],
            (memory, nonce, bytes.fromhex(suite["plan_sha256"])),
        ),
        (
            child["artifacts"]["owner"],
            (
                bytes.fromhex(child["public_key_hex"]),
                bytes.fromhex(child["package_nonce_hex"]),
                data,
            ),
        ),
    ):
        raw = Path(role["path"]).read_bytes()
        if any(value not in raw for value in values):
            raise ValueError("owner does not contain compiled binding/ROM")
    from tools.memstage.guest_job import job

    if hashlib.sha256(job(0, 0, suite).encode()).hexdigest() != suite["job_sha256"]:
        raise ValueError("combined guest job differs")
    pci.source_record()
    if require_rehearsal:
        from tools.memstage import rehearse

        rehearse.validate(suite)
    return suite


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        validate_public()
        print("Combined source/artifact/rehearsal checks pass; no launch.")
    else:
        build()


if __name__ == "__main__":
    main()
