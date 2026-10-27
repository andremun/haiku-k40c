#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Bind the fixed D0 artifact suite and current source hashes. --check writes nothing."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/haiku'))
import probe_stage
STAGE='D0_MAPPING_OBSERVE_ONLY'
FILES={
 'identity':'build/haiku/k40_identity_probe',
 'owner':'build/haiku/k40_owner_post_module',
 'memory':'build/haiku/k40_d0_memory_probe',
 'observer':'build/observer/strace-source/src/strace',
 'qemu':'/usr/bin/qemu-system-x86_64',
}
SOURCES=(
 'tools/haiku/d0_stage.py','tools/haiku/d0_run.py','tools/haiku/d0_monitor.py',
 'tools/haiku/d0_topology.py','tools/haiku/d0_kernel_log.py','tools/haiku/d0_evidence.py',
 'tools/haiku/selftest/map_owner.cpp','tools/haiku/card_run.py','tools/haiku/vm_guard.py',
 'tools/haiku/qemu_hmp.py','tools/observer/supervise.py','tools/observer/binding.py',
 'tools/observer/normalize.py','tools/observer/vfio_decode.inc','tools/observer/build.py','tools/dma_model.py',
 'src/os/OwnerClient.cpp','src/os/OwnerClient.h','src/os/HaikuOwnerModule.cpp','src/os/HaikuOwnerModule.h',
 'src/os/NativeOwner.cpp','src/os/NativeOwner.h','src/os/HaikuMemory.cpp','src/os/HaikuMemory.h',
 'src/os/HaikuBackend.c','src/os/HaikuBackend.h','src/devinit/PostImage.cpp','src/devinit/PostImage.h',
 'src/devinit/BoardPolicy.cpp','src/devinit/BoardPolicy.h','src/devinit/Sha256.cpp','src/devinit/Sha256.h','src/runtime/BootState.h',
 'src/devinit/BoundPost.cpp','src/devinit/BoundPost.h','src/devinit/BoardCore.cpp','src/devinit/BoardCore.h',
 'src/devinit/Interpreter.cpp','src/devinit/Interpreter.h','src/devinit/I2c.cpp','src/devinit/I2c.h','src/memory/Memory.h',
)
OUTPUT=ROOT/'work/S1D0PACKAGE/stage.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def elf(path,tag):
 data=path.read_bytes()
 if not 4096<=len(data)<=32*1024*1024 or data[:6]!=b'\x7fELF\x02\x01' or data[18:20]!=b'\x3e\x00' or tag not in data:
  raise ValueError('wrong artifact role: '+str(path))
 return data


def manifest():
 paths={name:(ROOT/path if not Path(path).is_absolute() else Path(path)).resolve(strict=True) for name,path in FILES.items()}
 identity=probe_stage.validate(paths['identity'])
 elf(paths['memory'],b'D0_MEMORY_NO_DEVICE');elf(paths['owner'],b'generic/k40c_owner/v1')
 imports={line.split()[-1].split('@')[0] for line in subprocess.check_output(['nm','-u',str(paths['memory'])],text=True).splitlines() if line.split()}
 if not imports<= {'dprintf','get_module','put_module','memcmp','strcmp','memset'}:raise ValueError('unexpected D0 memory probe capability')
 symbols=subprocess.check_output(['nm','-D','--defined-only',str(paths['owner'])],text=True)
 if not any(line.split()[-1]=='modules' for line in symbols.splitlines()) or 'simulatePost' in symbols:
  raise ValueError('wrong permanent owner interface')
 return dict(stage=STAGE,kernel_sha256=identity['kernel_sha256'],identity=identity,
  artifacts={name:dict(path=str(path),sha256=sha(path)) for name,path in sorted(paths.items())},
  sources={name:sha(ROOT/name) for name in sorted(SOURCES)},
  probe_gpu_writes=False,device_iova_publication=False,claim='mapping observation only; no payload/coherency proof')


def text():return json.dumps(manifest(),indent=2,sort_keys=True)+'\n'


def validate():
 expected=text()
 if not OUTPUT.is_file() or OUTPUT.read_text()!=expected:raise ValueError('D0 suite/source record differs; rebuild and review')
 return json.loads(expected)


def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
 if args.check:validate()
 else:OUTPUT.write_text(text())
 return 0

if __name__=='__main__':raise SystemExit(main())
