#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Build the userspace observer, never install it. --check compares patched source text.

Requires the exact reconstructed strace 5.16-0ubuntu3 source tree. Source archives
and hashes are recorded by the observer task. No network, guest or device access.
"""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BASELINE='ffc4fae7d375a3926093446958861f8598a717f674bb1471e092107e764cb322'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('/tmp/k40-observer-sources/strace-ubuntu'))
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    original=(args.source/'src/ioctl.c').read_text()
    if hashlib.sha256(original.encode()).hexdigest()!=BASELINE:
        raise ValueError('strace source is not the recorded baseline')
    expected=original.replace('#include "defs.h"','#include "defs.h"\n#include "k40_vfio.inc"',1)
    needle='const kernel_ulong_t arg = tcp->u_arg[2];\n\n\tswitch (_IOC_TYPE(code)) {'
    expected=expected.replace(needle,needle+'\n\tcase VFIO_TYPE:\n\t\treturn k40_vfio_decode(tcp, code, arg);',1)
    include=(ROOT/'tools/observer/vfio_decode.inc').read_text()
    path_original=(args.source/'src/pathtrace.c').read_text()
    if hashlib.sha256(path_original.encode()).hexdigest()!='36b24c6fffc454d924ae75ef15e0663432ef3c9668cee2b0149062d8b5e5f68d':
        raise ValueError('path-filter source is not the recorded baseline')
    path_expected=path_original.replace('switch (s->sen) {','switch (s->sen) {\n\tcase SEN_close:\n\t\treturn true; /* K40: observe all descriptor lifetimes. */',1)
    target=ROOT/'build/observer/strace-source'
    if args.check:
        return 0 if ((target/'src/ioctl.c').is_file() and (target/'src/ioctl.c').read_text()==expected
            and (target/'src/k40_vfio.inc').is_file() and (target/'src/k40_vfio.inc').read_text()==include
            and (target/'src/pathtrace.c').read_text()==path_expected) else 1
    if not target.exists():
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(args.source,target,symlinks=True)
    elif (target/'src/ioctl.c').read_text() not in (original,expected):
        raise ValueError('existing observer source differs; preserve and investigate')
    if (target/'src/pathtrace.c').read_text() not in (path_original,path_expected):
        raise ValueError('existing path-filter source differs; preserve and investigate')
    (target/'src/pathtrace.c').write_text(path_expected)
    (target/'src/ioctl.c').write_text(expected)
    (target/'src/k40_vfio.inc').write_text(include)
    if not (target/'Makefile').exists():
        subprocess.run(['./configure','--enable-mpers=no','--without-libunwind','--without-libiberty'],cwd=target,check=True)
    subprocess.run(['make','-j2'],cwd=target,check=True)
    print('Observer binary:',target/'src/strace')
    return 0


if __name__=='__main__':raise SystemExit(main())
