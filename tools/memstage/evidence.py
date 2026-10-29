# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Strict phase/effect checks. Missing data is pending; contradictory data stops."""
import re
import struct

NO_CARD = 0x80006003  # Haiku Errors.h:104, B_STORAGE_ERROR_BASE+3.
MC = 0x100  # fb/gf100.c:37.
CONTEXT = 0x1704  # bar/gf100.c:46-58.
PDB = 0x100CB8  # mmu/vmmgf100.c:185,216.
INVALIDATE = 0x100CBC  # mmu/vmmgf100.c:221.
MODE = 0x100C80  # fb/gf100.c:66-77.
FLUSH = 0x70000  # bar/g84.c:33.
WINDOW = 0x1700  # instmem/nv50.c:68.


def installed(output, artifacts, roles, prefix="MEM"):
    for role in roles:
        matches = re.findall(
            r"^"
            + prefix
            + "-INSTALL "
            + re.escape(role)
            + r" size=(\d+) sha256=([0-9a-f]{64}) inode-before=(\d+) inode-after=(\d+)\r?$",
            output,
            re.M,
        )
        if len(matches) != 1:
            raise ValueError("missing/repeated checked install: " + role)
        size, digest, before, after = matches[0]
        expected = artifacts[role]
        if (
            int(size) != expected["bytes"]
            or digest != expected["sha256"]
            or before != after
        ):
            raise ValueError("artifact size/hash/inode differs: " + role)


def preflight(folder, serial, cardless):
    if not all(
        (folder / name).exists()
        for name in (
            "preflight-output.txt",
            "preflight-exit.txt",
            "preflight-install.txt",
        )
    ):
        return False
    output = (folder / "preflight-output.txt").read_text()
    status = NO_CARD if cardless else 0
    expected = f"MEM-OPEN-RESULT role=preflight status=0x{status:08x}"
    if (
        output.count(expected) != 1
        or output.count("MEM-OPEN-RESULT") != 1
        or (folder / "preflight-exit.txt").read_text().strip()
        != ("1" if cardless else "0")
    ):
        raise ValueError("preflight one-open result differs")
    loads = re.findall(
        r"^k40_mem_preflight: LOAD result=([0-9a-f]{8})\r?$", serial, re.M
    )
    opens = re.findall(
        r"^k40_mem_preflight: OPEN result=([0-9a-f]{8})\r?$", serial, re.M
    )
    if not loads or not opens:
        return False
    if opens != [f"{status:08x}"]:
        raise ValueError("preflight callback was not reached exactly once")
    if any(int(value, 16) != status for value in loads):
        raise ValueError("preflight raw status differs")
    raw = re.findall(
        r"^k40_mem_preflight: G0 raw_mc=([0-9a-f]{8}) requested=explicit-UC read-only\r?$",
        serial,
        re.M,
    )
    if cardless:
        if raw:
            raise ValueError("cardless preflight accessed a matching device")
    elif not raw:
        return False
    elif any(int(value, 16) for value in raw):
        raise ValueError("dirty G0 baseline")
    return True


def a7_nocard(folder, serial, child):
    if not all(
        (folder / name).exists()
        for name in ("job.exit", "job-output.txt", "kernel.sha256")
    ):
        return False
    if (folder / "job.exit").read_text().strip() == "0":
        raise ValueError("A7 succeeded without card")
    output = (folder / "job-output.txt").read_text()
    installed(output, child["guest_artifacts"], tuple(child["guest_artifacts"]), "A7")
    if output.count("A7-OPEN-RESULT status=0xffffffff") != 1:
        raise ValueError("wrong A7 no-card open status")
    if "k40_a7: REFUSED no matching PCI card before reservation" not in serial:
        return False
    if "k40_a7: FAIL client prepare" not in serial:
        return False
    if (folder / "kernel.sha256").read_text().strip() != child["kernel_sha256"]:
        raise ValueError("guest kernel differs")
    if any((folder / name).exists() for name in ("request.bin", "grant.bin")) or any(
        marker in serial
        for marker in ("k40_a7: PREPARED", "k40_a7: ARM_BEFORE", "k40_a7: POST_RESULT")
    ):
        raise ValueError("unexpected A7 hardware/grant path in rehearsal")
    return True


def memory_nocard(folder, serial):
    if not all(
        (folder / name).exists() for name in ("memory-output.txt", "memory-exit.txt")
    ):
        return False
    output = (folder / "memory-output.txt").read_text()
    if (
        output.count(f"MEM-OPEN-RESULT role=memory status=0x{NO_CARD:08x}") != 1
        or output.count("MEM-OPEN-RESULT") != 1
        or (folder / "memory-exit.txt").read_text().strip() != "1"
    ):
        raise ValueError("wrong memory no-card open status")
    if serial.count("k40_mem: NO_CARD before reservation or mapping") != 1:
        return False
    if serial.count("k40_mem: PREPARE_CALL n=1") != 1:
        raise ValueError("memory preparation was not reached exactly once")
    if any((folder / name).exists() for name in ("request.bin", "grant.bin")) or any(
        marker in serial
        for marker in (
            "k40_mem: PREPARED",
            "k40_mem: EVENT",
            "k40_mem: PASS BAR1_SCOPED",
        )
    ):
        raise ValueError("unexpected memory grant/effect path in rehearsal")
    return True


