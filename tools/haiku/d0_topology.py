# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Source-checked QEMU 6.2 Q35 topology subset, not a payload/coherency proof.

The ramblock Offset column is internal ram_addr_t, never HVA or GPA. RAM aliases
are resolved from the global memory FlatView against pc.ram used_length.
"""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class RamRegion:
    gpa: int
    size: int
    offset: int


@dataclass(frozen=True)
class Topology:
    regions: tuple[RamRegion,...]
    ram_bytes: int
    ramblock_offset: int
    physical: bool

    def contains(self,gpa,size):
        if type(gpa) is not int or type(size) is not int or gpa<0 or size<=0 or gpa+size>2**64:return False
        return any(r.gpa<=gpa and gpa+size<=r.gpa+r.size for r in self.regions)


def parse(qtree,mtree,ramblock,*,physical):
    for text in (qtree,mtree,ramblock):
        if type(text) is not str or not text or len(text)>1024*1024:raise ValueError('topology size/type')
    devices=[];vfio=[];current=None
    for line in qtree.splitlines():
        device=re.fullmatch(r' *dev: ([^, ]+), id "[^"\n]*"',line)
        if device:
            current=device[1];devices.append(current)
            if current=='vfio-pci':vfio.append([])
        elif current=='vfio-pci':
            host=re.fullmatch(r' +host = "([^"\n]+)"',line)
            if host:vfio[-1].append(host[1])
    if devices.count('q35-pcihost')!=1 or any('iommu' in name.lower() for name in devices):
        raise ValueError('unsupported realized host/IOMMU topology')
    if vfio!=([['0000:04:00.0']] if physical else []):raise ValueError('realized assignment mismatch')
    rows=[]
    for line in ramblock.splitlines():
        match=re.fullmatch(r'\s*pc\.ram\s+\d+ (?:KiB|MiB|GiB)\s+(0x[0-9a-f]{16})\s+(0x[0-9a-f]{16})\s+(0x[0-9a-f]{16})\s*',line)
        if match:rows.append(tuple(int(x,16) for x in match.groups()))
    if len(rows)!=1 or rows[0][1]!=4*1024**3 or rows[0][2]!=rows[0][1]:raise ValueError('RAM backing is not fixed 4 GiB')
    selected=[]
    for block in re.split(r'(?m)^FlatView #[0-9]+\r?$',mtree)[1:]:
        if re.search(r'(?m)^ AS "memory", root: system\r?$',block):selected.append(block)
    if len(selected)!=1:raise ValueError('global memory address space is missing/ambiguous')
    block=selected[0]
    if not re.search(r'(?m)^ Root memory region: system\r?$',block):raise ValueError('memory root mismatch')
    regions=[];last_end=-1;range_count=0
    for line in block.splitlines():
        if not re.match(r'^  [0-9a-f]{16}-',line):continue
        match=re.fullmatch(r'  ([0-9a-f]{16})-([0-9a-f]{16}) \(prio -?[0-9]+, ([^()]+)\): (.+)',line)
        if not match:raise ValueError('unsupported flat range format')
        start,end=int(match[1],16),int(match[2],16);range_count+=1
        if end<start or start<=last_end or range_count>1024:raise ValueError('range ordering/size bound')
        last_end=end
        if match[3]!='ram':continue
        ram=re.fullmatch(r'pc\.ram(?: @([0-9a-f]{16}))?(?: KVM)?',match[4])
        if not ram:continue  # Other RAM/device-backed regions cannot satisfy this role.
        offset=int(ram[1],16) if ram[1] else 0
        if offset+end-start+1>rows[0][1]:raise ValueError('RAM alias exceeds backing')
        regions.append(RamRegion(start,end-start+1,offset))
    if not regions:raise ValueError('no mapped system RAM')
    return Topology(tuple(regions),rows[0][1],rows[0][0],physical)
