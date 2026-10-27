#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Synthetic normalized histories only. No trace parser, VFIO ioctl or hardware."""
import dataclasses
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from dma_model import Backend, Identity, Ledger, Observation, Operation, LIMIT


class ModelTests(unittest.TestCase):
    def ledger(self,backend=Backend.TYPE1V2,**kwargs):
        ledger=Ledger(Identity('fixture',1,1),**kwargs)
        self.assertTrue(ledger.apply(Observation(ledger.identity,1,Operation.SETUP,backend=backend)))
        return ledger

    def event(self,ledger,operation,**kwargs):
        return Observation(ledger.identity,ledger.cutoff+1,operation,**kwargs)

    def map(self,ledger,iova=4096,size=4096,**kwargs):
        return ledger.apply(self.event(ledger,Operation.MAP,iova=iova,size=size,hva=kwargs.pop('hva',0x100000),read=True,write=kwargs.pop('write',True),**kwargs))

    def cover(self,ledger,base=4096,size=4096,**kwargs):
        return ledger.coverage(gpa=kwargs.pop('gpa',base),iova=base,size=size,**kwargs)

    def test_no_announcement_or_failed_map_coverage(self):
        ledger=self.ledger()
        self.assertTrue(ledger.apply(self.event(ledger,Operation.ANNOUNCE)))
        self.assertIsNone(self.cover(ledger))
        self.assertTrue(self.map(ledger,result=-1,errno=16))
        self.assertIsNone(self.cover(ledger))
        self.assertTrue(self.map(ledger))
        self.assertIsNotNone(self.cover(ledger))

    def test_domains_permissions_and_cutoff(self):
        ledger=self.ledger();self.assertTrue(self.map(ledger))
        witness=self.cover(ledger,gpa=0x200000)
        self.assertEqual((witness.gpa,witness.iova,witness.regions[0].hva),(0x200000,4096,0x100000))
        self.assertTrue(ledger.current(witness))
        self.assertFalse(hasattr(witness,'verified'))
        self.assertFalse(ledger.current(dataclasses.replace(witness,size=8192)))
        self.assertTrue(ledger.apply(self.event(ledger,Operation.ANNOUNCE)))
        self.assertFalse(ledger.current(witness))
        ledger=self.ledger();self.assertTrue(self.map(ledger,write=False))
        self.assertIsNone(self.cover(ledger));self.assertIsNotNone(self.cover(ledger,write=False))

    def test_split_records_and_holes(self):
        ledger=self.ledger()
        for base in (4096,8192,12288):self.assertTrue(self.map(ledger,base))
        self.assertIsNotNone(self.cover(ledger,size=12288))
        self.assertTrue(ledger.apply(self.event(ledger,Operation.UNMAP,iova=8192,size=4096,returned_size=4096)))
        self.assertIsNone(self.cover(ledger,size=12288))
        self.assertIsNotNone(self.cover(ledger));self.assertIsNotNone(self.cover(ledger,12288))
        # A large request may include holes. Returned size counts actual whole maps.
        self.assertTrue(ledger.apply(self.event(ledger,Operation.UNMAP,iova=4096,size=12288,returned_size=8192)))
        self.assertIsNone(self.cover(ledger))

    def test_v1_expands_and_zero_removal(self):
        ledger=self.ledger(Backend.TYPE1);self.assertTrue(self.map(ledger,size=8192))
        self.assertTrue(ledger.apply(self.event(ledger,Operation.UNMAP,iova=8192,size=4096,returned_size=0)))
        self.assertIsNotNone(self.cover(ledger,size=8192))
        self.assertTrue(ledger.apply(self.event(ledger,Operation.UNMAP,iova=4096,size=4096,returned_size=8192)))
        self.assertIsNone(self.cover(ledger))

    def test_v2_partial_and_wrong_return_are_uncertain(self):
        for size,returned in ((4096,4096),(8192,4096),(8192,0),(8192,12288)):
            ledger=self.ledger();self.assertTrue(self.map(ledger,size=8192))
            self.assertFalse(ledger.apply(self.event(ledger,Operation.UNMAP,iova=4096,size=size,returned_size=returned)))
            self.assertIsNone(self.cover(ledger));self.assertIsNotNone(ledger.error)

    def test_failed_unmap_and_ebusy_retry(self):
        ledger=self.ledger();self.assertTrue(self.map(ledger))
        self.assertTrue(self.map(ledger,result=-1,errno=16))
        self.assertIsNotNone(self.cover(ledger))
        self.assertTrue(ledger.apply(self.event(ledger,Operation.UNMAP,iova=4096,size=4096,returned_size=4096)))
        self.assertIsNone(self.cover(ledger));self.assertTrue(self.map(ledger,hva=0x200000))
        self.assertEqual(self.cover(ledger).regions[0].hva,0x200000)
        self.assertFalse(ledger.apply(self.event(ledger,Operation.UNMAP,iova=4096,size=4096,result=-1,errno=5)))
        self.assertIsNone(self.cover(ledger))

    def test_sequence_epoch_backend_and_incomplete(self):
        changes=[dict(sequence=3),dict(sequence=1),dict(identity=Identity('other',1,1)),
                 dict(identity=Identity('fixture',2,1)),dict(identity=Identity('fixture',1,2)),
                 dict(complete=False,result=None),dict(result=-1),dict(result=0,errno=5),dict(flags=1)]
        for change in changes:
            ledger=self.ledger();event=self.event(ledger,Operation.ANNOUNCE)
            self.assertFalse(ledger.apply(dataclasses.replace(event,**change)))
            self.assertFalse(self.map(ledger));self.assertIsNone(self.cover(ledger))
        ledger=Ledger(Identity('fixture',1,1))
        self.assertFalse(ledger.apply(Observation(ledger.identity,1,Operation.SETUP,backend='noiommu')))
        ledger=Ledger(Identity('fixture',1,1))
        self.assertFalse(self.map(ledger))

    def test_overlap_overflow_capacity(self):
        for change in (dict(iova=LIMIT-4096,size=8192),dict(hva=LIMIT-4096,size=8192),dict(iova=True),dict(size=0),dict(iova=1)):
            ledger=self.ledger();event=self.event(ledger,Operation.MAP,iova=4096,size=4096,hva=0x100000,read=True)
            self.assertFalse(ledger.apply(dataclasses.replace(event,**change)))
        ledger=self.ledger(capacity=1);self.assertTrue(self.map(ledger));self.assertFalse(self.map(ledger,8192))
        ledger=self.ledger();self.assertTrue(self.map(ledger));self.assertFalse(self.map(ledger))
        ledger=self.ledger(max_events=2);self.assertTrue(self.map(ledger));self.assertFalse(ledger.apply(self.event(ledger,Operation.ANNOUNCE)))
        ledger=self.ledger();self.assertTrue(self.map(ledger,LIMIT-4096));self.assertIsNotNone(self.cover(ledger,LIMIT-4096))

    def test_identity_and_constructor_validation(self):
        for identity in (Identity('',1,1),Identity('x',0,1),Identity('x',1,0),Identity('x',1,1,'0000:03:00.0'),Identity('x',1,1,'0000:82:00.0')):
            with self.assertRaises(ValueError):Ledger(identity)
        for kwargs in (dict(capacity=0),dict(page_size=3),dict(max_events=0)):
            with self.assertRaises(ValueError):Ledger(Identity('x',1,1),**kwargs)
        first=self.ledger();self.map(first);witness=self.cover(first)
        with self.assertRaises(AttributeError):first.identity=Identity('other',1,2)
        second=Ledger(Identity('fixture',1,2));self.assertFalse(second.current(witness))

    def test_seeded_page_oracle(self):
        # Independent page-set oracle for aligned V2 histories with one-page maps.
        rng=random.Random(40);ledger=self.ledger(max_events=4096);pages=set()
        for _ in range(500):
            page=rng.randrange(1,33)
            if page not in pages:
                self.assertTrue(self.map(ledger,page*4096));pages.add(page)
            else:
                low=page;high=min(33,page+rng.randrange(1,5));removed={p for p in pages if low<=p<high}
                self.assertTrue(ledger.apply(self.event(ledger,Operation.UNMAP,iova=low*4096,size=(high-low)*4096,returned_size=len(removed)*4096)))
                pages-=removed
            for start in (1,8,16,24):
                actual=self.cover(ledger,start*4096,3*4096) is not None
                self.assertEqual(actual,all(p in pages for p in range(start,start+3)))


if __name__=='__main__':unittest.main()
