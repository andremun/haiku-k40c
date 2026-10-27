#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Closed D0 mapping observation. No IOVA publication or GPU writes.

Requires ADR 008, the reviewed package/source suite and the human-started R5 log.
--check reads host/artifact/baseline prerequisites, starts no guest and writes nothing.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime
import hashlib
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import uuid
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).resolve().parent))
import card_run
import d0_stage
from tools.haiku.vm_guard import guest_lock
from tools.haiku.d0_kernel_log import KernelLog
from tools.haiku.d0_evidence import native_extent
from tools.haiku.d0_monitor import snapshot
from tools.haiku.d0_topology import parse as parse_topology
from tools.observer.task_stream import TaskStream
from tools.observer.supervise import observed_child
BASE=card_run.DEFAULT_BASE


def save(path,data):
    if isinstance(data,str):data=data.encode()
    with path.open('xb') as out:out.write(data)


def save_json(path,value):save(path,json.dumps(value,indent=2,sort_keys=True)+'\n')


def job(port):
    host=f'http://10.0.2.2:{port}'
    return '\n'.join(['#!/bin/sh','set -eu',f'host={host}',
        'finish() { code=$?; trap - EXIT; echo "$code" > /tmp/d0.exit; curl -fsS -T /tmp/d0.exit "$host/job.exit" || true; }',
        'trap finish EXIT','uname -a > /tmp/d0.environment',
        'curl -fsS -T /tmp/d0.environment "$host/environment.txt"',
        'curl -fsS -T /boot/system/kernel_x86_64 "$host/kernel_x86_64"',
        'base=$(finddir B_USER_NONPACKAGED_ADDONS_DIRECTORY)',
        'mkdir -p "$base/kernel/generic" "$base/kernel/drivers/bin" "$base/kernel/drivers/dev/misc"',
        'curl -fsS -o "$base/kernel/generic/k40c_owner" "$host/owner"',
        'curl -fsS -o "$base/kernel/drivers/bin/k40_d0_memory_probe" "$host/memory"',
        'curl -fsS -o "$base/kernel/drivers/bin/k40_identity_probe" "$host/identity"',
        'chmod +x "$base/kernel/generic/k40c_owner" "$base/kernel/drivers/bin/k40_d0_memory_probe" "$base/kernel/drivers/bin/k40_identity_probe"',
        'ln -sf ../../bin/k40_d0_memory_probe "$base/kernel/drivers/dev/misc/k40_d0_memory_probe"',
        'ln -sf ../../bin/k40_identity_probe "$base/kernel/drivers/dev/misc/k40_identity_probe"',
        'echo K40-B5-BEGIN > /dev/dprintf',
        'for pass in 1 2 3 4; do ls /dev/misc >/dev/null; sleep 1; done',
        'echo K40-B5-END > /dev/dprintf','echo ready > /tmp/d0.ready',
        'curl -fsS -T /tmp/d0.ready "$host/ready.txt"',
        'poll=0; while [ "$poll" -lt 120 ]; do if curl -fsS "$host/release" >/dev/null 2>&1; then exit 0; fi; poll=$((poll+1)); sleep 1; done','exit 1',''])


@contextmanager
def exchange(folder,evidence,suite):
    lock=threading.Lock();release=threading.Event()
    downloads={name:folder/name for name in ('identity','memory','owner')}
    limits={'environment.txt':65536,'kernel_x86_64':64*1024*1024,'ready.txt':32,'job.exit':16}
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path=='/release':
                self.send_response(200 if release.is_set() else 404);self.end_headers();return
            name=self.path[1:]
            path=folder/'job.sh' if name=='job.sh' else downloads.get(name)
            if path is None:self.send_error(404);return
            data=path.read_bytes();self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        def do_PUT(self):
            name=self.path[1:]
            try:size=int(self.headers.get('Content-Length','-1'))
            except ValueError:self.send_error(400);return
            if name not in limits or not 0<=size<=limits[name]:self.send_error(413);return
            self.connection.settimeout(20);data=self.rfile.read(size)
            if len(data)!=size:self.send_error(400);return
            if name=='kernel_x86_64':
                if hashlib.sha256(data).hexdigest()!=suite['kernel_sha256']:self.send_error(409,'kernel mismatch');return
                name='kernel.sha256';data=(suite['kernel_sha256']+'\n').encode()
            with lock:
                target=evidence/name
                if target.exists():code=201 if target.read_bytes()==data else 409
                else:save(target,data);code=201
            self.send_response(code);self.end_headers()
        def log_message(self,fmt,*args):
            with lock,(evidence/'http.log').open('a') as out:out.write(fmt%args+'\n')
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.daemon_threads=True
    save(folder/'job.sh',job(server.server_address[1]));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:yield server.server_address[1],release
    finally:server.shutdown();server.server_close();thread.join(timeout=5)