def request_fields(raw, suite, serial, resources):
    if len(raw) != 256 or raw[:16] != b"K40MEMREQ\x01" + bytes(6):
        raise ValueError("memory request framing")
    if (
        raw[16:48].hex() != suite["package_nonce_hex"]
        or raw[48:80].hex() != suite["plan_sha256"]
        or not any(raw[80:96])
        or any(raw[176:256])
    ):
        raise ValueError("memory request nonce/plan/challenge/reserved")
    epoch, owner, bar0, size0, bar1, size1, vram, begin, end, prefix = struct.unpack(
        "<10Q", raw[96:176]
    )
    if (
        not epoch
        or owner != epoch
        or vram != suite["plan"]["vram_bytes"]
        or begin != (256 * 1024 + 4096)
        or end != vram - 1048576
        or prefix != 8192
    ):
        raise ValueError("memory owner/layout profile")
    if (bar0, size0) != (
        resources["bars"]["0"]["address"],
        resources["bars"]["0"]["bytes"],
    ) or (bar1, size1) != (
        resources["bars"]["1"]["address"],
        resources["bars"]["1"]["bytes"],
    ):
        raise ValueError("guest/QMP BAR resource mismatch")
    prepared = re.findall(
        r"^k40_mem: PREPARED owner=(\d+) epoch=(\d+) bar0=([0-9a-f]+) bar1=([0-9a-f]+)\r?$",
        serial,
        re.M,
    )
    if prepared != [(str(owner), str(epoch), f"{bar0:x}", f"{bar1:x}")]:
        raise ValueError("resident request identity differs")
    map0 = re.findall(
        r"^k40_mem: MAP bar=0 base=([0-9a-f]+) resource=(\d+) mapped=8388608 flags=explicit-UC status=(\d+)\r?$",
        serial,
        re.M,
    )
    map1 = re.findall(
        r"^k40_mem: MAP bar=1 base=([0-9a-f]+) resource=(\d+) mapped=8192 flags=explicit-UC read-only status=(\d+)\r?$",
        serial,
        re.M,
    )
    if (
        len(map0) != 1
        or len(map1) != 1
        or map0[0][:2] != (f"{bar0:x}", str(size0))
        or map1[0][:2] != (f"{bar1:x}", str(size1))
    ):
        raise ValueError("explicit UC mapping observations missing/different")
    return dict(
        epoch=epoch,
        owner=owner,
        bar0=bar0,
        bar0_bytes=size0,
        bar1=bar1,
        bar1_bytes=size1,
        vram=vram,
        begin=begin,
        end=end,
        prefix_bytes=prefix,
    )


