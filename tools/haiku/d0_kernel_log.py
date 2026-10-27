# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Read the human-started R5 journal stream. Never starts a privileged process.

A user-provided log is a baseline input, not authenticated DMA/coherency evidence.
Pin the live reader with pidfd, detect replacement/truncation, and preserve raw data.
"""
import hashlib
import os
from pathlib import Path
import re
import select
import stat

PATH=Path('/tmp/k40-s1-kernel.log')
FAULT=re.compile(r'(?i)(?:dmar|amd-vi|iommu|vfio|remapping).*\b(?:faults?|errors?|failed|failure|timeout|invalid)\b|\b(?:faults?|errors?|failed|failure|timeout|invalid)\b.*(?:dmar|amd-vi|iommu|vfio|remapping)')
REQUIRED={'-k','-b','-f','--no-pager','--output=short-monotonic'}


def find_reader(proc=Path('/proc')):
    found=[]
    for entry in proc.glob('[0-9]*'):
        try:args=(entry/'cmdline').read_bytes().split(b'\0')
        except (FileNotFoundError,PermissionError,ProcessLookupError):continue
        if args and Path(os.fsdecode(args[0])).name=='journalctl' and REQUIRED<=set(os.fsdecode(x) for x in args[1:] if x):
            found.append(int(entry.name))
    if len(found)!=1:raise ValueError('R5 requires one identifiable live kernel journal reader')
    return found[0]


class KernelLog:
    def __init__(self,path=PATH,reader=None):
        self.path=Path(path);self.fd=None;self.reader_fd=None
        try:
            self.fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            info=os.fstat(self.fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid not in (0,os.getuid()):raise ValueError('R5 log ownership/type')
            self.identity=(info.st_dev,info.st_ino)
            self.pid=find_reader() if reader is None else reader
            self.reader_fd=os.pidfd_open(self.pid)
            self.before=self._read()
            if not re.search(rb'^\[\s*[0-9]+\.[0-9]+\].*kernel:',self.before,re.M):raise ValueError('R5 lacks a kernel baseline')
            self.observed=self.before
            self.last=self.before
            self.prefix=hashlib.sha256(self.before).digest()
        except BaseException:self.close();raise

    def _read(self):
        if self.reader_fd is None or select.select([self.reader_fd],[],[],0)[0]:raise RuntimeError('kernel journal reader exited')
        named=self.path.lstat()
        if stat.S_ISLNK(named.st_mode) or (named.st_dev,named.st_ino)!=self.identity:raise RuntimeError('kernel log replaced')
        info=os.fstat(self.fd)
        if info.st_size>16*1024*1024:raise RuntimeError('kernel log output limit')
        data=os.pread(self.fd,info.st_size,0)
        # Preserve complete records. A currently appended partial line waits for the next poll.
        return data[:data.rfind(b'\n')+1]

    def poll(self):
        data=self._read();self.observed=data
        if len(data)<len(self.last) or hashlib.sha256(data[:len(self.last)]).digest()!=self.prefix:
            raise RuntimeError('kernel log truncated or rewritten')
        delta=data[len(self.last):].decode('utf-8',errors='replace')
        if any(FAULT.search(line) for line in delta.splitlines()):raise RuntimeError('new host IOMMU/VFIO fault; stop without retry')
        self.last=data;self.prefix=hashlib.sha256(data).digest()
        return data

    def capture(self):
        info=os.fstat(self.fd)
        if info.st_size>16*1024*1024:raise RuntimeError('kernel capture bound')
        return os.pread(self.fd,info.st_size,0)

    def close(self):
        for name in ('reader_fd','fd'):
            fd=getattr(self,name,None)
            if fd is not None:os.close(fd);setattr(self,name,None)
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
