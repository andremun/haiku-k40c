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
        r"^k40_mem: MAP bar=0 base=([0-9a-f]+) resource=(\d+) mapped=16777216 flags=explicit-UC status=(\d+)\r?$",
        serial,
        re.M,
    )
    map1 = re.findall(
        r"^k40_mem: MAP bar=1 base=([0-9a-f]+) resource=(\d+) mapped=8192 flags=explicit-UC read-write status=(\d+)\r?$",
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


CHID = 1  # memstage/ChannelImage.h; trace line 562290.
GP_GET, GP_PUT = 0x288, 0x28C  # cla16f.h:62-63 in USERD slot CHID*0x200.
GPFIFO_VA, PUSH_VA = 0x10000000, 0x10001000  # software channel VA layout.
PB_ROLES = (8, 9, 10, 11, 12, 13, 14)  # ChanDirectory..Runlist, VramArena.h.
# S2 (stage S2_A7_BAR1_CHANNEL_COPY): CopySource and CopyDest, one copy as
# nouveau_boa0b5.c:37-71 on subchannel 4 (include/nvif/push906f.h:19).
COPY_STAGE = "S2_A7_BAR1_CHANNEL_COPY"
COPY_ROLES = (15, 16)
SOURCE_VA, DEST_VA = 0x10002000, 0x10003000  # software channel VA layout.
COPY_BYTES = 4096  # one small page; nouveau_boa0b5.c:57-59 PAGE_SIZE.
CE_INTR, CE_LAUNCHERR = 0x104908, 0x104F14  # ce/gk104.c:52,64-65, CE0.


def header(op, count, subchannel, method):
    # include/nvhw/class/cl906f.h:54-70: SEC_OP 31:29, count 28:16, subchannel 15:13, method/4 11:0.
    return (op << 29) | (count << 16) | (subchannel << 13) | (method >> 2)


def copy_words():
    """The twelve 32-bit words of the copy sequence, from the class headers."""
    launch = 2 | (1 << 2) | (1 << 7) | (1 << 8) | (1 << 9)  # cla0b5.h:38-61; nouveau_boa0b5.c:61-71.
    return [
        header(1, 1, 4, 0x0000), 0xA0B5,  # nouveau_boa0b5.c:85; nouveau_bo.c:937.
        header(1, 8, 4, 0x0400),  # cla0b5.h:94 OFFSET_IN_UPPER.
        (SOURCE_VA >> 32) & 0xFF, SOURCE_VA & 0xFFFFFFFF,  # cla0b5.h:94-97.
        (DEST_VA >> 32) & 0xFF, DEST_VA & 0xFFFFFFFF,  # cla0b5.h:98-101.
        COPY_BYTES, COPY_BYTES, COPY_BYTES, 1,  # cla0b5.h:102-109 pitches, line length, line count.
        header(4, launch, 4, 0x0300),  # cla0b5.h:37 LAUNCH_DMA, immediate.
    ]


def pte(physical, writable=False):
    # vmmgf100.c:313-316 valid, RO bit 2 unless writable; VRAM, kind 0.
    return (physical >> 8) | (1 if writable else 5)


def channel_image(byrole, copy=False):
    """Independent re-encoding of memstage/ChannelImage.cpp from pinned sources."""
    userd = byrole[11] + CHID * 0x200  # fifo/gk104.c:84,88-89,117.
    ramfc = [
        (0x08, userd),
        (0x10, 0xFACE),  # fifo/gk104.c:90.
        (0x30, 0xFFFFF902),  # fifo/gk104.c:91.
        (0x48, (GPFIFO_VA & 0xFFFFFFFF) | (((GPFIFO_VA >> 32) | (9 << 16)) << 32)),  # gk104.c:85,92-93.
        (0x80, 0x20400000 << 32),  # gk104.c:94.
        (0x90, 0x30000001 << 32),  # gk104.c:95; devm 1, trace 562278.
        (0x98, 0x100 << 32),  # gk104.c:96.
        (0xA8, 0x1F << 32),  # gk104.c:97.
        (0xB8, 0xF8000000),  # gk104.c:100.
        (0xE0, 0x20 << 32),  # gk104.c:98.
        (0xE8, CHID),  # gk104.c:99.
        (0xF8, 0x10003080 | (0x10000010 << 32)),  # gk104.c:101-102.
        (0x200, byrole[8]),  # vmmgf100.c:346-360.
        (0x208, (1 << 40) - 1),
    ]
    if copy:
        words = [(1 << 29) | (1 << 16) | (0x08 >> 2), 0, *copy_words()]
        push = [
            (index * 4, words[index] | (words[index + 1] << 32))
            for index in range(0, len(words), 2)
            if words[index] or words[index + 1]
        ]
        second = PUSH_VA + 8  # after the NOP.
        return {
            8: [((GPFIFO_VA >> 27) * 8, (byrole[9] << 24) | (1 << 32))],
            9: [
                (((GPFIFO_VA >> 12) & 32767) * 8, pte(byrole[12])),
                (((PUSH_VA >> 12) & 32767) * 8, pte(byrole[13])),
                (((SOURCE_VA >> 12) & 32767) * 8, pte(byrole[15])),
                (((DEST_VA >> 12) & 32767) * 8, pte(byrole[16], True)),  # destination writable.
            ],
            10: ramfc,
            11: [],
            12: [
                (0, (PUSH_VA & 0xFFFFFFFF) | (((PUSH_VA >> 32) | (8 << 8)) << 32)),
                (8, (second & 0xFFFFFFFF) | (((second >> 32) | (48 << 8)) << 32)),  # nouveau_dma.c:83-84.
            ],
            13: push,
            14: [(0, CHID)],
        }
    return {
        8: [((GPFIFO_VA >> 27) * 8, (byrole[9] << 24) | (1 << 32))],  # vmmgf100.c:129-140.
        9: [
            (((GPFIFO_VA >> 12) & 32767) * 8, pte(byrole[12])),
            (((PUSH_VA >> 12) & 32767) * 8, pte(byrole[13])),
        ],
        10: ramfc,
        11: [],
        12: [(0, (PUSH_VA & 0xFFFFFFFF) | (((PUSH_VA >> 32) | (8 << 8)) << 32))],  # nouveau_dma.c:83-84.
        13: [(0, (1 << 29) | (1 << 16) | (0x08 >> 2))],  # dma-pusher.rst:417; cla16f.h:74.
        14: [(0, CHID)],  # fifo/gk104.c:454-455.
    }


def copy_phase(serial, chan, engine):
    """S2: second entry consumed, engine idle, no launch error, destination compared."""
    line = re.findall(
        r"^k40_mem: COPY engine=(\d+) submitted=1 get=2/2 polls=\d+ us=\d+ copied=1\r?$", serial, re.M
    )
    status = re.findall(
        r"^k40_mem: COPY_STATUS engine=([0-9a-f]+) idle_polls=\d+ idle_us=\d+ ce_intr=([0-9a-f]+) launcherr=([0-9a-f]+)\r?$",
        serial,
        re.M,
    )
    if len(line) != 1 or len(status) != 1 or int(line[0]) != engine:
        raise ValueError("copy report missing, repeated or not complete")
    busy, intr, error = (int(x, 16) for x in status[0])
    if busy & 0x80000000 or intr & 4 or error & 15:
        raise ValueError("copy engine busy or launch error")  # fifo/gk104.c:208; ce/gk104.c:52,76.
    register = 0x2640 + engine * 8  # fifo/gk104.c:206.
    if not any(e[6] == 2 and e[0] == 13 and e[2] == GP_GET and e[3] == 2 for e in chan):
        raise ValueError("GP_GET poll for the copy entry missing")
    if not any(e[6] == 2 and e[0] == 13 and e[2] == register and not e[3] & 0x80000000 for e in chan):
        raise ValueError("engine idle poll missing")
    for address, mask in ((CE_INTR, 4), (CE_LAUNCHERR, 15)):
        values = [e[3] for e in chan if e[6] == 0 and e[0] == 13 and e[2] == address]
        if len(values) != 1 or values[0] & mask:
            raise ValueError("copy-engine status read missing or in error")
    return dict(engine=engine, bytes=COPY_BYTES, source_va=SOURCE_VA, dest_va=DEST_VA)


# S3 stages: the compute stage replaces the CE0 channel (src/gr/Compute.cpp).
GR_STAGES = {"S3A_A7_BAR1_GR_GOLDEN": False, "S3B_A7_BAR1_GR_COMPUTE": True}  # value: with launch.
GR_ROLES = tuple(range(17, 29))  # GrText..GrMmioList, VramArena.h.
GR_UNWRITTEN = (18, 24, 25, 26)  # Tls, PagePool, Bundle, Attrib: allocated, never written by the host.


def gr_program():
    """Stage lengths of the generated program, from the generator (not from the driver)."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "gr/program.py"
    spec = importlib.util.spec_from_file_location("k40_gr_program", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    stages, patches, _, _ = module.record()
    stages.update(module.fifo_stages())
    return {name: len(ops) for name, ops in stages.items()}, len(patches), module.launch.layout()


def gr_phase(serial, events, byrole, launch):
    """Validate an S3 run: program progress, context, launch result, faults, teardown."""
    lengths, _, layout = gr_program()
    flag = "1" if launch else "0"
    if len(re.findall(
        rf"^k40_mem: GR step=15 error=0 bound=1 started=1 golden=1 attached=1 submitted={flag} consumed={flag} computed={flag} closed=1\r?$",
        serial, re.M,
    )) != 1:
        raise ValueError("GR report missing or stage not complete")
    order = ("fifo", "bind", "gating", "start", "golden", "attach")
    total = sum(lengths[name] for name in order)
    program = re.findall(r"^k40_mem: GR_PROGRAM ops=(\d+) reads=\d+ writes=\d+ guard=(\d+)/(\d+) total_us=(\d+)\r?$", serial, re.M)
    if len(program) != 1 or (int(program[0][0]), int(program[0][1]), int(program[0][2])) != (total, 6, lengths["teardown"]):
        raise ValueError("GR program progress or guard position differs")
    if serial.count("k40_mem: GR_FAILURE runner=0 index=0 addr=0 value=0 expected=0 closing=0 closing_index=0") != 1:
        raise ValueError("GR failure record")
    got = re.findall(r"^k40_mem: GR_GET after=(\d+)/(\d+) polls=\d+ us=\d+ result_polls=\d+ result_us=\d+ wrong=(\d+) first=\d+ value=[0-9a-f]+\r?$", serial, re.M)
    if len(got) != 1 or tuple(map(int, got[0])) != ((1, 1, 0) if launch else (0, 0, 0)):
        raise ValueError("GP_GET progress or result compare differs")
    status = re.findall(
        r"^k40_mem: GR_STATUS mc=[0-9a-f]+ fifo=([0-9a-f]+) mmu=0 pbdma=0 hce=0 state=[0-9a-f]+ gr=0 trap=0 fecs=0 engine=([0-9a-f]+)\r?$",
        serial, re.M,
    )
    if len(status) != 1 or int(status[0][0], 16) & 0x3FFFFFFF:
        raise ValueError("GR, FECS, FIFO or MMU fault status")  # fifo/gk104.c:654-718; gr/gf100.c:1414,1570.
    image = re.findall(r"^k40_mem: GR_IMAGE ((?:[0-9a-f]+ ){7}[0-9a-f]+)\r?$", serial, re.M)
    if len(image) != 1:
        raise ValueError("golden image words missing")
    chan = [e for e in events if e[0] >= 8]
    stages, done = [(e[2], e[3], e[8]) for e in chan if e[6] == 8], 0
    expected = []
    for number, name in enumerate(order):
        done += lengths[name]
        expected.append((number, done, 1))
    if stages != expected:
        raise ValueError("program stage records differ")
    context = 0x80000000 | (byrole[5] >> 12)  # bar/gf100.c:56-58.
    writes = [(e[2], e[3]) for e in chan if e[6] == 1 and e[2] not in (WINDOW, FLUSH)]
    wanted = [(PDB, (byrole[3] >> 12) << 4), (INVALIDATE, 0x80000005), (CONTEXT, context)]
    wanted += [(GP_PUT, 1)] if launch else []
    wanted += [(CONTEXT, context & 0x7FFFFFFF)]
    if writes != wanted:
        raise ValueError("journaled mapping, GP_PUT or BAR1 context writes differ")
    if launch:
        blocks = [e for e in chan if e[6] == 4 and e[7] == 23 and e[3] == 256]
        if len(blocks) != 16 or [e[2] for e in blocks] != [index * 256 for index in range(16)]:
            raise ValueError("output buffer was not read completely")
    return dict(
        program_ops=total, guard_position=[6, lengths["teardown"]], golden_image_words=image[0].split(),
        total_us=int(program[0][3]), launch=launch,
        context_va=layout["Context"]["va"] + 0x80000, records=len(GR_ROLES),
    )


def channel_phase(serial, events, byrole, copy=False):
    """Validate phases 8-14: exact write order, NOP progress, faults, teardown."""
    line = re.findall(
        r"^k40_mem: CHANNEL runlist=(\d+) pbdma=(\d+) mask=([0-9a-f]+) runm=([0-9a-f]+) bound=1 closed=1 progress=1 error=0 step=24\r?$",
        serial,
        re.M,
    )
    if len(line) != 1:
        raise ValueError("channel report missing or not consumed/closed")
    rl, pb, mask = int(line[0][0]), int(line[0][1]), int(line[0][2], 16)
    routes = re.findall(
        r"^k40_mem: ROUTE type=1 instance=0 address=[0-9a-f]+ fault=\S+ runlist=1/(\d+) ", serial, re.M
    )
    if routes != [str(rl)] or not mask & (1 << pb) or rl > 15:
        raise ValueError("CE0 runlist/PBDMA route differs")  # top/gk104.c:79; gk104.c:392.
    if serial.count("k40_mem: CHANNEL_GET before=0/0 after=1/1 ") != 1:
        raise ValueError("GP_GET did not advance from 0 to GP_PUT 1")
    status = re.findall(
        r"^k40_mem: CHANNEL_STATUS mc=([0-9a-f]+) fifo=([0-9a-f]+) mmu=0 pbdma=0 hce=0 state=([0-9a-f]+)\r?$",
        serial,
        re.M,
    )
    if len(status) != 1 or int(status[0][1], 16) & 0x3FFFFFFF:
        raise ValueError("channel fault/status")  # gk104.c:654-718.
    chan = [e for e in events if e[0] >= 8]
    if [e[3] for e in chan if e[0] == 8 and e[2] == MC and e[6] == 0] != [0]:
        raise ValueError("channel baseline MC dirty")
    image = channel_image(byrole, copy)
    patches = [(e[0], e[7], e[2], e[3]) for e in chan if e[6] == 5]
    expected = [(9, role, offset, value) for role in PB_ROLES for offset, value in image[role]]
    expected.append((10, 4, 0, pte(byrole[11], True)))  # BAR1 VA 0 -> USERD page.
    if patches != expected:
        raise ValueError("channel image serialization differs")
    bulk = [(e[6], e[7], e[8], e[3]) for e in chan if e[6] in (3, 4)]
    sizes = {8: 65536, 9: 262144}
    zeroed = PB_ROLES + (COPY_ROLES if copy else ())
    expectedBulk = [(op, role, 0, sizes.get(role, 4096)) for role in zeroed for op in (3, 4)]
    if copy:
        # Source pattern written and verified before the bind; destination
        # compared with the source pattern after the copy (image 1, Upload.cpp).
        expectedBulk += [(3, 15, 1, COPY_BYTES), (4, 15, 1, COPY_BYTES), (4, 16, 1, COPY_BYTES)]
    if bulk != expectedBulk:
        raise ValueError("channel zeroing/pattern/compare protocol differs")
    if copy:
        final = [i for i, e in enumerate(chan) if e[6] == 4 and e[7] == 16 and e[8] == 1]
        put = [i for i, e in enumerate(chan) if e[6] == 1 and e[2] == GP_PUT and e[3] == 2]
        if len(final) != 1 or len(put) != 1 or final[0] < put[0]:
            raise ValueError("destination compare is not after the copy submission")
    last, writes = {}, []
    for e in chan:
        if e[6] == 0:
            last[e[2]] = e[3]
        elif e[6] == 1 and e[2] not in (WINDOW, FLUSH):
            writes.append((e[0], e[2], e[3], dict(last)))
    state, reg = 0x800004 + CHID * 8, 0x800000 + CHID * 8  # fifo/gk104.c:44-77.
    context = 0x80000000 | (byrole[5] >> 12)  # bar/gf100.c:56-58.
    control = 0x04013C + pb * 0x2000  # gf100.c:357.
    plan = [
        (9, PDB, lambda r: (byrole[8] >> 12) << 4),  # vmmgf100.c:216.
        (9, INVALIDATE, lambda r: 0x80000001),  # vmmgf100.c:221,230 PAGE_ALL.
        (10, PDB, lambda r: (byrole[3] >> 12) << 4),
        (10, INVALIDATE, lambda r: 0x80000005),
        (10, CONTEXT, lambda r: context),
        (11, 0x200, lambda r: 0xFFFFFFFF),  # mc/nv04.c:120; trace line 47330.
        (11, 0x204, lambda r: 0xFFFFFFFF),  # gf100.c:927-934.
        (11, 0x204, lambda r: r[0x204]),  # gk104.c:739 present mask.
        (11, 0x2A04, lambda r: r[0x2A04] | 0xBFFFFFFF),  # gk104.c:740.
        (11, control, lambda r: r[control] & ~0x10000100 & 0xFFFFFFFF),
        (11, 0x2254, lambda r: 0x10000000),  # gk104.c:749.
        (12, state, lambda r: rl << 16),  # gk104.c:77 from inactive 0.
        (12, reg, lambda r: 0x80000000 | (byrole[10] >> 12)),  # gk104.c:68.
        (12, state, lambda r: r[state] | 0x400),  # gk104.c:52.
        (12, 0x2270, lambda r: byrole[14] >> 12),  # gk104.c:446.
        (12, 0x2274, lambda r: (rl << 20) | 1),  # gk104.c:447.
        (13, GP_PUT, lambda r: 1),  # nouveau_dma.c:92.
        *([(13, GP_PUT, lambda r: 2)] if copy else []),  # second entry, S2 only.
        (14, state, lambda r: r[state] | 0x800),  # gk104.c:44.
        (14, 0x2634, lambda r: CHID),  # gf100.c:43.
        (14, 0x2270, lambda r: byrole[14] >> 12),
        (14, 0x2274, lambda r: rl << 20),
        (14, reg, lambda r: 0),  # gk104.c:60.
        (14, CONTEXT, lambda r: context & 0x7FFFFFFF),  # bar/gf100.c:46-49.
    ]
    if len(writes) != len(plan):
        raise ValueError("channel register write count differs")
    for (phase, address, value, reads), (wantPhase, wantAddress, rule) in zip(writes, plan):
        if (phase, address) != (wantPhase, wantAddress) or value != rule(reads):
            raise ValueError(f"channel write {address:x} differs")
    if reads_of(chan, state, 12) != [0] or reads_of(chan, reg, 12) != [0]:
        raise ValueError("selected channel was not inactive before bind")
    if not any(e[6] == 2 and e[0] == 13 and e[2] == GP_GET and e[3] == 1 for e in chan):
        raise ValueError("GP_GET progress poll missing")
    for phase, address in ((12, 0x2284 + rl * 8), (14, 0x2634), (14, 0x2284 + rl * 8)):
        if not any(e[6] == 2 and e[0] == phase and e[2] == address and not e[3] & 0x100000 for e in chan):
            raise ValueError("runlist/preempt completion poll missing")  # gk104.c:426; gf100.c:372.
    result = dict(runlist=rl, pbdma=pb, pbdma_mask=mask, writes=len(writes))
    if copy:
        engines = re.findall(
            r"^k40_mem: ROUTE type=1 instance=0 address=[0-9a-f]+ fault=\S+ runlist=\S+ engine=1/(\d+)\r?$", serial, re.M
        )
        if len(engines) != 1:
            raise ValueError("CE0 engine ID missing")  # top/gk104.c:55-56.
        result["copy"] = copy_phase(serial, chan, int(engines[0]))
    elif "k40_mem: COPY" in serial:
        raise ValueError("copy report in an S1 run")
    return result


def reads_of(events, address, phase):
    return [e[3] for e in events if e[6] == 0 and e[0] == phase and e[2] == address][:1]


def memory_final(serial, suite, request):
    copy = suite.get("stage") == COPY_STAGE
    gr = suite.get("stage") in GR_STAGES
    launch = GR_STAGES.get(suite.get("stage"), False)
    marker = (
        "k40_mem: PASS S2_COPY faults=0 upload=0 mapper=0 closure=2 allocations=16 journal_overflow=0"
        if copy
        else "k40_mem: PASS S1_CHANNEL_NOP faults=0 upload=0 mapper=0 closure=2 allocations=14 journal_overflow=0"
    )
    if gr:
        marker = f"k40_mem: PASS {'S3_COMPUTE' if launch else 'S3_GOLDEN'} faults=0 upload=0 mapper=0 closure=2 allocations=26 journal_overflow=0"
    if serial.count("k40_mem: PASS ") != 1:
        raise ValueError("pass marker of another stage or repeated")
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
    sizes = {1: 131072, 2: 131072, 3: 65536, 4: 262144, 5: 4096, 6: 4096, 7: 4096,
             8: 65536, 9: 262144, 10: 4096, 11: 4096, 12: 4096, 13: 4096, 14: 4096}
    generations = {1: 1, 2: 1, 3: 2, 4: 6, 5: 3, 6: 3, 7: 3,
                   8: 2, 9: 3, 10: 15, 11: 1, 12: 2, 13: 2, 14: 2}
    roles = (1, 2, 6, 7, 3, 4, 5, *PB_ROLES)
    if copy:
        # Two more table entries, one more GPFIFO entry, six more push words;
        # source: zero then pattern; destination: zero only (never written by the host again).
        roles += COPY_ROLES
        sizes.update({15: 4096, 16: 4096})
        generations.update({9: 5, 12: 3, 13: 8, 15: 2, 16: 1})
    flags = {}
    if gr:
        # Directory and table: zero and one bulk store. Instance: zero, 14 words, two
        # context-pointer updates. One GPFIFO entry, the push words, one runlist entry.
        from tools.gr import launch as images  # layout sizes, from the generator.

        layout = images.layout()
        roles += GR_ROLES
        sizes.update({17 + index: region["bytes"] for index, region in enumerate(layout.values())})
        generations.update({8: 2, 9: 2, 10: 17, 11: 1, 12: 2, 13: 2, 14: 2,
                            17: 2, 19: 1, 20: 2, 21: 2, 22: 2, 23: 1, 27: 2, 28: 2})
        generations.update({role: 0 for role in GR_UNWRITTEN})
        flags = {role: (0, 0, 0) for role in GR_UNWRITTEN}
    cursor = 256 * 1024 + 4096
    byrole = {}
    if len(allocations) != len(roles):
        raise ValueError("allocation ledger incomplete")
    for index, record in enumerate(allocations, 1):
        ident, role, address, size, generation, staged, referenced, retained = record
        if (
            ident != index
            or role != roles[index - 1]
            or address != cursor
            or size != sizes[role]
            or generation != generations[role]
            or (staged, referenced, retained) != flags.get(role, (1, 1, 1))
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
        if event[1] or event[0] > 14 or event[6] > (8 if gr else 7):
            raise ValueError("memory error/unknown diagnostic event")
        events.append(event)
    if not events or len(events) > 4096:
        raise ValueError("diagnostic coverage/bound")
    for phase in range(8):
        if [(e[3]) for e in events if e[0] == phase and e[2] == MC and e[6] == 0] != [
            0
        ]:
            raise ValueError("raw per-phase MC baseline missing/dirty")
    batch1 = [e for e in events if e[0] <= 7]
    writes = [(e[0], e[2], e[3]) for e in batch1 if e[6] == 1]
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
    patches = [(e[0], e[7], e[2], e[3]) for e in batch1 if e[6] == 5]
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
    bulk = [(e[6], e[7], e[8], e[3]) for e in batch1 if e[6] in (3, 4)]
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

    witnesses = [(e[0], e[2], e[7], e[3], e[8]) for e in batch1 if e[6] == 7]
    expectedWitness = [
        (phase, virtual, role, fingerprint(byrole[role]), 1)
        for phase, first, second in ((3, 6, 7), (5, 7, 7), (6, 6, 7))
        for virtual, role in ((0, first), (4096, second))
    ]
    if witnesses != expectedWitness:
        raise ValueError("BAR1 page/remap/readback witnesses differ")

    if gr:
        if "k40_mem: COPY" in serial:
            raise ValueError("copy report in an S3 run")
        return dict(
            scope=(
                "S3: one compute job on the card, out[i] = in[i] + 1 for 1024 elements, every element checked by slow-window readback, "
                "no fault, clean teardown; no host DMA payload proof"
                if launch
                else "S3a: GR engine started, golden context generated and attached to one channel of the GR runlist, no fault, clean teardown; no compute job"
            ),
            gr=gr_phase(serial, events, byrole, launch),
            owner=owner,
            allocations=[dict(id=r[0], role=r[1], physical=r[2], bytes=r[3], generation=r[4]) for r in allocations],
            events=len(events),
            closure="owned BAR1 disabled; channel unbound; GR engine left started; all storage retained until reviewed guest/VFIO end",
            S1_complete=False,
            S2_complete=False,
            S3_golden_complete=True,
            S3_complete=launch,
        )
    if "k40_mem: GR" in serial:
        raise ValueError("GR report in an S1 or S2 run")
    channel = channel_phase(serial, events, byrole, copy)
    return dict(
        scope=(
            "S2: after the S1 NOP, one 4096-byte copy between two owned VRAM pages on the same CE0-runlist channel, "
            "destination equal to source by slow-window readback, no fault, clean teardown; no host DMA payload proof"
            if copy
            else "S1: one host NOP consumed on one CE0-runlist channel (GP_GET 0->1), no fault, clean teardown; no DMA payload proof"
        ),
        S2_complete=copy,
        channel=channel,
        owner=owner,
        allocations=[
            dict(id=r[0], role=r[1], physical=r[2], bytes=r[3], generation=r[4])
            for r in allocations
        ],
        events=len(events),
        bar1_context_writes=values(CONTEXT),
        invalidation_count=3,
        bar_flush_count=17,
        closure="owned BAR1 disabled; channel unbound; all storage retained until reviewed guest/VFIO end",
        S1_complete=True,
    )