def arguments(folder,evidence):
    args=card_run.qemu_args(BASE,folder,evidence,card_run.ALLOWED_BDF)
    args[0]=d0_stage.FILES['qemu'];args[args.index('-name')+1]='k40-d0-map-observe'
    args+=['-qmp','unix:'+str(folder/'qmp')+',server,nowait']
    return args


def monitor(child,folder,evidence,port,release,host,kernel):
    def proof_record(value):
        with (evidence/'task-proofs.jsonl').open('a') as out:
            out.write(json.dumps(value,sort_keys=True)+'\n')
    stream=TaskStream(folder.name,child.process.pid,int(host['group']),
                      target=str(Path(d0_stage.FILES['qemu']).resolve()),sink=proof_record)
    old=b'';pending=b'';launched=False;launch_at=None;terminal_at=None;cutoff=False
    def drain():
        nonlocal old,pending
        current=child.trace.read_bytes() if child.trace.exists() else b''
        if len(current)>16*1024*1024 or not current.startswith(old):
            raise RuntimeError('observer output rewritten or oversized')
        pending+=current[len(old):];old=current
        while b'\n' in pending:
            line,pending=pending.split(b'\n',1)
            if not stream.feed((line+b'\n').decode('ascii')):
                raise RuntimeError('D0 observer: '+str(stream.error))
    start=time.monotonic()
    while time.monotonic()-start<570:
        child.check();kernel.poll()
        for name in ('serial.log','qemu.log'):
            path=evidence/name
            if path.exists() and path.stat().st_size>16*1024*1024:raise RuntimeError('D0 log limit')
        serial=(evidence/'serial.log').read_text(errors='replace') if (evidence/'serial.log').exists() else ''
        allowed={'B5_IDENTITY_READ_ONLY','D0_MEMORY_NO_DEVICE'}
        tags={line.partition('k40_stage: ')[2].strip() for line in serial.splitlines() if 'k40_stage: ' in line}
        if tags-allowed:raise RuntimeError('unexpected guest probe role')
        extent=native_extent(serial)
        drain()
        exited=evidence/'job.exit'
        if exited.exists() and exited.read_bytes().strip()!=b'0':raise RuntimeError('D0 guest job failed')
        if not cutoff and (evidence/'ready.txt').exists() and extent and not pending:
            if (evidence/'ready.txt').read_bytes()!=b'ready\n' or not (evidence/'kernel.sha256').exists():raise RuntimeError('D0 ready/kernel handshake')
            if not card_run.verdict(serial,b'0'):raise RuntimeError('D0 identity evidence incomplete')
            topology=snapshot(folder/'qmp');realized=parse_topology(**topology,physical=True)
            if not realized.contains(extent.gpa,extent.size):raise RuntimeError('D0 allocation is not in realized system RAM')
            # QMP may take time. Include every complete trace record now visible.
            drain()
            if pending:raise RuntimeError('partial observer record at cutoff')
            # Explicit source-selected identity candidate, not a provider conversion.
            witness=stream.coverage(gpa=extent.gpa,iova=extent.gpa,size=extent.size)
            if witness is None:raise RuntimeError('D0 successful map/association coverage missing')
            child.check();kernel.poll()
            for name,data in topology.items():save(evidence/(name+'.txt'),data)
            save_json(evidence/'cutoff.json',dict(gpa=extent.gpa,bytes=extent.size,token=extent.token,lease=extent.lease,
                trace_prefix_bytes=len(old),trace_prefix_sha256=hashlib.sha256(old).hexdigest(),
                container=witness.mapping.identity.container,generation=witness.mapping.identity.generation,
                cutoff=witness.mapping.cutoff,group=witness.group,device_fd=witness.device_fd,
                mapped_segments=[vars(region) for region in witness.mapping.regions],
                claim='structural API map coverage at this cutoff; no hardware payload/coherency proof',publication=False))
            cutoff=True;release.set()
        if cutoff and exited.exists():
            if not card_run.verdict(serial,exited.read_bytes()):raise RuntimeError('D0 final identity incomplete')
            return stream,old,pending
        now=time.monotonic()
        if launch_at is None and ('first login script' in serial or 'Volume::InitialVerify(): volume at "/boot/home/config" is consistent' in serial):launch_at=now+12
        if launch_at is not None and terminal_at is None and now>=launch_at:
            card_run.hmp(folder/'monitor.sock','cmd','sendkey alt-meta_l-t');terminal_at=now+8
        if terminal_at is not None and not launched and now>=terminal_at:
            card_run.hmp(folder/'monitor.sock','type',f'curl -fsS http://10.0.2.2:{port}/job.sh -o /tmp/d0-job.sh; sh /tmp/d0-job.sh');launched=True
        time.sleep(0.5)
    raise RuntimeError('D0 guest deadline; stop without retry')


def finish_trace(trace,stream,prefix,pending):
    data=trace.read_bytes()
    if len(data)>16*1024*1024 or not data.startswith(prefix):
        raise RuntimeError('observer final output rewritten or oversized')
    tail=pending+data[len(prefix):]
    if tail and not tail.endswith(b'\n'):raise RuntimeError('observer final record incomplete')
    for line in tail.splitlines(keepends=True):
        if not stream.feed(line.decode('ascii')):
            raise RuntimeError('observer final history: '+str(stream.error))


