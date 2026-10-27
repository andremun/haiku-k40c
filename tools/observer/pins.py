#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Generate source/binary/capture metadata. No trace or mapping authority is granted.

--check compares exact metadata text. --verify-external also hashes the cache.
The captured build/trace identity log is an archived input, not a live attestation.
"""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PINS=({'origin': 'https://archive.ubuntu.com/ubuntu/pool/main/s/strace/strace_5.16-0ubuntu3.dsc',
  'path': 'strace-ubuntu.dsc',
  'sha256': '2531ee5c4e44a909cf94a1f246cad50b05065212035d52712ceddd99b32f536f'},
 {'origin': 'https://archive.ubuntu.com/ubuntu/pool/main/s/strace/strace_5.16.orig.tar.xz',
  'path': 'strace_5.16.orig.tar.xz',
  'sha256': 'dc7db230ff3e57c249830ba94acab2b862da1fcaac55417e9b85041a833ca285'},
 {'origin': 'https://archive.ubuntu.com/ubuntu/pool/main/s/strace/strace_5.16-0ubuntu3.debian.tar.xz',
  'path': 'strace_5.16-0ubuntu3.debian.tar.xz',
  'sha256': '65a5620cb1edb29b1d07d88db347f6dadbc868b22fe2bd85751ed6e241b9d495'},
 {'origin': 'Exact reconstructed Ubuntu 5.16-0ubuntu3 source',
  'path': 'strace-ubuntu/src/ioctl.c',
  'sha256': 'ffc4fae7d375a3926093446958861f8598a717f674bb1471e092107e764cb322'},
 {'origin': 'Exact reconstructed Ubuntu 5.16-0ubuntu3 source',
  'path': 'strace-ubuntu/src/pathtrace.c',
  'sha256': '36b24c6fffc454d924ae75ef15e0663432ef3c9668cee2b0149062d8b5e5f68d'},
 {'origin': 'Installed /usr/include/linux/vfio.h; package version in observer-identity.log',
  'path': 'linux-vfio.h',
  'sha256': 'ed78e4a399fb3d864d5bc23e3345b645f92295f420fa06c5b073c10924c2c0ea'})
LOCAL=('tools/observer/build.py','tools/observer/vfio_decode.inc','tools/observer/normalize.py',
       'tests/test_observer.py','tests/observer_null.c','tools/observer/pins.py',
       'tools/dma_model.py','work/S1D0OBSERVER/null-trace.log',
       'work/S1D0OBSERVER/observer-identity.log')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--verify-external',action='store_true')
    parser.add_argument('--external-root',type=Path,default=Path('/tmp/k40-observer-sources'))
    args=parser.parse_args()
    if args.verify_external:
        for pin in PINS:
            if hashlib.sha256((args.external_root/pin['path']).read_bytes()).hexdigest()!=pin['sha256']:
                raise ValueError('external source differs: '+pin['path'])
    text=json.dumps(dict(scope='HOST_ONLY source/binary/capture metadata; no live DMA',
        source_pins=PINS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(LOCAL)},
        actual_fixture='owned /dev/null: all three ioctl calls returned ENOTTY',
        actual_successful_vfio_ioctl=False,physical_visibility_verified=False,production_eligible=False),indent=2,sort_keys=True)+'\n'
    output=ROOT/'work/S1D0OBSERVER/source-pins.json'
    if args.check:return 0 if output.is_file() and output.read_text()==text else 1
    output.write_text(text)
    print('Observer metadata generated; captured fixture has no successful VFIO ioctl')
    return 0

if __name__=='__main__':raise SystemExit(main())
