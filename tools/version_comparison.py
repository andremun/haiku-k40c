#!/usr/bin/env python3
# Copyright 2026 Mario Andrés Muñoz.
# Distributed under the terms of the MIT License.
"""Hash selected upstream v6.8 files against pinned v6.12. --check is offline.

Use --fetch explicitly to populate the ignored cache. This does not establish
identity with Ubuntu's downstream kernel source package used in the capture.
"""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parent.parent
PATHS=['nvkm/subdev/bios/init.c','nvkm/subdev/bios/bit.c','nvkm/subdev/bios/ramcfg.c','nvkm/subdev/devinit/gf100.c','nvkm/engine/device/base.c','nvkm/subdev/fb/base.c','nvkm/subdev/fb/gf100.c','nvkm/subdev/instmem/nv50.c','nvkm/subdev/bar/g84.c','nvkm/subdev/bar/gf100.c','nvkm/subdev/mmu/vmmgf100.c','nvkm/subdev/mmu/vmmgk104.c','nvkm/subdev/mmu/gf100.c','nvkm/subdev/mmu/gk104.c','nvkm/engine/fifo/gk104.c','nvkm/engine/fifo/gk110.c','nvkm/engine/fifo/gf100.c','nvkm/engine/fifo/chan.c','nvkm/engine/fifo/runl.c','nvif/user.c','nouveau_dma.c']
CACHE=ROOT/'build/linux-v6.8-selected'
def url(path):return 'https://raw.githubusercontent.com/torvalds/linux/v6.8/drivers/gpu/drm/nouveau/'+path

def fetch(path):
    with urllib.request.urlopen(url(path),timeout=20) as response:data=response.read(1024*1024+1)
    if len(data)>1024*1024:raise ValueError('source exceeds safety size limit')
    destination=CACHE/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--fetch',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.fetch and args.check:parser.error('--check must not use network or write')
    if args.fetch:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(fetch,PATHS))
    rows=[]
    for path in PATHS:
        old=(CACHE/path).read_bytes() if (CACHE/path).is_file() else None
        new=(ROOT/'reference/nouveau'/path).read_bytes()
        rows.append(dict(path=path,url=url(path),v68_sha256=hashlib.sha256(old).hexdigest() if old is not None else None,v612_sha256=hashlib.sha256(new).hexdigest(),identical=(old==new) if old is not None else None,status='available' if old is not None else 'missing_cached_v6.8_source'))
    complete=all(row['identical'] is not None for row in rows)
    report=dict(scope='upstream v6.8 tag file hashes vs pinned v6.12; Ubuntu downstream patches not covered',comparison_complete=complete,files=rows)
    text=json.dumps(report,indent=2,sort_keys=True)+'\n';output=ROOT/'analysis/s1-version-comparison.json'
    if args.check:
        if not output.is_file() or output.read_text()!=text:return 1
        return 0 if complete else 2
    output.write_text(text);print('Version comparison:', 'complete' if complete else 'INCOMPLETE: v6.8 cache unavailable', '; byte-identical files:',sum(r['identical'] is True for r in rows))
    return 0 if complete else 2
if __name__=='__main__':raise SystemExit(main())
