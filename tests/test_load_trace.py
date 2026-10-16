#!/usr/bin/env python3
# Copyright 2026 Mario Andrés Muñoz.
# Distributed under the terms of the MIT License.
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from load_trace import summarize
lines=['PCIDEV 0018 10de1024 b d1000000 90000000c 0 91000000c 0 0 0 1000000 10000000 0 2000000 0 0 0\n',
       'W 4 1.0 1 0xd1100c10 0x123 0x0 0\n',
       'W 4 1.1 2 0x910000004 0xabc 0x0 0\n',
       'W 4 1.2 1 0xd1002634 0x2 0x0 0\n',
       'MARK 2.0 compute_test start\n',
       'W 4 2.1 1 0xd1002274 0x1 0x0 0\n']
r=summarize(lines)
assert r['bars']['0']['base']=='0xd1000000' and r['job_start']['line']==5
assert len(r['anchors'])==2 and r['anchors'][0]['register']=='0x100c10'
assert r['anchors'][1]['source'].endswith('gf100.c:43-46')
assert r['domains']['BAR3_memory']['writes']==1
try:summarize(lines[:3])
except ValueError:pass
else:raise AssertionError('missing end marker accepted')
print('load trace: shifted-BAR/phase/anchor tests pass')
