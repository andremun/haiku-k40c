# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Bounded host-only mapping history. No parser, device API or publication authority.

Normalized observations are fixtures, not authenticated evidence. A witness means
only that this supplied history has structural coverage at its current cutoff.
Source rules: docs/DMA-CONTRACT.md; Linux v6.8 vfio_iommu_type1.c:1279-1426.
"""
from dataclasses import dataclass
from enum import Enum
import re

LIMIT = 1 << 64  # Software validation bound for the VFIO 64-bit fields.


class Backend(Enum):
    TYPE1 = 'type1'
    TYPE1V2 = 'type1v2'


class Operation(Enum):
    SETUP = 'setup'
    MAP = 'map'
    UNMAP = 'unmap'
    ANNOUNCE = 'announce'


@dataclass(frozen=True)
class Identity:
    launch: str
    container: int  # Stable observer identity, never an unqualified reused fd.
    generation: int
    device: str = '0000:04:00.0'  # Repository policy, not a hardware constant.


@dataclass(frozen=True)
class Observation:
    identity: Identity
    sequence: int
    operation: Operation
    complete: bool = True
    result: int | None = 0
    errno: int = 0
    backend: Backend | None = None
    iova: int = 0
    size: int = 0
    hva: int = 0
    read: bool = False
    write: bool = False
    returned_size: int = 0
    flags: int = 0  # Only ordinary map/unmap supported, no VADDR/ALL/dirty mode.


@dataclass(frozen=True)
class Region:
    iova: int
    size: int
    hva: int
    read: bool
    write: bool


@dataclass(frozen=True)
class Witness:
    identity: Identity
    cutoff: int
    gpa: int  # Explicit separate input. No GPA -> IOVA inference is performed.
    iova: int
    size: int
    read: bool
    write: bool
    regions: tuple[Region, ...]
    # No token or field convertible to DmaMapping.verified/publication permission.


def integer(value, low=0, high=LIMIT):
    return type(value) is int and low <= value < high


def extent(base, size):
    return integer(base) and integer(size, 1) and base + size <= LIMIT


class Ledger:
    def __init__(self, identity, *, page_size=4096, capacity=256, max_events=65536):
        if (not isinstance(identity, Identity) or not isinstance(identity.launch, str)
                or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', identity.launch)
                or not integer(identity.container, 1) or not integer(identity.generation, 1)
                or identity.device != '0000:04:00.0'
                or not integer(page_size, 1) or page_size & (page_size-1)
                or not integer(capacity, 1, 4097) or not integer(max_events, 1, 1048577)):
            raise ValueError('unsupported identity or model capacity')
        self._identity = identity
        self._page_size, self._capacity, self._max_events = page_size, capacity, max_events
        self._sequence = 0
        self._backend = None
        self._regions = ()
        self._error = None

    @property
    def identity(self):
        return self._identity

    @property
    def error(self):
        return self._error

    @property
    def cutoff(self):
        return self._sequence

    def _fail(self, reason):
        self._error = reason
        return False

    def _range(self, base, size):
        return extent(base, size) and not ((base | size) & (self._page_size-1))

    def apply(self, event):
        if self._error:
            return False
        if (not isinstance(event, Observation) or event.identity != self.identity
                or not integer(event.sequence, 1) or event.sequence != self._sequence+1
                or event.sequence > self._max_events):
            return self._fail('identity, sequence or event capacity')
        self._sequence = event.sequence
        if (event.complete is not True or type(event.result) is not int
                or event.result not in (0, -1) or not integer(event.errno, 0, 4096)
                or (event.result == 0) != (event.errno == 0)):
            return self._fail('incomplete or ambiguous syscall result')
        if not isinstance(event.operation, Operation) or type(event.flags) is not int or event.flags:
            return self._fail('unsupported operation or flags')
        if event.operation == Operation.SETUP:
            if self._backend or event.result or not isinstance(event.backend, Backend):
                return self._fail('unsupported or repeated backend setup')
            self._backend = event.backend
            return True
        if not self._backend:
            return self._fail('no successful backend setup')
        if event.operation == Operation.ANNOUNCE:
            return True  # Never adds coverage; it still advances the evidence cutoff.
        if not self._range(event.iova, event.size):
            return self._fail('invalid IOVA extent')
        if event.operation == Operation.MAP:
            if (not self._range(event.hva, event.size) or type(event.read) is not bool
                    or type(event.write) is not bool or not (event.read or event.write)):
                return self._fail('invalid host extent or mapping permissions')
            if event.result:
                return True  # A failed map cannot create or replace a mapping.
            if any(r.iova < event.iova+event.size and event.iova < r.iova+r.size for r in self._regions):
                return self._fail('successful map overlaps observed mapping')
            if len(self._regions) >= self._capacity:
                return self._fail('mapping capacity')
            self._regions = tuple(sorted((*self._regions, Region(event.iova,event.size,event.hva,event.read,event.write)), key=lambda r:r.iova))
            return True
        # Failed unmap may have partial effects. Do not reconstruct guessed ranges.
        if event.result or not integer(event.returned_size):
            return self._fail('failed or unlocated unmap effects')
        end = event.iova+event.size
        overlaps = tuple(r for r in self._regions if r.iova < end and event.iova < r.iova+r.size)
        if self._backend == Backend.TYPE1V2:
            if any(r.iova < event.iova or r.iova+r.size > end for r in overlaps):
                return self._fail('v2 successful unmap bisects original map')
            removed = overlaps
        else:
            # Linux v6.8:1355-1377: V1 inside-first-map yields zero; otherwise
            # whole maps whose starts are in the request are removed, even past end.
            removed = () if overlaps and overlaps[0].iova < event.iova else overlaps
        if sum(r.size for r in removed) != event.returned_size:
            return self._fail('returned unmap size differs from observed original maps')
        self._regions = tuple(r for r in self._regions if r not in removed)
        return True

    def coverage(self, *, gpa, iova, size, read=True, write=True):
        if (self._error or not self._backend or not self._range(gpa,size)
                or not self._range(iova,size) or type(read) is not bool or type(write) is not bool
                or not (read or write)):
            return None
        end, cursor, used = iova+size, iova, []
        for region in self._regions:
            if region.iova+region.size <= cursor:
                continue
            if region.iova > cursor or (read and not region.read) or (write and not region.write):
                return None
            used.append(region)
            cursor = min(end,region.iova+region.size)
            if cursor == end:
                return Witness(self.identity,self._sequence,gpa,iova,size,read,write,tuple(used))
        return None

    def current(self, witness):
        # Recompute the witness. A caller-created object confers no authority.
        return (isinstance(witness, Witness) and witness.identity == self.identity
                and witness.cutoff == self._sequence
                and witness == self.coverage(gpa=witness.gpa,iova=witness.iova,
                    size=witness.size,read=witness.read,write=witness.write))
