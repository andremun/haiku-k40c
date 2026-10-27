# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Validate pinned syscall-stop task proofs before sharing the FD namespace.

The proof comes from the exact owned tracer, not caller-provided metadata. Keep
all raw lines. Normalization never authenticates arbitrary external trace files.
"""
import re
from tools.observer.binding import BoundStream

PROOF=re.compile(r'K40_TASK\{tgid=([0-9]+), files=(-?[0-9]+)\} ')


class TaskStream:
    def __init__(self,launch,pid,group,*,target=None,sink=None):
        self._base=BoundStream(launch,pid,group)
        self._pid=pid
        self._target=target
        self._sink=sink
        self._error=None
        self._seen=False
        self._exec=False
        self._count=0
        self._proofs=0

    @property
    def error(self):return self._error or self._base.error

    def feed(self,line):
        if self.error:return False
        try:return self._feed(line)
        except ValueError as error:self._error=str(error);return False

    def _feed(self,line):
        self._count+=1
        if self._count>100000 or not isinstance(line,str) or len(line)>8192:
            raise ValueError('task record capacity/type')
        frame=re.fullmatch(r'([1-9][0-9]{0,9}) +([^\n]+)\n',line)
        if not frame:raise ValueError('task record framing')
        pid,text=int(frame[1]),frame[2]
        if re.match(r'(?:execve|execveat|unshare|close_range)\(',text):
            first=(not self._seen and pid==self._pid and self._target is not None
                and text.startswith('execve("'+self._target+'", ') and text.endswith(') = 0')
                and not any(word in text for word in ('unfinished','resumed','INJECTED')))
            if not first:raise ValueError('file-table replacement/split or unknown exec')
            self._exec=True;self._seen=True;return True
        self._seen=True
        proofs=list(PROOF.finditer(text))
        if len(proofs)>1:raise ValueError('multiple task proofs')
        proof=proofs[0] if proofs else None
        if 'K40_TASK' in text and proof is None:raise ValueError('malformed task proof')
        cleaned=PROOF.sub('',text)
        close=re.fullmatch(r'close\(([0-9]+)(?:<[^<>\n]*>)?\) += .+',cleaned)
        # An unrelated close has no mapping effect; preserve BoundStream's policy.
        unrelated=close and not self._base.related_fd(int(close[1]))
        if not unrelated and (pid!=self._pid or proof is not None):
            if proof is None or int(proof[1])!=self._pid or int(proof[2])!=0:
                raise ValueError('missing or unequal syscall task/FD-table proof')
            # The marker must be in the actual argument slot, not an annotation.
            if close:
                if not text.startswith('close('+proof[0]):raise ValueError('close proof position')
            elif not re.fullmatch(r'ioctl\([^,]+, 0x[0-9a-f]+, '+re.escape(proof[0])+r'.+\) += .+',text):
                raise ValueError('ioctl proof position')
            self._proofs+=1
            if self._proofs>4096:raise ValueError('task proof capacity')
            if self._sink:self._sink(dict(record=self._count,tid=pid,tgid=int(proof[1]),kcmp_files=int(proof[2])))
            pid=self._pid
        # Never remove any other opaque text or bypass BoundStream semantics.
        return self._base.feed(str(pid)+' '+cleaned+'\n')

    def coverage(self,**request):
        if self.error or (self._target is not None and not self._exec):return None
        return self._base.coverage(**request)

    def current(self,witness):
        return not self.error and self._base.current(witness)
