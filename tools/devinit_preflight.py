#!/usr/bin/env python3
# Copyright 2026 Mario Andrés Muñoz.
# Distributed under the terms of the MIT License.
"""Conservative raw-ROM structural preflight, never executes hardware effects.

Follows all direct/table calls and both conditional jump alternatives. Conditions
are not evaluated. Numeric listing/table rows are not treated as instructions.
Only aggregate/control-flow issues are written, never decoded firmware payloads.
"""
import argparse
from collections import Counter
import hashlib
import json
import lzma
from pathlib import Path
import os
import re
import devinit_inventory
ROOT=Path(__file__).resolve().parent.parent
EXPECTED='aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54'


def preflight(rom):
    def read(offset,size):
        if offset<0 or offset>len(rom) or size>len(rom)-offset:raise ValueError(f'ROM bounds at {offset:#x}')
        return int.from_bytes(rom[offset:offset+size],'little')
    bit=rom.find(b'\xff\xb8BIT')
    if bit<0:raise ValueError('BIT signature absent')
    count=read(bit+10,1);stride=read(bit+9,1)
    if stride<6:raise ValueError('invalid BIT entry stride')
    entries={}
    for i in range(count):
        at=bit+12+i*stride
        ident=chr(read(at,1));version=read(at+1,1);size=read(at+2,2);offset=read(at+4,2)
        read(offset,size);entries[ident]=(version,size,offset)
    if 'I' not in entries or 'M' not in entries:raise ValueError('missing BIT I/M')
    iv,il,ip=entries['I'];mv,ml,mp=entries['M']
    if iv!=1 or il<14:raise ValueError('unreviewed BIT I version/length')
    groups=read(mp+(2 if mv==1 else 0),1) if (mv==1 and ml>=5) or (mv==2 and ml>=3) else 0
    table=read(ip,2);scripts=[]
    if not table:raise ValueError('missing init script table')
    for i in range(256):
        pointer=read(table+2*i,2)
        if not pointer:break
        scripts.append(pointer)
    else:raise ValueError('unterminated script pointer table')
    if not scripts:raise ValueError('empty main script table')
    extra=read(ip+14,2) if il>=16 else 0
    roots=scripts+([extra] if extra else [])
    pending=list(roots);visited={};issues=[];calls=0
    fixed={0x33:2,0x36:1,0x38:1,0x53:3,0x56:3,0x5b:3,0x5c:3,0x5f:22,0x69:5,0x6b:2,0x6e:13,0x6f:2,0x71:1,0x72:1,0x74:3,0x75:2,0x7a:9,0x8c:1,0x8d:1,0x8e:1,0x90:9,0x97:13}
    while pending:
        pc=pending.pop();loops=[]
        while pc not in visited:
            try:
                opcode=read(pc,1);length=fixed.get(opcode)
                if opcode==0x4d:length=4+2*read(pc+3,1)
                elif opcode in (0x58,0x91):length=6+4*read(pc+5,1)
                elif opcode==0x8f:
                    if not groups:raise ValueError('RAM group count unavailable')
                    length=7+4*read(pc+6,1)*groups
                elif opcode==0xa9:length=2+read(pc+1,1)
                elif opcode==0x3a:length=3+(0 if read(pc+1,1) in (0,1,2,5,7) else read(pc+2,1))
                if length is None:
                    issues.append(dict(offset=hex(pc),kind='unsupported_length',opcode=hex(opcode)));break
                read(pc,length);visited[pc]=opcode
                if opcode==0x33:
                    if not read(pc+1,1):issues.append(dict(offset=hex(pc),kind='zero_repeat'))
                    loops.append(pc)
                elif opcode==0x36:
                    if loops:loops.pop()
                    else:issues.append(dict(offset=hex(pc),kind='unstructured_repeat_end'))
                elif opcode in (0x5b,0x5c,0x6b):
                    target=read(pc+1,2) if opcode!=0x6b else read(table+2*read(pc+1,1),2)
                    if not target:issues.append(dict(offset=hex(pc),kind='null_call_or_jump'))
                    else:pending.append(target);calls+=1
                if opcode==0x71:
                    if loops:issues.append(dict(offset=hex(pc),kind='done_inside_repeat'))
                    break
                pc+=length
                if len(visited)>65536:raise ValueError('instruction budget exceeded')
            except ValueError as error:
                issues.append(dict(offset=hex(pc),kind='bounds_or_format',detail=str(error)));break
    return dict(bit_offset=hex(bit),main_scripts=[hex(p) for p in scripts],extra_script=hex(extra),ram_groups=groups,
                condition_table=hex(read(ip+6,2)),macro_table=hex(read(ip+4,2)),potential_instruction_count=len(visited),
                opcodes={f'0x{op:02x}':n for op,n in sorted(Counter(visited.values()).items())},
                call_or_jump_edges=calls,issues=issues,structural_coverage_complete=not issues),visited


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--rom',type=Path,default=Path(os.environ.get('K40_VBIOS',str(Path.home()/'mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom'))).expanduser());parser.add_argument('--check',action='store_true');args=parser.parse_args()
    rom=args.rom.read_bytes()
    if hashlib.sha256(rom).hexdigest()!=EXPECTED:raise ValueError('ROM identity mismatch')
    report,visited=preflight(rom)
    log=devinit_inventory.parse_log(lzma.open(devinit_inventory.LOG,'rt').read())
    observed={int(i['offset'],16) for i in log if int(i['offset'],16)}
    report.update(rom_sha256=EXPECTED,scope='conservative structural reachability; not runtime paths/helpers/readiness',observed_offsets_not_covered=[hex(o) for o in sorted(observed-set(visited))])
    nv=(ROOT/'reference/nouveau/nvkm/subdev/bios/init.c').read_text().splitlines()
    report['opcode_sources']={f'0x{op:02x}':next(f'reference/nouveau/nvkm/subdev/bios/init.c:{i}' for i,line in enumerate(nv,1) if re.search(r'\[0x%02x\].*init_'%op,line)) for op in sorted(set(visited.values()))}
    path=ROOT/'analysis/devinit_preflight.json';text=json.dumps(report,indent=2,sort_keys=True)+'\n'
    if args.check:return 0 if path.is_file() and path.read_text()==text else 1
    path.write_text(text);print('ROM structural preflight:',report['potential_instruction_count'],'instructions;',len(report['issues']),'issues; uncovered observed offsets',len(report['observed_offsets_not_covered']))
    return 0
if __name__=='__main__':raise SystemExit(main())
