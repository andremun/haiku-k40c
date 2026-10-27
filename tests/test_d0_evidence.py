#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.haiku.d0_evidence import native_extent
LOG='''k40_d0: phase=1 lease=1 token=1 gpa=0x100000 bytes=4096 quarantine=0 visibility=DENIED
k40_d0: phase=1 detached lease=1 token=1 retained
k40_d0: phase=2 lease=2 token=1 gpa=0x100000 bytes=4096 quarantine=1 visibility=DENIED
k40_d0: phase=2 detached lease=2 token=1 retained
k40_d0: PASS retained host extent only; DMA denied
'''
class EvidenceTests(unittest.TestCase):
 def test_retained_extent(self):
  result=native_extent(LOG);self.assertEqual((result.gpa,result.size,result.token,result.lease),(0x100000,4096,1,2))
 def test_incomplete_not_success(self):
  self.assertIsNone(native_extent(LOG.rsplit('k40_d0: PASS',1)[0]));self.assertIsNone(native_extent(''))
 def test_bad_lifecycle(self):
  for before,after in [('lease=2','lease=1'),('quarantine=1','quarantine=0'),('gpa=0x100000 bytes=4096 quarantine=1','gpa=0x101000 bytes=4096 quarantine=1'),('bytes=4096','bytes=8192'),('gpa=0x100000','gpa=0x100001'),('token=1 retained','token=2 retained')]:
   with self.assertRaises(RuntimeError):native_extent(LOG.replace(before,after))
 def test_failure_and_real_panic(self):
  for prefix in ('k40_os: FAIL D0 prepare\n','PANIC: bad state\n'):
   with self.assertRaises(RuntimeError):native_extent(prefix+LOG)
  self.assertIsNotNone(native_extent('Kernel Debugger: type panic to crash\n'+LOG))
if __name__=='__main__':unittest.main()
