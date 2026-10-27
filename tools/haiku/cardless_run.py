#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Bounded, snapshot-only Haiku kernel/probe runner. No host devices/options.

Boots an overlay of the existing cardless application guest. It never modifies
that base disk or accepts additional QEMU arguments. Serial and HTTP results
are saved incrementally in ignored build/cardless/RUN/. Requires no sudo/KVM.
"""
import argparse
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


def run(base,driver,seconds,cpus=1,kvm=False):
    from vm_guard import guest_lock

    with guest_lock(base.parent):
        return _run(base,driver,seconds,cpus,kvm)


def _run(base,driver,seconds,cpus=1,kvm=False):
    if not 30<=seconds<=600:raise ValueError('timeout must be 30..600 seconds')
    if cpus not in (1,2):raise ValueError('cardless CPU count must be one or two')
    if kvm and not os.access('/dev/kvm',os.R_OK|os.W_OK):raise ValueError('KVM unavailable to this user; no sudo attempted')
    if not base.is_file():raise ValueError('missing cardless base disk')
    if driver is not None and not driver.is_file():raise ValueError('missing driver binary')
    folder=ROOT/'build/cardless'/time.strftime('%Y%m%d-%H%M%S')
    folder.mkdir(parents=True,exist_ok=False)
    # The monitor socket stays in the run folder, not in /tmp (sun_path: 107 bytes at most).
    monitor=folder/'monitor.sock'
    if len(os.fsencode(monitor))>107:raise ValueError('run folder path is too long for a monitor socket')
    peer_vars=base.parent/'vars.fd'
    shutil.copyfile(peer_vars if peer_vars.is_file() else '/usr/share/OVMF/OVMF_VARS_4M.fd',folder/'vars.fd')
    subprocess.run(['qemu-img','create','-q','-f','qcow2','-F','qcow2','-b',str(base.resolve()),str(folder/'overlay.qcow2')],check=True)
    if driver is not None:shutil.copyfile(driver,folder/'probe')
    received=set()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            name=self.path.lstrip('/')
            if name not in ('job.sh','probe') or not (folder/name).is_file():self.send_error(404);return
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
    commands=['#!/bin/sh','set -eu',f'host=http://10.0.2.2:{port}',
              'uname -a > /tmp/k40-environment.txt','curl -fsS -T /tmp/k40-environment.txt "$host/environment.txt"',
              'curl -fsS -T /boot/system/kernel_x86_64 "$host/kernel_x86_64"']
    if driver is not None:
        commands += ['base=/boot/system/non-packaged/add-ons/kernel/drivers',
                     'mkdir -p "$base/bin" "$base/dev/misc"',
                     'curl -fsS -o "$base/bin/k40_cardless_probe" "$host/probe"',
                     'chmod +x "$base/bin/k40_cardless_probe"',
                     'ln -sf ../../bin/k40_cardless_probe "$base/dev/misc/k40_cardless_probe"',
                     'echo K40-CARDLESS-BEGIN > /dev/dprintf','ls /dev/misc >/dev/null','sleep 3',
                     'echo K40-CARDLESS-END > /dev/dprintf']
    commands += ['echo 0 > /tmp/k40-job.exit','curl -fsS -T /tmp/k40-job.exit "$host/job.exit"']
    (folder/'job.sh').write_text('\n'.join(commands)+'\n')
    args=['qemu-system-x86_64','-name','k40-cardless-verification','-machine','q35','-accel','kvm' if kvm else 'tcg,thread=multi','-cpu','host' if kvm else 'qemu64','-smp',str(cpus),'-m','4096',
          '-drive','if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd',
          '-drive','if=pflash,format=raw,file='+str(folder/'vars.fd'),
          '-drive','file='+str(folder/'overlay.qcow2')+',format=qcow2,if=none,id=system',
          '-device','ide-hd,drive=system,bus=ide.0,bootindex=1','-device','qemu-xhci','-device','usb-tablet','-vga','std',
          '-netdev','user,id=n0','-device','e1000,netdev=n0','-display','none',
          '-serial','file:'+str(folder/'serial.log'),'-monitor','unix:'+str(monitor)+',server,nowait']
    (folder/'launch.json').write_text(json.dumps(dict(args=args,base=str(base),timeout_seconds=seconds,scope='CARDLESS_KVM' if kvm else 'CARDLESS_TCG'),indent=2)+'\n')
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    process=None;watchdog=None;start=time.monotonic();status='failed'
    def hmp(mode,text):
        subprocess.run(['python3',str(HMP),str(monitor),mode,text],check=True,timeout=30,stdout=subprocess.DEVNULL)
    try:
        with (folder/'qemu.log').open('wb') as log:
            process=subprocess.Popen(args,stdout=log,stderr=log)
            def timeout():
                if process.poll() is None:process.kill()
            watchdog=threading.Timer(seconds,timeout);watchdog.daemon=True;watchdog.start()
            launched=False
            while time.monotonic()-start<seconds and process.poll() is None:
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
                        if not probe_complete(serial):time.sleep(1);continue
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
    parser.add_argument('--timeout',type=int,default=600)
    parser.add_argument('--cpus',type=int,choices=(1,2),default=1)
    parser.add_argument('--kvm',action='store_true',help='explicit cardless acceleration; requires existing user access to /dev/kvm')
    args=parser.parse_args();run(args.base,args.driver,args.timeout,args.cpus,args.kvm)
if __name__=='__main__':main()
