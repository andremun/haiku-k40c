#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Synthetic decoder-format binding histories. No syscall or device access."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.observer.binding import BoundStream

PREFIX='100 '
LINES=[
 'openat(-100</work>, "/dev/vfio/23", 0x80002) = 4</dev/vfio/23>',
 'ioctl(4</dev/vfio/23>, 0x3b67, K40_STATUS{argsz=8, flags=0x1}) = 0',
 'openat(-100</work>, "/dev/vfio/vfio", 0x80002) = 5</dev/vfio/vfio>',
 'ioctl(5</dev/vfio/vfio>, 0x3b64, 0) = 0',
 'ioctl(4</dev/vfio/23>, 0x3b68, K40_ATTACH{5}) = 0',
 'ioctl(5</dev/vfio/vfio>, 0x3b66, K40_SETUP{3}) = 0',
 'ioctl(5</dev/vfio/vfio>, 0x3b71, K40_MAP{argsz=32, flags=0x3, hva=0x100000, iova=0x1000, size=0x2000}) = 0',
 'ioctl(4</dev/vfio/23>, 0x3b6a, K40_DEVICE{"0000:04:00.0"}) = 9',
]
class BindingTests(unittest.TestCase):
 def load(self,lines=LINES):
  stream=BoundStream('synthetic',100,23)
  for text in lines:self.assertTrue(stream.feed(PREFIX+text+'\n'),stream.error)
  return stream
 def query(self,stream):return stream.coverage(gpa=0x1000,iova=0x1000,size=0x1000)
 def test_full_association_and_anonymous_close(self):
  stream=self.load();witness=self.query(stream);self.assertIsNotNone(witness);self.assertTrue(stream.current(witness))
  self.assertTrue(stream.feed('100 close(9<anon_inode:[vfio-device]>) = 0\n'));self.assertFalse(stream.current(witness));self.assertIsNone(self.query(stream))
 def test_incomplete_binding_not_coverage(self):
  stream=self.load(LINES[:-1]);self.assertIsNone(self.query(stream))
 def test_wrong_device_fd_or_group(self):
  for old,new in [('0000:04:00.0','0000:03:00.0'),('0000:04:00.0','0000:82:00.0'),('K40_ATTACH{5}','K40_ATTACH{8}'),('/dev/vfio/23','/dev/vfio/24'),('flags=0x1','flags=0')]:
   stream=BoundStream('synthetic',100,23);outcomes=[stream.feed(PREFIX+text.replace(old,new)+'\n') for text in LINES]
   self.assertFalse(all(outcomes));self.assertIsNone(self.query(stream))
 def test_other_thread_related_close_fails(self):
  stream=self.load();self.assertFalse(stream.feed('101 close(9<anon_inode:[vfio-device]>) = 0\n'));self.assertIsNone(self.query(stream))
 def test_unrelated_close_and_detach(self):
  stream=self.load();witness=self.query(stream)
  self.assertTrue(stream.feed('101 close(44<anon_inode:[eventfd]>) = 0\n'));self.assertTrue(stream.current(witness))
  self.assertTrue(stream.feed('100 ioctl(4</dev/vfio/23>, 0x3b69, K40_DETACH{}) = 0\n'));self.assertIsNone(self.query(stream))
 def test_group_close_reuse_and_failure(self):
  stream=self.load();self.assertTrue(stream.feed('100 close(4</dev/vfio/23>) = 0\n'));self.assertIsNone(self.query(stream))
  self.assertFalse(stream.feed(PREFIX+LINES[0]+'\n'));self.assertIsNone(self.query(stream))
  stream=self.load();self.assertFalse(stream.feed('100 close(9<anon_inode:[vfio-device]>) = -1 EINTR (Interrupted system call)\n'))

if __name__=='__main__':unittest.main()
