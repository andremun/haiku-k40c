#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.haiku.d0_kernel_log import KernelLog
BASE=b'[ 1.000000] fixture kernel: DMAR: IOMMU enabled\n'
class KernelLogTests(unittest.TestCase):
 def test_append_and_new_fault(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'log';path.write_bytes(BASE)
   with KernelLog(path,reader=os.getpid()) as log:
    self.assertEqual(log.poll(),BASE)
    with path.open('ab') as out:out.write(b'[ 2.0] fixture kernel: vfio-pci: enabled\n')
    self.assertGreater(len(log.poll()),len(BASE))
    with path.open('ab') as out:out.write(b'[ 3.0] fixture kernel: DMAR: DMA fault\n')
    with self.assertRaises(RuntimeError):log.poll()
 def test_truncation_replacement_and_empty(self):
  for mode in ('truncate','replace','rewrite'):
   with tempfile.TemporaryDirectory() as d:
    path=Path(d)/'log';path.write_bytes(BASE)
    with KernelLog(path,reader=os.getpid()) as log:
     if mode=='replace':path.unlink();path.write_bytes(BASE)
     elif mode=='truncate':path.write_bytes(b'')
     else:path.write_bytes(BASE.replace(b'enabled',b'disabled'))
     with self.assertRaises(RuntimeError):log.poll()
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'log';path.write_bytes(b'-- No entries --\n')
   with self.assertRaises(ValueError):KernelLog(path,reader=os.getpid())
if __name__=='__main__':unittest.main()
