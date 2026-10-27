#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Bounded Unix-socket monitor fixtures. No QEMU or device."""
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.haiku.d0_monitor import snapshot
from tools.haiku.d0_topology_fixture import arguments

class MonitorTests(unittest.TestCase):
 def exchange(self,problem=None):
  with tempfile.TemporaryDirectory() as d,socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as server:
   path=Path(d)/'qmp';server.bind(str(path));server.listen()
   errors=[]
   def serve():
    try:
     connection,_=server.accept()
     with connection:
      connection.sendall(b'{"QMP":{}}\r\n');stream=connection.makefile('rb')
      for index in range(1,6):
       line=stream.readline()
       if not line:break
       request=json.loads(line)
       if index==1:self.assertEqual(request['execute'],'qmp_capabilities');reply={}
       elif index==2:reply={'status':'running','running':True}
       else:
        self.assertEqual(request['execute'],'human-monitor-command');self.assertIn(request['arguments']['command-line'],('info qtree','info mtree -f','info ramblock'))
        reply='captured topology'
       if problem=='paused' and index==2:reply={'status':'paused','running':False}
       message={'id':request['id'],'return':reply}
       if problem=='id' and index==1:message['id']=99
       if problem=='error' and index==1:message={'id':1,'error':{}}
       if problem=='empty' and index==3:message['return']=''
       connection.sendall((json.dumps(message)+'\r\n').encode())
      stream.close()
    except (BrokenPipeError,ConnectionResetError):pass
    except BaseException as error:errors.append(error)
   thread=threading.Thread(target=serve);thread.start()
   try:return snapshot(path)
   finally:thread.join(timeout=3);server.close();self.assertFalse(thread.is_alive());self.assertFalse(errors)
 def test_complete_snapshot(self):self.assertEqual(set(self.exchange()),{'mtree','qtree','ramblock'})
 def test_reject_bad_id_error_status_or_empty(self):
  for problem in ('id','error','paused','empty'):
   with self.assertRaises(RuntimeError):self.exchange(problem)
 def test_fixture_command_is_cardless(self):
  args=arguments(Path('/fixture'),Path('/evidence'))
  self.assertFalse(any('vfio' in value.lower() for value in args));self.assertNotIn('-device vfio-pci',' '.join(args))
  self.assertIn('-qmp',args);self.assertIn('q35',args)

if __name__=='__main__':unittest.main()
