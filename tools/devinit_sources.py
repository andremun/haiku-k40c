#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Generate an opcode/source cross-reference, not executable firmware data."""
import argparse
import hashlib
import json
from pathlib import Path
import os
import re
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent.parent

def generate():
    rompath=Path(os.environ.get('K40_VBIOS',str(Path.home()/'mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom'))).expanduser()
    rom=rompath.read_bytes()
    if hashlib.sha256(rom).hexdigest()!='aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54':
        raise ValueError('unexpected ROM identity')
    inventory=json.loads((ROOT/'analysis/devinit_inventory.json').read_text())
    import devinit_inventory as inv
    import lzma
    instructions=inv.parse_log(lzma.open(inv.LOG,'rt').read())
    selected={rom[int(i['offset'],16)]:i['name'] for i in instructions if int(i['offset'],16)}
    observed=set(selected)
    preflight=json.loads((ROOT/'analysis/devinit_preflight.json').read_text())
    for opcode in preflight['opcodes']:
        selected.setdefault(int(opcode,16),'ZM_REG_GROUP' if int(opcode,16)==0x91 else 'UNOBSERVED')
    nouveau=ROOT/'reference/nouveau/nvkm/subdev/bios/init.c'
    decoder=ROOT/'reference/envytools/nvbios/nvbios.c'
    spec=ROOT/'reference/open-gpu-doc/Devinit/devinit.xml'
    nvlines=nouveau.read_text().splitlines(); declines=decoder.read_text().splitlines(); splines=spec.read_text().splitlines()
    xml={int(n.attrib['value'],0):n.attrib for n in ET.parse(spec).findall('.//opcode')}
    entries=[]
    board={0x4d,0x53,0x69,0x8e,0xa9}
    for opcode,name in sorted(selected.items()):
        dispatch=next((n,line) for n,line in enumerate(nvlines,1) if re.search(r'\[0x%02x\].*init_'%opcode,line))
        handler=re.search(r'\{ (init_\w+)',dispatch[1])[1]
        handlerline=next(n for n,line in enumerate(nvlines,1) if line.startswith(handler+'('))
        decl=next(n for n,line in enumerate(declines,1) if re.search(r'case 0x%02x:'%opcode,line))
        spl=next(n for n,line in enumerate(splines,1) if '<opcode ' in line and re.search(r'value="0x%02x"'%opcode,line,re.I))
        entries.append(dict(opcode=f'0x{opcode:02x}',observed_name=name,observed_in_log=opcode in observed,nvidia=xml[opcode],nvidia_source=f'reference/open-gpu-doc/Devinit/devinit.xml:{spl}',nouveau_source=f'reference/nouveau/nvkm/subdev/bios/init.c:{handlerline}',dispatch_source=f'reference/nouveau/nvkm/subdev/bios/init.c:{dispatch[0]}',decoder_source=f'reference/envytools/nvbios/nvbios.c:{decl}',implementation='delegated; default-denied board/helper operation' if opcode in board else 'host simulation core',evidence='SOURCE_ONLY; observed occurrence in Linux log is separate'))
    return dict(scope='observed opcode source cross-reference; not full reachability',rom_sha256=hashlib.sha256(rom).hexdigest(),opcodes=entries,source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (nouveau,decoder,spec)},observed_names=len(inventory['opcodes']))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=json.dumps(generate(),indent=2,sort_keys=True)+'\n';path=ROOT/'analysis/devinit_sources.json'
    if args.check:return 0 if path.is_file() and path.read_text()==text else 1
    path.write_text(text);return 0
if __name__=='__main__':raise SystemExit(main())
