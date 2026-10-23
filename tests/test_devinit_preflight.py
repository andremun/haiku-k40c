#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from devinit_preflight import preflight
rom=bytearray(1024)
rom[32:37]=b'\xff\xb8BIT';rom[41]=6;rom[42]=2
rom[44:50]=bytes([ord('I'),1,18,0,80,0]);rom[50:56]=bytes([ord('M'),2,3,0,112,0])
rom[80:82]=(144).to_bytes(2,'little');rom[112]=2;rom[144:146]=(256).to_bytes(2,'little')
rom[256:263]=bytes([0x75,0,0x5b,0x10,1,0x71,0])
rom[272:274]=bytes([0x8c,0x71])
r,visited=preflight(rom)
assert r['structural_coverage_complete'] and {256,258,261,272,273}==set(visited)
rom[272]=0xfe
r,_=preflight(rom)
assert not r['structural_coverage_complete'] and r['issues'][0]['opcode']=='0xfe'
rom[32]=0
try:preflight(rom)
except ValueError:pass
else:raise AssertionError('missing BIT accepted')
print('raw ROM preflight: roots, conditional calls, unknown opcode and bounds checks pass')
