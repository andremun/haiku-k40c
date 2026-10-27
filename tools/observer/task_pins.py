#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Bind the current observer task-proof sources and inert captures. No authority.

Reads repository inputs and the built observer. Writes one deterministic record.
--check compares exact text without writing. Captures contain no VFIO success.
"""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/'work/S1D0THREAD/pins.json'
LOCAL=('tools/observer/task_pins.py','tools/observer/task_proof.inc',
       'tools/observer/task_stream.py','tools/observer/build.py','tools/observer/vfio_decode.inc',
       'tools/observer/supervise.py','tools/observer/binding.py','tests/observer_tasks.c',
       'tests/test_task_stream.py')


def render():
    names=sorted((*LOCAL,*(f'work/S1D0THREAD/owned-{mode}-02.log'
                   for mode in ('thread','fork','private','guard'))))
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    return json.dumps(dict(scope='owned /dev/null fixture; no successful VFIO ioctl',
        source_and_capture_sha256={name:digest(ROOT/name) for name in names},
        observer_sha256=digest(ROOT/'build/observer/strace-source/src/strace'),
        original_desc_sha256='340cbc008974197f6269a85765ccd02e588161107ee6ec00c4ca4d9b5522ba2b',
        api='Linux KCMP_FILES and proc TGID; exact original desc.c is in the pinned strace source package'),
        indent=2,sort_keys=True)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    expected=render()
    if args.check:return 0 if OUTPUT.is_file() and OUTPUT.read_text()==expected else 1
    OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_text(expected);return 0

if __name__=='__main__':raise SystemExit(main())
