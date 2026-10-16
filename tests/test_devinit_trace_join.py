#!/usr/bin/env python3
# Copyright 2026 Mario Andrés Muñoz.
# Distributed under the terms of the MIT License.
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from devinit_trace_join import join
log='[ 1.0] n: devinit: 0x00000100[0]: NV_REG\n[ 1.1] n: devinit: 0x0000010d[ ]: TIME\n[ 1.2] n: devinit: 0x00000110[0]: DONE\n'
trace=['PCIDEV 0018 10de1024 b d1000000 0 0 0 0 0 0 1000000 0 0 0 0 0 0\n','W 4 1.05 1 0xd1000000 0x1 0x0 0\n','R 4 1.15 1 0xd1000000 0x1 0x0 0\n','R 4 1.16 2 0x1000 0x0 0x0 0\n']
r=join(log,trace)
assert r['intervals'][0]['writes']==1 and r['intervals'][1]['reads']==1
assert r['skipped_intervals_with_accesses']==[2]
print('devinit timestamp join: interval/BAR/ambiguity tests pass')