def memory_final(serial, suite, request):
    marker = "k40_mem: PASS BAR1_SCOPED faults=0 upload=0 mapper=0 closure=2 allocations=7 journal_overflow=0"
    if serial.count(marker) != 1 or serial.count("K40-MEM-END") != 1:
        raise ValueError("memory final pass/closure missing or repeated")
    owner = struct.unpack_from("<Q", request, 104)[0]
    sequence = (
        marker,
        "k40_mem: SUBMIT result=0 state=3",
        f"k40_mem: RETAINED owner={owner} state=3",
        "K40-MEM-END",
    )
    positions = [serial.find(text) for text in sequence]
    if (
        -1 in positions
        or positions != sorted(positions)
        or any(serial.count(text) != 1 for text in sequence)
    ):
        raise ValueError("memory result/retention ordering")
    if serial.count("k40_mem: IO_REJECT kind=0 offset=0 value=0") != 1:
        raise ValueError("native policy rejection")
    allocations = []
    for match in re.finditer(
        r"^k40_mem: ALLOCATION id=(\d+) role=(\d+) physical=([0-9a-f]+) bytes=(\d+) generation=(\d+) staged=(\d+) referenced=(\d+) retained=(\d+)\r?$",
        serial,
        re.M,
    ):
        values = list(match.groups())
        allocations.append(
            tuple(int(x, 16 if i == 2 else 10) for i, x in enumerate(values))
        )
    sizes = {1: 131072, 2: 131072, 3: 65536, 4: 262144, 5: 4096, 6: 4096, 7: 4096}
    generations = {1: 1, 2: 1, 3: 2, 4: 5, 5: 3, 6: 3, 7: 3}
    roles = (1, 2, 6, 7, 3, 4, 5)
    cursor = 256 * 1024 + 4096
    byrole = {}
    if len(allocations) != 7:
        raise ValueError("allocation ledger incomplete")
    for index, record in enumerate(allocations, 1):
        ident, role, address, size, generation, staged, referenced, retained = record
        if (
            ident != index
            or role != roles[index - 1]
            or address != cursor
            or size != sizes[role]
            or generation != generations[role]
            or (staged, referenced, retained) != (1, 1, 1)
        ):
            raise ValueError("allocation extent/generation/retention differs")
        cursor += size
        byrole[role] = address
    events = []
    pattern = r"^k40_mem: EVENT phase=(\d+) error=(\d+) offset=([0-9a-f]+) value=([0-9a-f]+) polls=(\d+) elapsed=(\d+) operation=(\d+) role=(\d+) detail=(\d+)\r?$"
    for match in re.finditer(pattern, serial, re.M):
        event = tuple(
            int(value, 16 if index in (2, 3) else 10)
            for index, value in enumerate(match.groups())
        )
        if event[1] or event[0] > 7 or event[6] > 7:
            raise ValueError("memory error/unknown diagnostic event")
        events.append(event)
    if not events or len(events) > 4096:
        raise ValueError("diagnostic coverage/bound")
    for phase in range(8):
        if [(e[3]) for e in events if e[0] == phase and e[2] == MC and e[6] == 0] != [
            0
        ]:
            raise ValueError("raw per-phase MC baseline missing/dirty")
    writes = [(e[0], e[2], e[3]) for e in events if e[6] == 1]
    allowed = {WINDOW, FLUSH, MODE, PDB, INVALIDATE, CONTEXT}
    if any(reg not in allowed for _, reg, _ in writes):
        raise ValueError("unexpected register write record")
    values = lambda reg: [value for phase, r, value in writes if r == reg]
    if values(PDB) != [byrole[3] >> 8] * 3 or values(INVALIDATE) != [0x80000005] * 3:
        raise ValueError("PDB-specific invalidation differs")  # vmmgf100.c:216,221-233.
    if values(CONTEXT) != [0x80000000 | (byrole[5] >> 12), byrole[5] >> 12]:
        raise ValueError("BAR1 context effects differ")  # bar/gf100.c:46-58.
    if len(values(MODE)) != 1 or values(MODE)[0] & 1 or values(FLUSH) != [1] * 17:
        raise ValueError("mode/flush protocol differs")  # gf100.c:66-77; bar/g84.c:33.
    if any(value != 0 for value in values(WINDOW)):
        raise ValueError(
            "selector outside finite owned first-window profile"
        )  # instmem/nv50.c:68; ledger derived above.
    pte = (
        lambda physical: (physical >> 8) | 5
    )  # vmmgf100.c:35,314-319 valid + RO, VRAM.
    patches = [(e[0], e[7], e[2], e[3]) for e in events if e[6] == 5]
    expected = [
        (3, 3, 0, (byrole[4] << 24) | (1 << 32)),
        (3, 4, 0, pte(byrole[6])),
        (3, 4, 8, pte(byrole[7])),  # vmmgf100.c:129-140.
        (3, 5, 512, byrole[3]),
        (
            3,
            5,
            520,
            struct.unpack_from("<Q", request, 136)[0] - 1,
        ),  # vmmgf100.c:358-360.
        (5, 4, 0, pte(byrole[7])),
        (6, 4, 0, pte(byrole[6])),
    ]
    if patches != expected:
        raise ValueError("table/instance/remap serialization differs")
    bulk = [(e[6], e[7], e[8], e[3]) for e in events if e[6] in (3, 4)]
    expectedBulk = []
    for role in (1, 2):
        expectedBulk.extend((operation, role, 0, sizes[role]) for operation in (3, 4))
    for image in (1, 2, 1):
        expectedBulk.extend(
            (operation, role, image, 4096)
            for operation, role in ((3, 6), (3, 7), (4, 6), (4, 7))
        )
    for role in (3, 4, 5):
        expectedBulk.extend((operation, role, 0, sizes[role]) for operation in (3, 4))
    if bulk != expectedBulk:
        raise ValueError("physical write-all/read-all pattern protocol differs")

    def fingerprint(physical):
        value = 0xCBF29CE484222325  # Software FNV-1a checksum; no device semantics.
        for offset in range(0, 4096, 4):
            word = (
                ((physical + offset) >> 2) ^ ((physical + offset) >> 32) ^ 0xA53C9E71
            )  # Software upload pattern, Upload.cpp.
            for byte in (word & 0xFFFFFFFF).to_bytes(4, "little"):
                value = ((value ^ byte) * 1099511628211) & (2**64 - 1)
        return value

    witnesses = [(e[0], e[2], e[7], e[3], e[8]) for e in events if e[6] == 7]
    expectedWitness = [
        (phase, virtual, role, fingerprint(byrole[role]), 1)
        for phase, first, second in ((3, 6, 7), (5, 7, 7), (6, 6, 7))
        for virtual, role in ((0, first), (4096, second))
    ]
    if witnesses != expectedWitness:
        raise ValueError("BAR1 page/remap/readback witnesses differ")

    return dict(
        scope="same-context BAR1 positive mapping/update observations only; no channel/DMA payload proof",
        owner=owner,
        allocations=[
            dict(id=r[0], role=r[1], physical=r[2], bytes=r[3], generation=r[4])
            for r in allocations
        ],
        events=len(events),
        bar1_context_writes=values(CONTEXT),
        invalidation_count=3,
        bar_flush_count=17,
        closure="owned BAR1 disabled; all storage retained until reviewed guest/VFIO end",
        S1_complete=False,
    )
