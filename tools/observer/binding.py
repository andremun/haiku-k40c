# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""D0 fixed-device association over the pinned single-process observation subset.

The stage must separately validate the executable/process and realized address
space. Neither a parsed binding nor a witness enables a DMA provider.
"""
from dataclasses import dataclass
import re
from tools.observer.normalize import Stream, InvalidTrace, result, NUMBER

STATUS, ATTACH, DETACH, DEVICE = 0x3b67,0x3b68,0x3b69,0x3b6a  # vfio.h VFIO_BASE+3..6.


@dataclass(frozen=True)
class BindingWitness:
    mapping: object
    revision: int
    group: int
    device_fd: int


class BoundStream:
    def __init__(self,launch,pid,group):
        if type(group) is not int or not 0<=group<2**31:raise ValueError('group identity')
        self._base=Stream(launch,expected_pid=pid)
        self._pid,self._group=pid,group
        self._group_path='/dev/vfio/'+str(group)
        self._group_fd=None;self._container_fd=None;self._device_fd=None
        self._viable=False;self._retired=False;self._revision=0;self._error=None
        self._lines=0;self._bytes=0

    @property
    def error(self):return self._error or self._base.error

    def feed(self,line):
        if self.error:return False
        try:self._feed(line)
        except (InvalidTrace,ValueError) as error:self._error=str(error);return False
        return True

    def _feed(self,line):
        if type(line) is not str or not line.isascii() or not line.endswith('\n') or line.count('\n')!=1 or len(line)>8192:
            raise InvalidTrace('binding line framing')
        self._lines+=1;self._bytes+=len(line)
        if self._lines>100000 or self._bytes>16*1024*1024:raise InvalidTrace('binding output bounds')
        if any(x in line for x in ('unfinished','resumed','INJECTED','ERESTART','unreadable')):raise InvalidTrace('ambiguous binding record')
        frame=re.fullmatch(r'([1-9][0-9]{0,9}) +([^\n]+)\n',line)
        if not frame:raise InvalidTrace('binding process format')
        pid,text=int(frame[1]),frame[2]
        # All closes are captured, including anonymous device FDs. Unrelated
        # descriptors have no mapping effects and may belong to other threads.
        closed=re.fullmatch(r'close\(([0-9]+)(?:<[^<>\n]*>)?\) += (.+)',text)
        if closed:
            fd=int(closed[1])
            known=fd in (self._group_fd,self._container_fd,self._device_fd)
            if not known:return
            if pid!=self._pid or result(closed[2])!=(0,0):raise InvalidTrace('unproved/failed related close')
            self._revision+=1;self._retired=True
            if fd==self._container_fd:
                if not self._base.feed(line):raise InvalidTrace(self._base.error)
                self._container_fd=None;self._device_fd=None
            if fd==self._device_fd:self._device_fd=None
            if fd==self._group_fd:self._group_fd=None;self._container_fd=None;self._device_fd=None;self._viable=False
            return
        if pid!=self._pid:raise InvalidTrace('unproved binding process')
        group=re.escape(self._group_path)
        opened=re.fullmatch(r'openat\(-100(?:<[^<>\n]{1,4096}>)?, "'+group+r'", ('+NUMBER+r')\) += ([0-9]+)<'+group+r'>',text)
        if opened:
            flags,fd=(int(v,0) for v in opened.groups())
            if self._retired or self._group_fd is not None or self._base.has_fd(fd) or fd==self._device_fd or flags not in (2,0x80002):raise InvalidTrace('group open ambiguity')
            self._group_fd=fd;self._revision+=1;return
        call=re.fullmatch(r'ioctl\(([0-9]+)<'+group+r'>, (0x[0-9a-f]+), (.+)\) += (.+)',text)
        if call:
            fd,code=int(call[1]),int(call[2],16)
            if fd!=self._group_fd:raise InvalidTrace('unknown group descriptor')
            returned,err=result(call[4]);body=call[3]
            if returned<0 or err:raise InvalidTrace('failed group operation')
            self._revision+=1
            if code==STATUS:
                status=re.fullmatch(r'K40_STATUS\{argsz=8, flags=('+NUMBER+r')\}',body)
                if not status or int(status[1],0)&~3 or not int(status[1],0)&1:raise InvalidTrace('nonviable or unknown group status')
                self._viable=True;return
            if not self._viable:raise InvalidTrace('missing viable group status')
            if code==ATTACH:
                attach=re.fullmatch(r'K40_ATTACH\{([0-9]+)\}',body)
                if self._retired or not attach or returned or self._container_fd is not None:raise InvalidTrace('ambiguous attachment')
                container=int(attach[1]);self._base._context(container)
                self._container_fd=container;return
            if code==DEVICE:
                if self._retired or body!='K40_DEVICE{"0000:04:00.0"}' or not 0<returned<2**31 or returned in (self._container_fd,self._group_fd) or self._container_fd is None or self._device_fd is not None:
                    raise InvalidTrace('device identity or lifetime mismatch')
                self._device_fd=returned;return
            if code==DETACH and body=='K40_DETACH{}' and returned==0:
                self._container_fd=None;self._device_fd=None;self._retired=True;return
            raise InvalidTrace('unknown group operation')
        reopened=re.search(r' = ([0-9]+)</dev/vfio/vfio>$',text)
        if reopened and int(reopened[1]) in (self._group_fd,self._device_fd):raise InvalidTrace('descriptor role collision')
        if not self._base.feed(line):raise InvalidTrace(self._base.error)

    def related_fd(self,fd):
        return fd in (self._group_fd,self._container_fd,self._device_fd) or self._base.has_fd(fd)

    def coverage(self,**request):
        if self.error or self._retired or self._container_fd is None or self._device_fd is None:return None
        mapping=self._base.coverage(self._container_fd,**request)
        return BindingWitness(mapping,self._revision,self._group,self._device_fd) if mapping else None

    def current(self,witness):
        return (not self.error and not self._retired and isinstance(witness,BindingWitness) and witness.revision==self._revision
            and witness.group==self._group and witness.device_fd==self._device_fd and self._container_fd is not None
            and self._base.current(self._container_fd,witness.mapping))
