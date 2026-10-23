#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
import hashlib,json,subprocess
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
rom=Path(os.environ.get('K40_VBIOS',str(Path.home()/'mediaflux/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom'))).expanduser()
# The VBIOS image is private. GitHub CI sets K40_CI_NO_VBIOS=1 and has no image:
# report the test as not run there. Without the flag a missing image fails the test.
if os.environ.get('K40_CI_NO_VBIOS')=='1' and not rom.is_file():
    print('test_devinit_rom.py: NOT RUN (private VBIOS image not available in CI)')
    raise SystemExit(0)
report=json.loads((ROOT/'analysis/devinit_preflight.json').read_text())
assert hashlib.sha256(rom.read_bytes()).hexdigest()==report['rom_sha256']
roots=report['main_scripts']+([report['extra_script']] if int(report['extra_script'],16) else [])
args=[str(ROOT/'build/tests/devinit_rom_sim'),str(rom),report['condition_table'],report['macro_table'],str(report['ram_groups']),*roots]
subprocess.run(args,check=True)
