# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Owned-child observer supervision. The stage caller supplies fixed reviewed argv.

-D keeps the tracee at Popen.pid. The existing independent pidfd watchdog therefore
watches the actual target, even if the tracer grandchild dies. No process is attached.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import select
import signal
import subprocess
import time
from tools.haiku.vm_guard import deadline


def tracer_pid(pid):
    for line in Path(f'/proc/{pid}/status').read_text().splitlines():
        if line.startswith('TracerPid:'):return int(line.split()[1])
    raise RuntimeError('tracee status has no tracer identity')


class Child:
    def __init__(self,process,observer,target,trace,seconds):
        self.process,self.observer,self.target,self.trace,self.seconds=process,observer,target,trace,seconds
        self.tracer=0;self.tracer_fd=None

    def ready(self):
        end=time.monotonic()+min(10,self.seconds)
        while self.process.poll() is None and time.monotonic()<end:
            try:
                pid=tracer_pid(self.process.pid)
                if pid and Path(f'/proc/{self.process.pid}/exe').resolve(strict=True)==self.target:
                    fd=os.pidfd_open(pid)
                    try:
                        if Path(f'/proc/{pid}/exe').resolve(strict=True)!=self.observer:
                            raise RuntimeError('unexpected tracer executable')
                        if tracer_pid(self.process.pid)!=pid:raise RuntimeError('tracer changed during readiness')
                    except BaseException:os.close(fd);raise
                    self.tracer,self.tracer_fd=pid,fd
                    self.check();return
            except (FileNotFoundError,ProcessLookupError):pass
            time.sleep(0.02)
        raise RuntimeError('owned target/observer readiness failed')

    def check(self):
        if self.process.poll() is not None:raise RuntimeError('owned target exited')
        if self.tracer_fd is None or select.select([self.tracer_fd],[],[],0)[0]:
            raise RuntimeError('observer exited; do not accept incomplete evidence')
        if tracer_pid(self.process.pid)!=self.tracer:raise RuntimeError('observer identity changed')
        if self.trace.exists() and self.trace.stat().st_size>16*1024*1024:raise RuntimeError('observer output limit')

    def stop(self):
        if self.process.poll() is None:self.process.terminate()
        try:self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=5)
        if self.tracer_fd is not None:
            if not select.select([self.tracer_fd],[],[],5)[0]:
                try:signal.pidfd_send_signal(self.tracer_fd,signal.SIGKILL)
                except ProcessLookupError:pass
                os.close(self.tracer_fd);self.tracer_fd=None
                raise RuntimeError('observer did not finish after owned target exit')
            os.close(self.tracer_fd);self.tracer_fd=None


@contextmanager
def observed_child(observer,argv,trace,log,seconds,watch_record,paths):
    if os.geteuid()==0:raise ValueError('root execution forbidden')
    if not 0<seconds<=600:raise ValueError('deadline outside stage bounds')
    observer=Path(observer).resolve(strict=True);target=Path(argv[0]).resolve(strict=True)
    if trace.exists():raise ValueError('observer output must be fresh')
    command=[str(observer),'-D','-f','-qq','-y','-X','raw','-e','trace=openat,ioctl,close,dup,dup2,dup3,fcntl,execve,execveat,unshare,close_range','-e','signal=none']
    for path in sorted(set(paths)):command+=['-P',path]
    command+=['-o',str(trace),'--',str(target),*argv[1:]]
    process=subprocess.Popen(command,stdout=log,stderr=log,start_new_session=True)
    child=Child(process,observer,target,trace,seconds)
    try:
        with deadline(process,seconds,watch_record):
            child.ready();yield child
    finally:child.stop()
