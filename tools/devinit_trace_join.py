#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Time-correlate devinit log intervals with device BAR accesses, not causation."""
import argparse
import bisect
from decimal import Decimal
import hashlib
import json
import lzma
from pathlib import Path
import re
import devinit_inventory
ROOT=Path(__file__).resolve().parent.parent
LOG=ROOT/'reference/linux-run-debug/dmesg.txt.xz';TRACE=ROOT/'reference/linux-run-debug/mmiotrace.txt.xz'
def ns(value):return int(Decimal(value)*1000000000)
def join(log_text,trace_lines):
    loglines=log_text.splitlines();instructions=devinit_inventory.parse_log(log_text)
    times=[ns(re.match(r'^\[\s*([0-9.]+)\]',loglines[i['line']-1])[1]) for i in instructions]
    if times!=sorted(times):raise ValueError('log timestamps not monotonic')
    rows=[dict(line=i['line'],offset=i['offset'],name=i['name'],marker=i['marker'],reads=0,writes=0,first_trace_line=None,last_trace_line=None) for i in instructions]
    bars={}
    for number,line in enumerate(trace_lines,1):
        parts=line.split()
        if not parts:continue
        if parts[0]=='MARK' and 'compute_test start' in line:break
        if parts[0]=='PCIDEV' and len(parts)>=18 and parts[2]=='10de1024':
            bars={i:(int(parts[4+i],16)&~15,int(parts[11+i],16)) for i in range(7) if int(parts[11+i],16)}
        if parts[0] not in ('R','W') or len(parts)<6:continue
        timestamp=ns(parts[2]);physical=int(parts[4],16)
        if timestamp<times[0] or timestamp>=times[-1]:continue
        if not any(base<=physical<base+size for base,size in bars.values()):continue
        index=bisect.bisect_right(times,timestamp)-1;row=rows[index]
        row['reads' if parts[0]=='R' else 'writes']+=1
        if row['first_trace_line'] is None:row['first_trace_line']=number
        row['last_trace_line']=number
    if not bars:raise ValueError('no card BAR metadata')
    return dict(scope='timestamp intervals only; same-time messages, asynchronous accesses and non-MMIO helpers prevent causal attribution',duplicate_log_timestamps=len(times)-len(set(times)),intervals=rows,skipped_intervals_with_accesses=[r['line'] for r in rows if r['marker']==' ' and r['reads']+r['writes']],coverage_claim='No register-value or helper-completeness equivalence is claimed')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    with lzma.open(TRACE,'rt') as stream:report=join(lzma.open(LOG,'rt').read(),stream)
    report['inputs_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (LOG,TRACE)}
    text=json.dumps(report,indent=2,sort_keys=True)+'\n';path=ROOT/'analysis/devinit_trace_join.json'
    if args.check:return 0 if path.is_file() and path.read_text()==text else 1
    path.write_text(text);print('devinit/trace correlation:',len(report['intervals']),'intervals;',len(report['skipped_intervals_with_accesses']),'skipped intervals with accesses (not causal proof)');return 0
if __name__=='__main__':raise SystemExit(main())
