#!/usr/bin/env python3
"""Write hardware/record.json and hardware/record.md from the captures.

Usage: tools/hardware_record.py

Reads reference/pci/ (formats: reference/pci/README.md) and writes the
A1 and A2 fields of docs/PHASES.md for every Tesla K40c that the captures
contain. Every value in record.md has the capture file and line it was
read from. Run it again after scripts/capture_user.sh and
scripts/capture_root.sh, for example when a card changes slot.

The chipset is KNOWN only for a card that has a PMC_BOOT_0 read in
reference/pci/root/boot0-*.txt. The read identifies a card by its PCI
address at that time: BOOT0_VALID_FOR below records which GPU UUID the
read belongs to, so a moved card does not inherit it by address alone.
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCI = os.path.join(ROOT, "reference", "pci")
K40C_ID = "10de:1024"
DEV_CARD = "0000:04:00.0"          # development card, listed first (assumption S1)
BASE_C = "reference/nouveau/nvkm/engine/device/base.c"
# boot0 capture -> GPU UUID of the card that was read (from nvidia-proc at
# the time of the read, 2026-10-05).
BOOT0_VALID_FOR = {
    "boot0-0000_04_00_0.txt": "GPU-305da5a6-e0a3-a36a-963b-4c099fd262f5",
}


def lines(rel):
    with open(os.path.join(PCI, rel), errors="replace") as f:
        return f.read().split("\n")


def find(rel, pattern, start=0):
    """Return (1-based line number, match) of the first match from start."""
    for n, text in enumerate(lines(rel)[start:], start + 1):
        m = re.search(pattern, text)
        if m:
            return n, m
    raise SystemExit(f"{rel}: no line matches {pattern!r}")


def size_text(n):
    return f"{n >> 20}M"


def chipset_case(value):
    """Line of base.c that selects the chipset for a BOOT0 chipset field."""
    path = os.path.join(ROOT, BASE_C)
    with open(path, errors="replace") as f:
        for n, text in enumerate(f, 1):
            m = re.search(r"case 0x%03x: device->chip = &(\w+);" % value, text)
            if m:
                return n, m.group(1)
    raise SystemExit(f"{BASE_C}: no case for 0x{value:03x}")


def card(tag):
    addr = "0000:" + tag.replace("_", ":", 1).replace("_", ".")
    vvv, res, sysfs = f"lspci-vvv-{tag}.txt", f"resource-{tag}.txt", f"sysfs-{tag}.txt"
    root_vvv, proc = f"root/lspci-vvv-{tag}.txt", f"nvidia-proc-{tag}.txt"
    src = {}  # field -> "file line N: text"

    def cite(key, rel, n, text=None):
        src[key] = f"`reference/pci/{rel}` line {n}" + (f": `{text}`" if text else "")

    n, m = find(vvv, r"\[([0-9a-f]{4}):([0-9a-f]{4})\] \(rev ([0-9a-f]+)\)")
    pci_id, rev = f"0x{m.group(1)}{m.group(2)}", f"0x{m.group(3)}"
    cite("pci_id", vvv, n, f"[{m.group(1)}:{m.group(2)}]")
    cite("revision", vvv, n, f"(rev {m.group(3)})")
    n, m = find(vvv, r"Subsystem: .*\[([0-9a-f]{4}):([0-9a-f]{4})\]")
    subsys = f"0x{m.group(1)}{m.group(2)}"
    cite("subsystem_id", vvv, n, f"[{m.group(1)}:{m.group(2)}]")

    bars = []
    for i, text in enumerate(lines(res)[:6]):
        f = text.split()
        if len(f) == 3 and int(f[0], 16):
            start, end, flags = (int(x, 16) for x in f)
            bars.append({"index": i, "base": f"0x{start:x}", "size": f"0x{end - start + 1:x}",
                         "flags": f"0x{flags:08x}"})
            cite(f"bar{i}", res, i + 1)

    def sys_value(key):
        n, m = find(sysfs, r"^%s: (.*)$" % key)
        cite(key, sysfs, n, f"{key}: {m.group(1)}")
        return m.group(1)

    numa = int(sys_value("numa_node"))
    speed, width = sys_value("current_link_speed"), int(sys_value("current_link_width"))

    n, m = find(proc, r"^GPU UUID:\s+(\S+)")
    uuid = m.group(1)
    # nvidia-smi -q: the block of this card starts at its "GPU <bus id>" line.
    q = "nvidia-smi-q.txt"
    block, _ = find(q, r"^GPU 0000%s$" % addr)
    n, m = find(q, r"VBIOS Version\s+: (\S+)", block)
    vbios = m.group(1)
    cite("vbios", q, n, f"VBIOS Version : {vbios}")
    n, _ = find(q, r"FB Memory Usage", block)
    n, m = find(q, r"Total\s+: (\d+) MiB", n)
    vram = int(m.group(1))
    cite("vram", q, n, f"Total : {vram} MiB")

    # Chipset: KNOWN only with a BOOT0 read of this card (same GPU UUID).
    chip = None
    for path in sorted(glob.glob(os.path.join(PCI, "root", "boot0-*.txt"))):
        name = os.path.basename(path)
        if BOOT0_VALID_FOR.get(name) != uuid:
            continue
        n, m = find(f"root/{name}", r"PMC_BOOT_0 = 0x([0-9a-f]{8})")
        boot0 = int(m.group(1), 16)
        field = (boot0 >> 20) & 0x1ff
        ln, chipname = chipset_case(field)
        chip = {"value": chipname, "status": "KNOWN",
                "evidence": f"PMC_BOOT_0=0x{boot0:08x} (reference/pci/root/{name}, read on the card "
                            f"with {uuid}); bits[28:20]=0x{field:03x}; {BASE_C}:{ln}: "
                            f"case 0x{field:03x}: device->chip = &{chipname}"}
        src["chipset"] = (f"KNOWN. PMC_BOOT_0=0x{boot0:08x} (`reference/pci/root/{name}` line {n}); "
                          f"bits[28:20]=0x{field:03x}; `{BASE_C}:{ln}`")
    rec = {"pci_address": addr, "pci_id": pci_id, "subsystem_id": subsys, "revision": rev,
           "bars": bars, "numa_node": numa, "vbios": vbios, "vram_mib": vram,
           "link": {"speed": speed, "width": width}, "nouveau_chipset": chip}

    # A2 fields, from the root capture.
    caps, cap_rows = [], []
    for n, text in enumerate(lines(root_vvv), 1):
        m = re.match(r"\s*Capabilities: \[([0-9a-f]+)(?: v(\d+))?\] (.*)$", text)
        if not m:
            continue
        rest, version = m.group(3), m.group(2)
        name = re.split(r" version | \(v\d+\)|:| <\?>", rest)[0].strip()
        if version is None:
            v = re.search(r"version (\d+)|\(v(\d+)\)", rest)
            version = (v.group(1) or v.group(2)) if v else None
        version = int(version) if version is not None else None
        caps.append({"offset": f"0x{m.group(1)}", "name": name, "version": version})
        cap_rows.append((f"0x{m.group(1)}", name, version, n, text.strip()))
    rec["pci_capabilities"] = caps

    n_int, m = find(root_vvv, r"Interrupt: pin (\w) routed to IRQ (\d+)")
    pin, irq = m.group(1), int(m.group(2))
    n_msi, m = find(root_vvv, r"Capabilities: \[([0-9a-f]+)\] MSI: Enable([+-]) "
                              r"Count=(\d+)/(\d+) Maskable([+-]) 64bit([+-])")
    rec["interrupt"] = {"pin": pin, "irq": irq, "msi": {
        "offset": f"0x{m.group(1)}", "enabled": m.group(2) == "+", "count": int(m.group(3)),
        "max_count": int(m.group(4)), "is_64bit": m.group(6) == "+", "maskable": m.group(5) == "+"}}
    n_cap, m = find(root_vvv, r"LnkCap:\s+Port #\d+, Speed ([^,]+), Width x(\d+), ASPM ([^,]+)")
    rec["link_capability"] = {"speed": m.group(1), "width": int(m.group(2)), "aspm": m.group(3)}
    n_sta, m = find(root_vvv, r"LnkSta:\s+(Speed (\S+) \((\w+)\), Width x(\d+) \((\w+)\))")
    sta_ok = (m.group(2).replace("GT/s", "") == speed.split()[0].rstrip("0").rstrip(".")
              and int(m.group(4)) == width)
    extra = {"uuid": uuid, "src": src, "cap_rows": cap_rows, "root_vvv": root_vvv,
             "n_int": n_int, "n_msi": n_msi, "n_cap": n_cap, "n_sta": n_sta,
             "lnksta": m.group(1), "sta_ok": sta_ok}
    return rec, extra


def main():
    tags = []
    for path in sorted(glob.glob(os.path.join(PCI, "lspci-vvv-*.txt"))):
        tag = os.path.basename(path)[len("lspci-vvv-"):-len(".txt")]
        if K40C_ID in lines(f"lspci-vvv-{tag}.txt")[0]:
            tags.append(tag)
    cards = [card(t) for t in tags]
    cards.sort(key=lambda c: c[0]["pci_address"] != DEV_CARD)
    known = next((c for c in cards if c[0]["nouveau_chipset"]), None)
    for rec, extra in cards:
        if rec["nouveau_chipset"] is None:
            if known is None:
                rec["nouveau_chipset"] = {"value": None, "status": "UNKNOWN",
                                          "evidence": "No PMC_BOOT_0 read (Q1)"}
                extra["src"]["chipset"] = "UNKNOWN. No PMC_BOOT_0 read (Q1)"
                continue
            k = known[0]
            rec["nouveau_chipset"] = {
                "value": k["nouveau_chipset"]["value"], "status": "INFERRED",
                "evidence": f"Same PCI ID {rec['pci_id']} and VBIOS {rec['vbios']} as "
                            f"{k['pci_address'][5:]}; PMC_BOOT_0 not read for "
                            f"{rec['pci_address'][5:]} (Q1)"}
            extra["src"]["chipset"] = (f"INFERRED. Same PCI ID and VBIOS as "
                                       f"{k['pci_address'][5:]}; PMC_BOOT_0 not read (Q1)")

    with open(os.path.join(ROOT, "hardware", "record.json"), "w") as f:
        json.dump([c[0] for c in cards], f, indent=2)
        f.write("\n")

    out = [f"# Hardware Record — Tesla K40c ×{len(cards)}", "",
           "Generated by `tools/hardware_record.py` from `reference/pci/`. Do not edit by hand.", ""]
    for r, x in cards:
        s, a, rv = x["src"], r["pci_address"], x["root_vvv"]
        out += [f"## GPU {a}", "", "| Field | Value | Source |", "|-------|-------|--------|",
                f"| PCI ID | {r['pci_id']} | {s['pci_id']} |",
                f"| Subsystem ID | {r['subsystem_id']} | {s['subsystem_id']} |",
                f"| Revision | {r['revision']} | {s['revision']} |"]
        for b in r["bars"]:
            out.append(f"| BAR{b['index']} | {b['base']} / {size_text(int(b['size'], 16))} "
                       f"(flags {b['flags']}) | {s['bar%d' % b['index']]} |")
        out += [f"| NUMA node | {r['numa_node']} | {s['numa_node']} |",
                f"| VBIOS | {r['vbios']} | {s['vbios']} |",
                f"| VRAM | {r['vram_mib']} MiB | {s['vram']} |",
                f"| Link speed | {r['link']['speed']} | {s['current_link_speed']} |",
                f"| Link width | x{r['link']['width']} | {s['current_link_width']} |",
                f"| GPU UUID | {x['uuid']} | `reference/pci/nvidia-proc-{a[5:].replace(':', '_').replace('.', '_')}.txt` |",
                f"| Nouveau chipset | `{r['nouveau_chipset']['value']}` | {s['chipset']} |",
                "", "### PCI Capabilities", "", "| Offset | Name | Version | Source |",
                "|--------|------|---------|--------|"]
        for off, name, ver, n, text in x["cap_rows"]:
            out.append(f"| {off} | {name} | {ver if ver is not None else '—'} | "
                       f"`reference/pci/{rv}` line {n}: `{text}` |")
        i, m = r["interrupt"], r["interrupt"]["msi"]
        lc = r["link_capability"]
        out += ["", "### Interrupt", "", "| Field | Value | Source |", "|-------|-------|--------|",
                f"| Pin | {i['pin']} | `reference/pci/{rv}` line {x['n_int']} |",
                f"| IRQ | {i['irq']} | `reference/pci/{rv}` line {x['n_int']} |",
                f"| MSI offset | {m['offset']} | `reference/pci/{rv}` line {x['n_msi']} |",
                f"| MSI enabled | {str(m['enabled']).lower()} | `reference/pci/{rv}` line {x['n_msi']} |",
                f"| MSI count | {m['count']}/{m['max_count']} | `reference/pci/{rv}` line {x['n_msi']} |",
                f"| MSI 64-bit | {str(m['is_64bit']).lower()} | `reference/pci/{rv}` line {x['n_msi']} |",
                f"| MSI maskable | {str(m['maskable']).lower()} | `reference/pci/{rv}` line {x['n_msi']} |",
                "", "### Link capability", "", "| Field | Value | Source |",
                "|-------|-------|--------|",
                f"| Speed | {lc['speed']} | `reference/pci/{rv}` line {x['n_cap']} |",
                f"| Width | x{lc['width']} | `reference/pci/{rv}` line {x['n_cap']} |",
                f"| ASPM | {lc['aspm']} | `reference/pci/{rv}` line {x['n_cap']} |",
                f"| LnkSta | {x['lnksta']} | `reference/pci/{rv}` line {x['n_sta']}. "
                f"{'Agrees' if x['sta_ok'] else 'DOES NOT AGREE'} with the `link` field "
                f"({r['link']['speed']}, x{r['link']['width']}). |", ""]
    nodes = sorted({c[0]["numa_node"] for c in cards})
    out += ["## Notes", "",
            "- BAR flags are the sysfs resource flags: `0x00040200` is memory, 32-bit, "
            "non-prefetchable; `0x0014220c` is memory, 64-bit, prefetchable.",
            "- NUMA: " + ", ".join(f"{c[0]['pci_address'][5:]} on node {c[0]['numa_node']}"
                                   for c in cards)
            + (". Both cards are on one node." if len(nodes) == 1 else "."),
            "- Q1 (`docs/OPEN_QUESTIONS.md`): the chipset is KNOWN only for a card with a "
            "PMC_BOOT_0 read.", ""]
    with open(os.path.join(ROOT, "hardware", "record.md"), "w") as f:
        f.write("\n".join(out))
    print(f"wrote hardware/record.json and hardware/record.md for "
          f"{', '.join(c[0]['pci_address'] for c in cards)}")


if __name__ == "__main__":
    main()
