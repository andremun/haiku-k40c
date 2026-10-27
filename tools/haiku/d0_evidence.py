# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Strict D0 retained-extent serial evidence. No inferred device address is published."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Extent:
    gpa: int
    size: int
    token: int
    lease: int


def native_extent(serial):
    if re.search(r'^\s*(?:PANIC:|KERNEL PANIC\b)',serial,re.I|re.M) or 'k40_os: FAIL' in serial:
        raise RuntimeError('D0 guest failure; stop without retry')
    lines=[line.rstrip('\r') for line in serial.splitlines() if line.startswith('k40_d0:')]
    last_lease=0;original=None;pending=None;detached=0;phase2=False;passed=False
    for line in lines:
        report=re.fullmatch(r'k40_d0: phase=([12]) lease=([0-9]+) token=([0-9]+) gpa=0x([0-9a-f]+) bytes=([0-9]+) quarantine=([01]) visibility=DENIED',line)
        if report:
            phase,lease,token=int(report[1]),int(report[2]),int(report[3]);gpa,size=int(report[4],16),int(report[5]);quarantine=int(report[6])
            if pending or lease<=last_lease or not 0<token<2**64 or lease>=2**64 or size!=4096 or gpa%4096 or not 0<=gpa<2**32 or gpa+size>2**32:
                raise RuntimeError('D0 extent/lifecycle mismatch')
            if phase==1:
                if original is not None or quarantine:raise RuntimeError('D0 repeated fresh allocation')
                original=(gpa,size,token)
            elif original!=(gpa,size,token) or not quarantine or not detached:
                raise RuntimeError('D0 reload did not preserve owned extent')
            pending=(phase,lease,token);last_lease=lease;passed=False;continue
        close=re.fullmatch(r'k40_d0: phase=([12]) detached lease=([0-9]+) token=([0-9]+) retained',line)
        if close:
            values=tuple(int(x) for x in close.groups())
            if values!=pending:raise RuntimeError('D0 detached wrong lease/token')
            detached+=1;phase2|=values[0]==2;pending=None;continue
        if line=='k40_d0: PASS retained host extent only; DMA denied':
            if pending or not phase2:raise RuntimeError('D0 success before retained reload')
            passed=True;continue
        raise RuntimeError('unknown D0 serial record')
    if not passed or pending or original is None:return None
    return Extent(*original,last_lease)
