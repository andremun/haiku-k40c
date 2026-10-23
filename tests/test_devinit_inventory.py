#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('inventory', Path(__file__).resolve().parents[1] / 'tools/devinit_inventory.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
log = ('[ 1.0] nouveau: devinit: 0x00000100[0]: TIME\t0x10\n'
       '[ 1.1] nouveau: devinit: 0x00000102[0]: \tdetail\n'
       '[ 1.2] i2c: bus\n\n'
       '[ 1.3] nouveau: devinit: 0x00000103[ ]: GPIO\n'
       '[ 1.4] nouveau: devinit: 0x00000104[2]: DONE\n')
rows = m.parse_log(log)
assert len(rows) == 3 and rows[0]['details'] == ['nouveau: devinit: 0x00000102[0]: \tdetail', 'i2c: bus']
assert m.log_summary(rows)['executed'] == 2 and m.log_summary(rows)['skipped'] == 1
listing = ('0x00000000: 71    DONE\nInit script table at 0x20: 1 main scripts\n'
           'Init script 0 at 0x100:\n0x00000100: 74 10 00          TIME 0x0010\n'
           '0x00000103: 11 22 33          R[0x000000] = 0\n'
           '0x00000106: 5f 00 00\n0x00000116: 01 00          COPY_NV_REG R[x]\n'
           '0x00000118: 71             DONE\n0x00000118: 71             DONE\n'
           '0x00000119: 01 00 00 00    0x00000001\n')
scripts, instructions = m.parse_listing(listing)
assert scripts == [dict(index=0, offset='0x100')]
assert len(instructions) == 5 and instructions[1]['offset'] == '0x00000116'
assert all(i['offset'] != '0x00000103' for i in instructions)
r = m.inventory(listing, log)
assert r['static_instructions'] == 5 and r['log_offsets_not_in_listing'] == ['0x00000103', '0x00000104']
assert [i['name'] for i in r['board_operations']] == ['TIME', 'GPIO']
assert m.markdown(r) == m.markdown(r)
print('devinit inventory parser: all checks passed')

assert not m.LISTING.match("0x0000745c:" + " 50" * 29 + " mask = 0x1f")