def prerequisites():
    if not os.access('/dev/kvm',os.R_OK|os.W_OK):raise ValueError('KVM access unavailable')
    for path in (BASE,BASE.parent/'vars.fd',Path(os.environ.get('HAIKU_OVMF_DIR','/usr/share/OVMF'))/'OVMF_CODE_4M.fd'):
        if not Path(path).is_file() or not os.access(path,os.R_OK):
            raise ValueError('missing readable VM prerequisite: '+str(path))


def run():
    if os.geteuid()==0:raise ValueError('root execution forbidden')
    if os.environ.get('GPU_BDF',card_run.ALLOWED_BDF)!=card_run.ALLOWED_BDF:raise ValueError('only 04:00.0 is approved')
    suite=d0_stage.validate()
    prerequisites()
    host=card_run.preflight(card_run.ALLOWED_BDF)
    with guest_lock(BASE.parent),KernelLog() as kernel:
        evidence=ROOT/'results'/(datetime.now().strftime('%Y%m%d')+'-d0-mapping-retry-01')
        evidence.mkdir(mode=0o700,exist_ok=False)
        folder=ROOT/'build/d0'/uuid.uuid4().hex[:8];folder.mkdir(mode=0o700,parents=True,exist_ok=False)
        if max(len(os.fsencode(folder/name)) for name in ('qmp','monitor.sock'))>107:raise ValueError('monitor path too long')
        for role in ('identity','memory','owner'):
            shutil.copyfile(suite['artifacts'][role]['path'],folder/role)
            if d0_stage.sha(folder/role)!=suite['artifacts'][role]['sha256']:raise ValueError('staged artifact differs')
        shutil.copyfile(BASE.parent/'vars.fd',folder/'vars.fd')
        subprocess.run(['qemu-img','create','-q','-f','qcow2','-F','qcow2','-b',str(BASE.resolve()),str(folder/'overlay.qcow2')],check=True)
        args=arguments(folder,evidence);save(evidence/'kernel-before.log',kernel.before)
        save_json(evidence/'launch.json',dict(stage=d0_stage.STAGE,args=args,host=host,suite=suite,
            timeout_seconds=600,kernel_stream=kernel.metadata(),source_commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()))
        status='failed';error='';start=time.monotonic()
        try:
            with exchange(folder,evidence,suite) as (port,release),(evidence/'qemu.log').open('xb') as log:
                if card_run.preflight(card_run.ALLOWED_BDF)!=host:raise ValueError('host isolation changed')
                # Revalidate executable/source bytes immediately before the process boundary.
                if d0_stage.validate()!=suite:raise ValueError('suite changed before launch')
                with observed_child(suite['artifacts']['observer']['path'],args,evidence/'trace.log',log,600,evidence/'watchdog.txt',
                                    ['/dev/vfio/vfio',host['vfio']]) as child:
                    save_json(evidence/'processes.json',dict(qemu_pid=child.process.pid,tracer_pid=child.tracer,kernel_reader_pid=kernel.pid))
                    stream,prefix,pending=monitor(child,folder,evidence,port,release,host,kernel)
                finish_trace(evidence/'trace.log',stream,prefix,pending)
                save(evidence/'kernel-after.log',kernel.poll());status='pass'
        except BaseException as exc:error=str(exc);raise
        finally:
            if not (evidence/'kernel-after.log').exists():
                try:save(evidence/'kernel-after.log',kernel.capture())
                except (OSError,RuntimeError):save(evidence/'kernel-after-unavailable.txt','host log capture failed\n')
            save_json(evidence/'result.json',dict(status=status,error=error,stage=d0_stage.STAGE,
                elapsed_seconds=round(time.monotonic()-start,2),
                claim='structural mapping observation only' if status=='pass' else 'none',
                device_payload_verified=False,coherency_verified=False,publication=False,
                kernel_log_scope='no new fault indication in filtered classes' if status=='pass' else 'not established',
                kernel_filter=kernel.metadata()['filter_pattern']))
            print(evidence,flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.check:
        try:
            if os.geteuid()==0:raise ValueError('root execution forbidden')
            d0_stage.validate();prerequisites()
            if os.environ.get('GPU_BDF',card_run.ALLOWED_BDF)!=card_run.ALLOWED_BDF:raise ValueError('only 04:00.0 is approved')
            card_run.preflight(card_run.ALLOWED_BDF)
            with KernelLog() as log:log.poll()
        except (OSError,ValueError,RuntimeError) as error:
            print('D0 prerequisite: '+str(error)+'; see R5 in docs/REQUESTS.md',file=sys.stderr)
            return 1
        print('D0 prerequisites available; no guest started')
    else:run()
    return 0

if __name__=='__main__':raise SystemExit(main())
