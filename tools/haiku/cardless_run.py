#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Bounded, snapshot-only Haiku kernel/probe runner. No host devices/options.

Boots an overlay of the existing cardless application guest. It never modifies
that base disk or accepts additional QEMU arguments. Serial and HTTP results
are saved incrementally in ignored build/cardless/RUN/. Requires no sudo/KVM.
"""
from contextlib import ExitStack
import argparse
import hashlib
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time

ROOT=Path(__file__).resolve().parents[2]
HMP=Path(__file__).with_name('qemu_hmp.py')
DEFAULT_BASE=Path(os.environ.get('HAIKU_PERSISTENT_VM_DIR',Path.home()/'haiku-vm')).expanduser()/'system.qcow2'


def probe_complete(serial):
    """Reject any failed load, including failure followed by a devfs reload PASS."""
    if 'k40_os: FAIL' in serial or 'cleanup failed' in serial:
        raise RuntimeError('cardless probe failed; stop without retry')
    if 'K40-CARDLESS-END' not in serial:
        return False
    if 'k40_os: PASS' not in serial:
        raise RuntimeError('guest commands completed without driver PASS')
    return True


def owner_complete(serial):
    """Require ordered native init/uninit evidence and unchanged owner state."""
    if not probe_complete(serial):
        return False
    if 'k40_owner_test: host-bytes-cleanup PASS; publication DENIED' not in serial:
        raise RuntimeError('owner probe lacks host-byte/cleanup evidence')
    events = list(re.finditer(r'k40_owner_test: phase([12]) (init|uninit) lease=(\d+) token=(\d+)([^\n]*)', serial))
    if len(events) != len(re.findall(r'k40_owner_test: phase',serial)):
        raise RuntimeError('owner probe has malformed lifetime evidence')
    if len(events) < 4:
        raise RuntimeError('owner probe lacks client reload evidence')
    expected = [(1, 'init'), (1, 'uninit')]
    for i in range(2, len(events)):
        expected.append((2, 'init' if i % 2 == 0 else 'uninit'))
    first_lease, token = int(events[0][3]), int(events[0][4])
    if not first_lease or not token or len(events) % 2:
        raise RuntimeError('owner probe has incomplete/invalid client lifetime')
    lease = 0
    previous = 0
    for event, (phase, kind) in zip(events, expected):
        if int(event[1]) != phase or event[2] != kind or int(event[4]) != token:
            raise RuntimeError('owner reload order or retained token differs')
        if kind == 'init':
            lease = int(event[3])
            if lease <= previous:
                raise RuntimeError('owner client lease did not advance')
            previous = lease
            if phase == 2 and event[5].strip() != 'state=3 owned=1 quarantine=1':
                raise RuntimeError('owner reload lost failed/quarantined state')
        elif int(event[3]) != lease or event[5].strip() != 'retained':
            raise RuntimeError('owner detach evidence differs')
    if 'k40_os: PASS native owner reload only; DMA denied' not in serial[events[-1].end():]:
        raise RuntimeError('owner reload lacks final PASS after uninit')
    return True


def validate_owner_pair(driver, module):
    """Refuse swapped/non-ELF owner artifacts before any guest starts."""
    if driver is None:
        raise ValueError('owner mode requires the client driver')
    if not module.is_file():
        raise ValueError('missing owner module binary')
    client, owner = driver.read_bytes(), module.read_bytes()
    if client[:4] != b'\x7fELF' or b'CARDLESS_OWNER_ONLY' not in client:
        raise ValueError('owner mode requires the owner client probe')
    if owner[:4] != b'\x7fELF' or b'generic/k40c_owner/v1' not in owner:
        raise ValueError('not an owner module ELF')
    symbols = subprocess.check_output(['readelf','--wide','--dyn-syms',str(module)], text=True, timeout=5)
    if not re.search(r'\bOBJECT\s+GLOBAL\s+DEFAULT\s+\d+\s+modules\s*$', symbols, re.MULTILINE):
        raise ValueError('owner ELF does not export the module table')


def guest_commands(port, driver, owner=False):
    """Stage only fixed test destinations; owner mode uses user add-on lookup."""
    commands=['#!/bin/sh','set -eu',f'host=http://10.0.2.2:{port}',
              'uname -a > /tmp/k40-environment.txt','curl -fsS -T /tmp/k40-environment.txt "$host/environment.txt"',
              'curl -fsS -T /boot/system/kernel_x86_64 "$host/kernel_x86_64"']
    if owner:
        commands += ["trap 'status=$?; echo \"$status\" > /tmp/k40-job.exit; curl -fsS -T /tmp/k40-job.exit \"$host/job.exit\"' EXIT"]
        commands += ['addons=$(finddir B_USER_NONPACKAGED_ADDONS_DIRECTORY)',
                     'mkdir -p "$addons/kernel/generic"',
                     'curl -fsS -o "$addons/kernel/generic/k40c_owner" "$host/owner_module"',
                     'chmod +x "$addons/kernel/generic/k40c_owner"',
                     'base="$addons/kernel/drivers"']
    elif driver:
        commands += ['base=/boot/system/non-packaged/add-ons/kernel/drivers']
    if driver:
        commands += ['mkdir -p "$base/bin" "$base/dev/misc"',
                     'curl -fsS -o "$base/bin/k40_cardless_probe" "$host/probe"',
                     'chmod +x "$base/bin/k40_cardless_probe"',
                     'ln -sf ../../bin/k40_cardless_probe "$base/dev/misc/k40_cardless_probe"',
                     'echo K40-CARDLESS-BEGIN > /dev/dprintf']
        if owner:
            # Empty-node drivers unload after publish_devices; each listing can reload.
            commands += ['ls /dev/misc >/dev/null','sleep 1'] * 4
        else:
            commands += ['ls /dev/misc >/dev/null','sleep 3']
        commands += ['echo K40-CARDLESS-END > /dev/dprintf']
    if not owner:
        commands += ['echo 0 > /tmp/k40-job.exit','curl -fsS -T /tmp/k40-job.exit "$host/job.exit"']
    return '\n'.join(commands)+'\n'


def run(base,driver,seconds,cpus=1,kvm=False,owner_module=None,logging_observer=False):
    from vm_guard import guest_lock

    with guest_lock(base.parent):
        return _run(base,driver,seconds,cpus,kvm,owner_module,logging_observer)


def _run(base,driver,seconds,cpus=1,kvm=False,owner_module=None,logging_observer=False):
    if not 30<=seconds<=600:raise ValueError('timeout must be 30..600 seconds')
    if cpus not in (1,2):raise ValueError('cardless CPU count must be one or two')
    if kvm and not os.access('/dev/kvm',os.R_OK|os.W_OK):raise ValueError('KVM unavailable to this user; no sudo attempted')
    if not base.is_file():raise ValueError('missing cardless base disk')
    if driver is not None and not driver.is_file():raise ValueError('missing driver binary')
    if owner_module is None and driver is not None and b'CARDLESS_OWNER_ONLY' in driver.read_bytes():
        raise ValueError('owner client requires --owner-module and strict reload validation')
    if logging_observer and (owner_module is not None or driver is None
        or b'CARDLESS_A7_LOGGING_ONLY' not in driver.read_bytes()):
        raise ValueError('logging observer requires the fixed inert logging probe')
    expected_kernel = None
    if logging_observer or (driver is not None and b'CARDLESS_A7_LOGGING_ONLY' in driver.read_bytes()):
        kernel=Path(os.environ.get('HAIKU_CROSS',Path.home()/'haiku-cross'))/'lib/kernel_x86_64'
        expected_kernel=hashlib.sha256(kernel.read_bytes()).hexdigest()
    if owner_module is not None:
        validate_owner_pair(driver,owner_module)
        kernel=Path(os.environ.get('HAIKU_CROSS',Path.home()/'haiku-cross'))/'lib/kernel_x86_64'
        expected_kernel=hashlib.sha256(kernel.read_bytes()).hexdigest()
    folder=ROOT/'build/cardless'/time.strftime('%Y%m%d-%H%M%S')
    folder.mkdir(parents=True,exist_ok=False)
    # The monitor socket stays in the run folder, not in /tmp (sun_path: 107 bytes at most).
    monitor=folder/'monitor.sock'
    if len(os.fsencode(monitor))>107:raise ValueError('run folder path is too long for a monitor socket')
    peer_vars=base.parent/'vars.fd'
    shutil.copyfile(peer_vars if peer_vars.is_file() else '/usr/share/OVMF/OVMF_VARS_4M.fd',folder/'vars.fd')
    subprocess.run(['qemu-img','create','-q','-f','qcow2','-F','qcow2','-b',str(base.resolve()),str(folder/'overlay.qcow2')],check=True)
    if driver is not None:shutil.copyfile(driver,folder/'probe')
    if owner_module is not None:shutil.copyfile(owner_module,folder/'owner_module')
    received=set()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            name=self.path.lstrip('/')
            if name not in ('job.sh','probe','owner_module') or not (folder/name).is_file():self.send_error(404);return
            data=(folder/name).read_bytes();self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        def do_PUT(self):
            name=self.path.lstrip('/')
            if name not in ('kernel_x86_64','environment.txt','job.exit'):self.send_error(400);return
            try:size=int(self.headers.get('Content-Length','-1'))
            except ValueError:self.send_error(400);return
            if not 0<=size<=64*1024*1024:self.send_error(413);return
            self.connection.settimeout(30)
            data=self.rfile.read(size)
            if len(data)!=size:self.send_error(400);return
            temporary=folder/(name+'.partial');temporary.write_bytes(data);temporary.replace(folder/name)
            received.add(name);self.send_response(201);self.end_headers()
        def log_message(self,fmt,*args):
            with (folder/'http.log').open('a') as log:log.write(fmt%args+'\n')
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    server.daemon_threads=True
    port=server.server_address[1]
    (folder/'job.sh').write_text(guest_commands(port,driver is not None,owner_module is not None))
    args=['qemu-system-x86_64','-name','k40-cardless-verification','-machine','q35','-accel','kvm' if kvm else 'tcg,thread=multi','-cpu','host' if kvm else 'qemu64','-smp',str(cpus),'-m','4096',
          '-drive','if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd',
          '-drive','if=pflash,format=raw,file='+str(folder/'vars.fd'),
          '-drive','file='+str(folder/'overlay.qcow2')+',format=qcow2,if=none,id=system',
          '-device','ide-hd,drive=system,bus=ide.0,bootindex=1','-device','qemu-xhci','-device','usb-tablet','-vga','std',
          '-netdev','user,id=n0','-device','e1000,netdev=n0','-display','none',
          '-serial','file:'+str(folder/'serial.log'),'-monitor','unix:'+str(monitor)+',server,nowait']
    artifacts={name:hashlib.sha256((folder/name).read_bytes()).hexdigest()
               for name in ('probe','owner_module') if (folder/name).is_file()}
    commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()
    (folder/'launch.json').write_text(json.dumps(dict(args=args,base=str(base),timeout_seconds=seconds,
        scope='CARDLESS_KVM' if kvm else 'CARDLESS_TCG',artifacts_sha256=artifacts,
        kernel_sha256=expected_kernel,source_commit=commit,owner_reload=owner_module is not None,logging_observer=logging_observer),indent=2)+'\n')
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    process=None;watchdog=None;start=time.monotonic();status='failed'
    def hmp(mode,text):
        subprocess.run(['python3',str(HMP),str(monitor),mode,text],check=True,timeout=30,stdout=subprocess.DEVNULL)
    try:
        with ExitStack() as stack:
            log=stack.enter_context((folder/'qemu.log').open('wb'))
            child=None
            if logging_observer:
                import sys
                sys.path.insert(0,str(ROOT))
                from tools.observer.supervise import observed_child
                child=stack.enter_context(observed_child(
                    ROOT/'build/observer/strace-source/src/strace',[str(Path(shutil.which(args[0])).resolve()),*args[1:]],
                    folder/'observer.trace',log,seconds,folder/'observer-watchdog.json',
                    ['/dev/vfio/vfio','/dev/vfio/23']))
                process=child.process
            else:process=subprocess.Popen(args,stdout=log,stderr=log)
            def timeout():
                if process.poll() is None:process.kill()
            watchdog=threading.Timer(seconds,timeout);watchdog.daemon=True;watchdog.start()
            launched=False
            while time.monotonic()-start<seconds and process.poll() is None:
                if child:child.check()
                serial=(folder/'serial.log').read_text(errors='replace') if (folder/'serial.log').is_file() else ''
                if 'PANIC:' in serial:raise RuntimeError('kernel panic; see incremental serial log')
                if driver is not None:probe_complete(serial)
                if not launched and ('first login script' in serial or 'Volume::InitialVerify(): volume at "/boot/home/config" is consistent' in serial):
                    # Wait for Tracker before sending its terminal shortcut.
                    time.sleep(12);hmp('cmd','sendkey alt-meta_l-t');time.sleep(8)
                    hmp('type',f'curl -fsS http://10.0.2.2:{port}/job.sh -o /tmp/k40-job.sh; sh /tmp/k40-job.sh')
                    launched=True
                if 'job.exit' in received:
                    if (folder/'job.exit').read_text().strip()!='0':raise RuntimeError('guest job failed')
                    if driver is not None:
                        complete=owner_complete(serial) if owner_module is not None else probe_complete(serial)
                        if not complete:time.sleep(1);continue
                    if expected_kernel and ('kernel_x86_64' not in received or hashlib.sha256((folder/'kernel_x86_64').read_bytes()).hexdigest()!=expected_kernel):
                        raise RuntimeError('guest kernel differs from owner link kernel')
                    status='pass';break
                time.sleep(1)
            if status!='pass':raise RuntimeError('guest ended or host deadline expired; see saved logs')
    finally:
        if watchdog:watchdog.cancel()
        if process and process.poll() is None:
            process.terminate()
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:process.kill();process.wait(timeout=5)
        server.shutdown();server.server_close();thread.join(timeout=5)
        monitor.unlink(missing_ok=True)
        (folder/'result.json').write_text(json.dumps(dict(status=status,elapsed_seconds=round(time.monotonic()-start,2),scope='CARDLESS_ONLY'),indent=2)+'\n')
        print(folder,flush=True)
    return folder


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=DEFAULT_BASE)
    parser.add_argument('--driver',type=Path)
    parser.add_argument('--owner-module',type=Path,help='fixed owner-module staging and strict client-reload evidence')
    parser.add_argument('--timeout',type=int,default=600)
    parser.add_argument('--cpus',type=int,choices=(1,2),default=1)
    parser.add_argument('--kvm',action='store_true',help='explicit cardless acceleration; requires existing user access to /dev/kvm')
    parser.add_argument('--logging-observer',action='store_true',help='observe only the inert native logging probe; no host devices')
    args=parser.parse_args();run(args.base,args.driver,args.timeout,args.cpus,args.kvm,args.owner_module,args.logging_observer)
if __name__=='__main__':main()
