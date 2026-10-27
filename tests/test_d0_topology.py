#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Archived cardless monitor fixtures and deliberately modified strings only."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.haiku.d0_topology import parse
ROOT=Path(__file__).resolve().parents[1]/'results/20261027-d0-topology-fixture'
Q,M,R=[(ROOT/(name+'.txt')).read_text() for name in ('qtree','mtree','ramblock')]

class TopologyTests(unittest.TestCase):
 def test_actual_cardless_ram(self):
  value=parse(Q,M,R,physical=False)
  self.assertEqual(value.ram_bytes,4*1024**3)
  self.assertTrue(value.contains(0x100000,4096));self.assertFalse(value.contains(0x80000000,4096))
  self.assertFalse(value.contains(0xa0000,4096));self.assertTrue(value.contains(0x100000000,4096))
 def test_synthetic_assignment_is_separate(self):
  physical=Q+'\n  dev: vfio-pci, id "test"\n    host = "0000:04:00.0"\n'
  self.assertTrue(parse(physical,M,R,physical=True).physical)
  with self.assertRaises(ValueError):parse(Q,M,R,physical=True)
  for card in ('0000:03:00.0','0000:82:00.0'):
   with self.assertRaises(ValueError):parse(physical.replace('0000:04:00.0',card),M,R,physical=True)
 def test_iommu_duplicate_and_bad_alias(self):
  for q,m,r in ((Q+'\n  dev: intel-iommu, id "x"\n',M,R),
                (Q,M+M,R),(Q,M.replace('pc.ram @0000000080000000','pc.ram @fffffffffffff000'),R),
                (Q,M,R.replace('0x0000000100000000','0x0000000200000000'))):
   with self.assertRaises(ValueError):parse(q,m,r,physical=False)
 def test_internal_offset_is_not_host_pointer(self):
  changed=R.replace('0x0000000000000000','0x0000000040000000')
  value=parse(Q,M,changed,physical=False)
  self.assertEqual(value.ramblock_offset,0x40000000);self.assertTrue(value.contains(0x100000,4096))

if __name__=='__main__':unittest.main()
