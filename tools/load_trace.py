#!/usr/bin/env python3
# Copyright 2026 Mario Andrés Muñoz.
# Distributed under the terms of the MIT License.
"""Name source-backed anchors in the Linux load trace, without replaying it."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import rnndb
ROOT=Path(__file__).resolve().parent.parent
TRACE=ROOT/'reference/linux-run-debug/mmiotrace.txt.xz'
# Facts, not a write recipe. Each address is tied to an exact pinned source.
ANCHORS={
    0x100c10:('host_flush_page','reference/nouveau/nvkm/subdev/fb/gf100.c:81-84'),
    0x001700:('physical_instance_window','reference/nouveau/nvkm/subdev/instmem/nv50.c:57-92'),
    0x070000:('bar_visibility_flush','reference/nouveau/nvkm/subdev/bar/g84.c:29-40'),
    0x000204:('pbdma_discovery_mask','reference/nouveau/nvkm/engine/fifo/gf100.c:927'),
    0x002270:('runlist_address','reference/nouveau/nvkm/engine/fifo/gk104.c:430-447'),
    0x002274:('runlist_commit','reference/nouveau/nvkm/engine/fifo/gk104.c:430-447'),
    0x002634:('channel_preempt_NOT_runlist_commit','reference/nouveau/nvkm/engine/fifo/gf100.c:43-46'),
}

def summarize(lines):
    bars={};anchors={};domains={};runs=[];cache={};count=0;stop=None
    for number,line in enumerate(lines,1):
        count=number;parts=line.split()
        if not parts:continue
        if parts[0]=='MARK' and 'compute_test start' in line:
            stop=dict(line=number,time=parts[1]);break
        if parts[0]=='PCIDEV' and len(parts)>=18 and parts[2]=='10de1024':
            for i in range(7):
                base=int(parts[4+i],16)&~15;size=int(parts[11+i],16)
                if size:bars[i]=(base,size)
        if parts[0] not in ('R','W') or len(parts)<6:continue
        physical=int(parts[4],16)
        found=next(((bar,physical-base) for bar,(base,size) in bars.items() if base<=physical<base+size),None)
        if found is None:continue
        bar,offset=found
        name=None
        if bar==0 and 0x700000<=offset<0x800000:
            # Physical PRAMIN data window, not distinct MMIO registers.
            # reference/nouveau/nvkm/subdev/instmem/nv50.c:57-92
            name='PRAMIN_WINDOW.DATA'
        elif bar==0:
            if offset not in cache:
                result=rnndb.lookup(offset);cache[offset]=result['name'] if result else None
            name=cache[offset]
        domain=name.split('.')[0] if name else ('unknown_bar0' if bar==0 else f'BAR{bar}_memory')
        aggregate=domains.setdefault(domain,dict(reads=0,writes=0,first_line=number,last_line=number))
        aggregate['reads' if parts[0]=='R' else 'writes']+=1;aggregate['last_line']=number
        if not runs or runs[-1]['domain']!=domain:
            runs.append(dict(domain=domain,first_line=number,last_line=number,reads=0,writes=0))
        runs[-1]['last_line']=number;runs[-1]['reads' if parts[0]=='R' else 'writes']+=1
        if bar!=0 or offset not in ANCHORS:continue
        label,source=ANCHORS[offset]
        item=anchors.setdefault(label,dict(register=f'0x{offset:06x}',source=source,reads=0,writes=0,first_line=number,last_line=number,first_time=parts[2],last_time=parts[2],examples=[]))
        item['reads' if parts[0]=='R' else 'writes']+=1;item['last_line']=number;item['last_time']=parts[2]
        event=dict(line=number,time=parts[2],op=parts[0],value=parts[5])
        if len(item['examples'])<3:item['examples'].append(event)
    if not bars or stop is None:raise ValueError('missing card BAR description or job-start marker')
    return dict(scope='Linux load-phase evidence; not a minimal S1 sequence',bars={str(b):dict(base=hex(v[0]),bytes=v[1]) for b,v in bars.items()},job_start=stop,lines_scanned=count,anchors=sorted(anchors.values(),key=lambda item:item['first_line']),domains=dict(sorted(domains.items())),domain_runs=runs)

def render(r):
    lines=['# Linux load phase: named evidence','', 'This is a source-anchored survey, not an executable recipe or proof that GR can be omitted.','',f"Load ends before trace line {r['job_start']['line']} at time {r['job_start']['time']}.",'','| Register | First line | Last line | Reads | Writes | Source |','|---|---|---|---|---|---|']
    lines += [f"| {a['register']} | {a['first_line']} | {a['last_line']} | {a['reads']} | {a['writes']} | {a['source']} |" for a in r['anchors']]
    lines += ['','## Domain totals','','| Domain | Reads | Writes | First line | Last line |','|---|---|---|---|---|']
    lines += [f"| {name} | {a['reads']} | {a['writes']} | {a['first_line']} | {a['last_line']} |" for name,a in r['domains'].items()]
    lines += ['','Detailed chronological domain runs and first anchor samples are in load_trace.json. BAR1/BAR3 writes are memory accesses, not independently identified objects. Unknown register names remain unknown.','', '0x002634 is channel preemption; runlist publication uses 0x002270/0x002274. Capture addresses are examples, never allocation addresses for Haiku.','']
    return '\n'.join(lines)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    with lzma.open(TRACE,'rt') as stream:r=summarize(stream)
    r['trace_sha256']=hashlib.sha256(TRACE.read_bytes()).hexdigest()
    outputs={ROOT/'analysis/load_trace.json':json.dumps(r,indent=2,sort_keys=True)+'\n',ROOT/'analysis/load_trace.md':render(r)}
    if args.check:return 0 if all(path.is_file() and path.read_text()==text for path,text in outputs.items()) else 1
    for path,text in outputs.items():path.write_text(text)
    print('load trace: named anchors',len(r['anchors']),'domain runs',len(r['domain_runs']))
    return 0
if __name__=='__main__':raise SystemExit(main())
