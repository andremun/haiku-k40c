# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Strict boundary for the pinned K40 decoder's path-filtered owned-child stream.

Not a general strace parser or authentication mechanism. Inputs must be complete
lines from the fixed -f -qq -y -X raw format. Ambiguity permanently closes coverage.
"""
from dataclasses import dataclass
import errno as errors
import re
from tools.dma_model import Backend, Identity, Ledger, Observation, Operation

# Linux userspace vfio.h: VFIO_TYPE=';', VFIO_BASE=100, _IO requests +0/1/2/12/13/14.
VERSION, EXTENSION, SETUP, INFO, MAP, UNMAP = (0x3b64,0x3b65,0x3b66,0x3b70,0x3b71,0x3b72)
NUMBER = r'(?:0x[0-9a-f]{1,16}|0|[1-9][0-9]{0,19})'


class InvalidTrace(ValueError):
    pass


def result(text):
    if re.fullmatch(r'0|[1-9][0-9]{0,9}',text):
        return int(text),0
    match=re.fullmatch(r'-1 (E[A-Z0-9]+) \([^()\n]*\)',text)
    if not match or match[1] not in errors.__dict__ or match[1]=='EINTR':
        raise InvalidTrace('unrecognized or interrupted result')
    return -1,getattr(errors,match[1])


def payload(code,text,return_code):
    """Decode only the original include's exact fields, never raw pointee guesses."""
    if code==SETUP:
        match=re.fullmatch(r'K40_SETUP\{('+NUMBER+r')\}',text)
        if not match:raise InvalidTrace('missing setup decoder')
        return dict(backend={1:Backend.TYPE1,3:Backend.TYPE1V2}.get(int(match[1],0)))
    if code==MAP:
        match=re.fullmatch(r'K40_MAP\{argsz=32, flags=('+NUMBER+r'), hva=('+NUMBER+r'), iova=('+NUMBER+r'), size=('+NUMBER+r')\}',text)
        if not match:raise InvalidTrace('unsupported map layout or opaque pointer')
        flags,hva,iova,size=(int(x,0) for x in match.groups())
        if not flags or flags & ~3:raise InvalidTrace('unsupported map flags')
        return dict(hva=hva,iova=iova,size=size,read=bool(flags&1),write=bool(flags&2))
    if code==UNMAP:
        match=re.fullmatch(r'K40_UNMAP\{argsz=24, flags=0, iova=('+NUMBER+r'), size=('+NUMBER+r'), returned=('+NUMBER+r'|error)\}',text)
        if not match:raise InvalidTrace('unsupported unmap layout or unreadable return')
        iova,size,returned=match.groups()
        if (returned=='error') != (return_code==-1):raise InvalidTrace('unmap return contradicts syscall')
        return dict(iova=int(iova,0),size=int(size,0),returned_size=0 if returned=='error' else int(returned,0))
    if code in (VERSION,EXTENSION,INFO) and re.fullmatch(NUMBER,text):return {}
    raise InvalidTrace('unreviewed ioctl or payload')


@dataclass
class Context:
    ledger: Ledger
    active: bool = True


class Stream:
    def __init__(self,launch,*,fixture=False,max_bytes=16*1024*1024,max_lines=100000):
        # Validate launch with the same policy as the typed ledger.
        Ledger(Identity(launch,1,1))
        if type(fixture) is not bool or type(max_bytes) is not int or not 0<max_bytes<=16*1024*1024 or type(max_lines) is not int or not 0<max_lines<=100000:
            raise ValueError('observer bounds')
        self._launch=launch
        self._path='/dev/null' if fixture else '/dev/vfio/vfio'
        self._bytes=0;self._lines=0;self._pid=None;self._next=1;self._contexts={}
        self._max_bytes=max_bytes;self._max_lines=max_lines
        self._error=None

    @property
    def error(self):
        return self._error

    def feed(self,line):
        if self.error:return False
        try:self._feed(line)
        except (InvalidTrace,ValueError) as error:
            self._error=str(error);return False
        return True

    def _feed(self,line):
        if (type(line) is not str or not line.isascii() or not line.endswith('\n')
                or line.count('\n')!=1 or len(line)>8192):raise InvalidTrace('line framing')
        self._bytes+=len(line);self._lines+=1
        if self._bytes>self._max_bytes or self._lines>self._max_lines:raise InvalidTrace('stream capacity')
        if any(word in line for word in ('unfinished','resumed','INJECTED','ERESTART','unreadable')):
            raise InvalidTrace('incomplete, restarted, injected or unreadable record')
        prefix=re.fullmatch(r'([1-9][0-9]{0,9}) +([^\n]+)\n',line)
        if not prefix:raise InvalidTrace('unsupported process/output format')
        pid=int(prefix[1]);text=prefix[2]
        if self._pid is None:self._pid=pid
        if pid!=self._pid:raise InvalidTrace('unproved shared-fd process identity')
        path=re.escape(self._path)
        opened=re.fullmatch(r'openat\(-100(?:<[^<>\n]{1,4096}>)?, "'+path+r'", ('+NUMBER+r')\) += ([0-9]+)<'+path+r'>',text)
        if opened:
            flags,fd=(int(x,0) for x in opened.groups())
            if flags not in (2,0x80002) or self._next>32:raise InvalidTrace('open flags or context capacity')
            if fd in self._contexts and self._contexts[fd].active:raise InvalidTrace('fd replaced without close')
            self._contexts[fd]=Context(Ledger(Identity(self._launch,self._next,self._next)))
            self._next+=1;return
        closed=re.fullmatch(r'close\(([0-9]+)<'+path+r'>\) += 0',text)
        if closed:
            context=self._context(int(closed[1]));context.active=False;return
        call=re.fullmatch(r'ioctl\(([0-9]+)<'+path+r'>, (0x[0-9a-f]+), (.+)\) += (.+)',text)
        if not call:raise InvalidTrace('unknown operation, FD duplication or opaque format')
        fd,code=int(call[1]),int(call[2],16);context=self._context(fd)
        returned,err=result(call[4]);fields=payload(code,call[3],returned)
        if code in (VERSION,EXTENSION,INFO):
            if context.ledger.cutoff:
                self._event(context,Operation.ANNOUNCE)
            return
        if returned not in (-1,0):raise InvalidTrace('nonzero successful mapping result')
        self._event(context,{SETUP:Operation.SETUP,MAP:Operation.MAP,UNMAP:Operation.UNMAP}[code],result=returned,errno=err,**fields)

    def _context(self,fd):
        if fd not in self._contexts or not self._contexts[fd].active:raise InvalidTrace('unknown or closed descriptor')
        return self._contexts[fd]

    def _event(self,context,operation,**fields):
        ledger=context.ledger
        if not ledger.apply(Observation(ledger.identity,ledger.cutoff+1,operation,**fields)):
            raise InvalidTrace(ledger.error)

    def coverage(self,fd,**request):
        if self.error:return None
        try:return self._context(fd).ledger.coverage(**request)
        except InvalidTrace:return None

    def current(self,fd,witness):
        if self.error:return False
        try:return self._context(fd).ledger.current(witness)
        except InvalidTrace:return False
