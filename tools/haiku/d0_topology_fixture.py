#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Capture source-format topology in a disposable cardless Q35 guest. No host device.

--check validates fixture prerequisites without starting a guest or writing files.
This is a new fixture launcher; existing B5/cardless commands are unchanged.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.haiku.vm_guard import guest_lock
from tools.haiku.d0_monitor import snapshot
from tools.observer.supervise import observed_child

BASE=Path.home()/'haiku-vm/system.qcow2'
OBSERVER=ROOT/'build/observer/strace-source/src/strace'
QEMU=Path('/usr/bin/qemu-system-x86_64')


def arguments(folder,evidence):
    args=[str(QEMU),'-name','k40-d0-cardless-topology','-machine','q35','-accel','kvm','-cpu','host','-smp','2','-m','4096',
        '-drive','if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd',
        '-drive','if=pflash,format=raw,file='+str(folder/'vars.fd'),
        '-drive','file='+str(folder/'overlay.qcow2')+',format=qcow2,if=none,id=system',
        '-device','ide-hd,drive=system,bus=ide.0,bootindex=1','-device','qemu-xhci','-device','usb-tablet','-vga','std',
        '-netdev','user,id=n0','-device','e1000,netdev=n0','-display','none',
        '-serial','file:'+str(evidence/'serial.log'),'-qmp','unix:'+str(folder/'qmp')+',server,nowait']
    if any('vfio' in arg.lower() for arg in args):raise ValueError('fixture must be cardless')
    return args


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true');options=parser.parse_args()
    if os.geteuid()==0:raise ValueError('root execution forbidden')
    for path in (BASE,OBSERVER,QEMU):path.resolve(strict=True)
    if not os.access('/dev/kvm',os.R_OK|os.W_OK):raise ValueError('KVM access unavailable')
    if options.check:
        print('CARDLESS topology fixture prerequisites available; no guest started');return 0
    with guest_lock(BASE.parent):
        evidence=ROOT/'results'/(datetime.now().strftime('%Y%m%d')+'-d0-topology-fixture')
        evidence.mkdir(mode=0o700,exist_ok=False)
        folder=ROOT/'build/d0'/uuid.uuid4().hex[:8];folder.mkdir(parents=True,mode=0o700,exist_ok=False)
        if len(os.fsencode(folder/'qmp'))>107:raise ValueError('monitor socket path too long')
        shutil.copyfile(BASE.parent/'vars.fd',folder/'vars.fd')
        subprocess.run(['qemu-img','create','-q','-f','qcow2','-F','qcow2','-b',str(BASE),str(folder/'overlay.qcow2')],check=True)
        args=arguments(folder,evidence)
        record=dict(scope='CARDLESS_TOPOLOGY_ONLY',args=args,base=str(BASE),timeout_seconds=60,
            binaries_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (OBSERVER,QEMU)},
            source_commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip())
        (evidence/'launch.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
        status='failed';error='';start=time.monotonic()
        try:
            with (evidence/'qemu.log').open('xb') as log,observed_child(OBSERVER,args,evidence/'trace.log',log,60,evidence/'watchdog.txt',['/dev/null']) as child:
                end=time.monotonic()+15
                while not (folder/'qmp').exists():
                    child.check()
                    if time.monotonic()>end:raise RuntimeError('QMP readiness deadline')
                    time.sleep(0.05)
                child.check();topology=snapshot(folder/'qmp')
                for name,text in topology.items():(evidence/(name+'.txt')).write_text(text)
                status='pass'
        except BaseException as exc:error=str(exc);raise
        finally:
            (evidence/'result.json').write_text(json.dumps(dict(status=status,error=error,
                elapsed_seconds=round(time.monotonic()-start,2),scope='CARDLESS_ONLY',claim='topology format only'),indent=2)+'\n')
            print(evidence,flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
