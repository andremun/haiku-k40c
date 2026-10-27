#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""D0 orchestration fixtures. Success records below are synthetic, never VFIO evidence."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.haiku import d0_run as run
from tools.haiku.d0_stage import elf
from test_d0_evidence import LOG
from test_observer_binding import LINES
ROOT=Path(__file__).resolve().parents[1]
TOPO=ROOT/'results/20261027-d0-topology-fixture'
SERIAL='''K40-B5-BEGIN
k40_stage: B5_IDENTITY_READ_ONLY
k40_os: PCI command 0x0007
k40_os: GPU identity 0x0f1240a1; no bring-up or DMA
k40_os: PASS B5 identity reads only
k40_stage: D0_MEMORY_NO_DEVICE
'''+LOG+'K40-B5-END\n'

class D0Tests(unittest.TestCase):
 def test_fixed_command_and_no_other_card(self):
  args=run.arguments(Path('/folder'),Path('/evidence'))
  self.assertEqual([a for a in args if a.startswith('vfio-pci,')],['vfio-pci,host=0000:04:00.0'])
  self.assertIn('-qmp',args);self.assertFalse(any('03:00.0' in a or '82:00.0' in a for a in args))
 def test_exchange_hash_write_once_and_release(self):
  with tempfile.TemporaryDirectory() as d:
   folder=Path(d)/'folder';folder.mkdir();evidence=Path(d)/'evidence';evidence.mkdir()
   for name in ('identity','owner','memory'):(folder/name).write_bytes(name.encode())
   kernel=b'fixture kernel';suite={'kernel_sha256':hashlib.sha256(kernel).hexdigest()}
   with run.exchange(folder,evidence,suite) as (port,release):
    root=f'http://127.0.0.1:{port}'
    def request(name,data=None):
     obj=urllib.request.Request(root+'/'+name,data=data,method='GET' if data is None else 'PUT')
     try:
      with urllib.request.urlopen(obj,timeout=3) as response:return response.status,response.read()
     except urllib.error.HTTPError as error:
      with error:return error.code,error.read()
    self.assertEqual(request('memory'),(200,b'memory'));self.assertEqual(request('../outside')[0],404)
    self.assertEqual(request('release')[0],404);release.set();self.assertEqual(request('release')[0],200)
    self.assertEqual(request('kernel_x86_64',b'wrong')[0],409)
    self.assertEqual(request('kernel_x86_64',kernel)[0],201);self.assertFalse((evidence/'kernel_x86_64').exists())
    self.assertEqual(request('ready.txt',b'ready\n')[0],201);self.assertEqual(request('ready.txt',b'wrong')[0],409)
    self.assertEqual((evidence/'ready.txt').read_bytes(),b'ready\n');self.assertEqual(request('job.exit',b'x'*17)[0],413)
 def test_cutoff_requires_binding_identity_and_retained_extent(self):
  for problem in (None,'binding','identity','role','kernel','guestfail','lateclose','partial'):
   with tempfile.TemporaryDirectory() as d:
    folder=Path(d)/'fixture';folder.mkdir();evidence=Path(d)/'evidence';evidence.mkdir()
    trace=Path(d)/'trace'
    records=[line.replace('iova=0x1000','iova=0x100000') for line in LINES]
    if problem=='binding':records[-1]=records[-1].replace('04:00.0','03:00.0')
    trace.write_text(''.join('100 '+line+'\n' for line in records))
    serial=SERIAL.replace('0x0f1240a1','0xdeadbeef') if problem=='identity' else SERIAL
    if problem=='role':serial+='k40_stage: UNREVIEWED_WRITE\n'
    (evidence/'serial.log').write_text(serial);(evidence/'ready.txt').write_bytes(b'ready\n')
    if problem!='kernel':(evidence/'kernel.sha256').write_text('fixture hash\n')
    if problem=='guestfail':(evidence/'job.exit').write_text('1\n')
    class Process:pid=100
    class Child:
     process=Process()
     def check(self):pass
    child=Child();child.trace=trace
    class Kernel:
     def poll(self):return b'kernel fixture'
    class Release:
     called=False
     def set(self):self.called=True;(evidence/'job.exit').write_text('0\n')
    release=Release()
    topology={name:(TOPO/(name+'.txt')).read_text() for name in ('qtree','mtree','ramblock')}
    topology['qtree']+='\n  dev: vfio-pci, id "test"\n    host = "0000:04:00.0"\n'
    def snapshot(_):
     if problem=='lateclose':
      with trace.open('a') as out:out.write('100 close(9) = 0\n')
     if problem=='partial':
      with trace.open('a') as out:out.write('100 ioctl(')
     return topology
    with patch.object(run,'snapshot',side_effect=snapshot):
     if problem:
      with self.assertRaises(RuntimeError):run.monitor(child,folder,evidence,1,release,{'group':'23'},Kernel())
      self.assertFalse(release.called)
     else:
      run.monitor(child,folder,evidence,1,release,{'group':'23'},Kernel())
      self.assertTrue(release.called);self.assertFalse(json.loads((evidence/'cutoff.json').read_text())['publication'])
 def test_final_trace_rejects_partial_or_rewritten_output(self):
  class Stream:
   error='fixture rejection'
   def feed(self,line):return line=='100 close(17) = 0\n'
  with tempfile.TemporaryDirectory() as d:
   trace=Path(d)/'trace';prefix=b'prefix\n'
   trace.write_bytes(prefix+b'100 close(17) = 0\n')
   run.finish_trace(trace,Stream(),prefix,b'')
   for tail in (b'100 close(',b'100 unknown() = 0\n'):
    trace.write_bytes(prefix+tail)
    with self.assertRaises(RuntimeError):run.finish_trace(trace,Stream(),prefix,b'')
   trace.write_bytes(b'rewritten\n')
   with self.assertRaises(RuntimeError):run.finish_trace(trace,Stream(),prefix,b'')
 def test_wrong_role_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'driver';path.write_bytes(b'X'*4096)
   with self.assertRaises(ValueError):elf(path,b'D0_MEMORY_NO_DEVICE')

if __name__=='__main__':unittest.main()
