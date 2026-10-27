#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
import os
import signal
import subprocess
from unittest.mock import patch
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.haiku.d0_kernel_log import KernelLog, FILTER_PATTERN, find_filter
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
 def test_home_override_and_filtered_metadata(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'log';path.write_bytes(BASE)
   with patch.dict(os.environ,{'K40_KERNEL_LOG':str(path)}):
    with KernelLog(reader=os.getpid()) as log:
     self.assertEqual(log.path,path)
     self.assertIn('pcie bus error',log.metadata()['filter_pattern'])
     self.assertIn('filtered',log.metadata()['scope'])
 def test_pcie_card_root_port_and_unscoped_aer(self):
  for message in ('vfio-pci 0000:04:00.0: PCIe Bus Error: severity=Uncorrected',
                  'pcieport 0000:00:03.0: AER: Corrected error received',
                  'AER: multiple errors'):
   with tempfile.TemporaryDirectory() as d:
    path=Path(d)/'log';path.write_bytes(BASE)
    with KernelLog(path,reader=os.getpid()) as log:
     with path.open('a') as out:out.write('[ 3.0] fixture kernel: '+message+'\n')
     with self.assertRaisesRegex(RuntimeError,'PCIe'):log.poll()
 def test_filter_identity_and_immediate_exit(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)/'proc';root.mkdir();entry=root/'10';entry.mkdir();(entry/'fd').mkdir()
   path=Path(d)/'log';path.write_bytes(BASE)
   (entry/'fd/1').symlink_to(path)
   info=path.stat();identity=(info.st_dev,info.st_ino)
   (entry/'cmdline').write_bytes(b'grep\0--line-buffered\0-iE\0'+FILTER_PATTERN.encode()+b'\0')
   self.assertEqual(find_filter(identity,root),10)
   (entry/'cmdline').write_bytes(b'grep\0--line-buffered\0-iE\0vfio\0')
   with self.assertRaises(ValueError):find_filter(identity,root)
   process=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'])
   try:
    with KernelLog(path,reader=os.getpid()) as log:
     log.filter_fd=os.pidfd_open(process.pid)
     process.terminate();process.wait(timeout=3)
     with self.assertRaisesRegex(RuntimeError,'filter exited'):log.poll()
   finally:
    if process.poll() is None:process.kill();process.wait()
 def test_reader_sigpipe_after_filter_exit(self):
  # Harmless owned child emulates journalctl's default SIGPIPE behavior.
  code='import os,signal; signal.signal(signal.SIGPIPE,signal.SIG_DFL); os.write(1,b"ready\\n"); os.read(0,1); os.write(1,b"next\\n")'
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'log';path.write_bytes(BASE)
   process=subprocess.Popen([sys.executable,'-c',code],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
   try:
    self.assertEqual(process.stdout.readline(),b'ready\n')
    with KernelLog(path,reader=process.pid) as log:
     process.stdout.close();process.stdin.write(b'x');process.stdin.flush()
     self.assertEqual(process.wait(timeout=3),-signal.SIGPIPE)
     with self.assertRaisesRegex(RuntimeError,'reader exited'):log.poll()
   finally:
    if process.poll() is None:process.kill();process.wait()
    process.stdin.close();process.stdout.close()
if __name__=='__main__':unittest.main()
