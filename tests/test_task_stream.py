#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Synthetic successful maps plus real inert task-proof captures. No GPU access."""
from pathlib import Path
import subprocess
import tempfile
import re
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.observer.task_stream import TaskStream
from tools.observer.supervise import observed_child
from test_observer_binding import LINES
ROOT=Path(__file__).resolve().parents[1]


def tag(text,group=100,files=0):
    marker=f'K40_TASK{{tgid={group}, files={files}}} '
    if text.startswith('close('):return text.replace('close(','close('+marker,1)
    return re.sub(r'(ioctl\([^,]+, 0x[0-9a-f]+, )',lambda m:m[0]+marker,text,count=1)


class TaskTests(unittest.TestCase):
    def load(self):
        stream=TaskStream('synthetic',100,23,target='/qemu')
        self.assertTrue(stream.feed('100 execve("/qemu", [], 0) = 0\n'))
        for line in LINES:self.assertTrue(stream.feed('100 '+line+'\n'),stream.error)
        return stream

    def test_shared_thread_map_and_close(self):
        stream=self.load()
        call=LINES[6].replace('iova=0x1000','iova=0x8000')
        self.assertTrue(stream.feed('101 '+tag(call)+'\n'),stream.error)
        witness=stream.coverage(gpa=0x8000,iova=0x8000,size=0x1000)
        self.assertIsNotNone(witness);self.assertTrue(stream.current(witness))
        self.assertTrue(stream.feed('101 '+tag('close(9<anon_inode:[vfio-device]>) = 0')+'\n'))
        self.assertIsNone(stream.coverage(gpa=0x8000,iova=0x8000,size=0x1000))

    def test_private_table_wrong_group_missing_and_opaque(self):
        call=LINES[6].replace('iova=0x1000','iova=0x8000')
        for text in (call,tag(call,files=1),tag(call,files=-1),tag(call,group=101),
                     tag(call).replace('files=0','files=unreadable'),tag(call)+' K40_TASK{tgid=100, files=0} '):
            stream=self.load()
            self.assertFalse(stream.feed('101 '+text+'\n'))
            self.assertIsNone(stream.coverage(gpa=0x1000,iova=0x1000,size=0x1000))

    def test_namespace_changes_and_exec_fail_closed(self):
        for text in ('unshare(0x400) = 0','close_range(0, 99, 0x2) = 0',
                     'execve("/qemu", [], 0) = 0','execveat(3, "", [], 0, 0) = 0'):
            stream=self.load();self.assertFalse(stream.feed('100 '+text+'\n'))
        stream=TaskStream('synthetic',100,23,target='/qemu')
        self.assertFalse(stream.feed('100 execve("/other", [], 0) = 0\n'))
        stream=TaskStream('synthetic',100,23,target='/qemu')
        for line in LINES:self.assertTrue(stream.feed('100 '+line+'\n'))
        self.assertIsNone(stream.coverage(gpa=0x1000,iova=0x1000,size=0x1000))

    def test_real_owned_captures(self):
        records=[]
        for mode in ('thread','fork','private'):
            data=(ROOT/f'work/S1D0THREAD/owned-{mode}-02.log').read_text()
            parent=int(re.search(r'^(\d+) execve',data)[1])
            proof=re.search(r'^(\d+) ioctl\([^\n]*K40_TASK\{tgid=(\d+), files=(-?\d+)\}',data,re.M)
            self.assertIsNotNone(proof);tid,group,files=map(int,proof.groups())
            self.assertNotEqual(tid,parent)
            self.assertIn('ENOTTY',data)  # Inert /dev/null, never a successful VFIO call.
            if mode=='thread':self.assertEqual((group,files),(parent,0))
            elif mode=='fork':self.assertNotEqual(group,parent)
            else:self.assertEqual(group,parent);self.assertNotEqual(files,0)
            records.append((mode,parent,tid,group,files))
        self.assertEqual(len(records),3)

    @unittest.skipUnless((ROOT/'build/observer/strace-source/src/strace').is_file(),'pinned observer not built')
    def test_current_observer_owned_thread_private_fork_and_guards(self):
        observer=ROOT/'build/observer/strace-source/src/strace'
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);fixture=folder/'fixture'
            subprocess.run(['cc','-Wall','-Wextra','-Werror','-pthread',str(ROOT/'tests/observer_tasks.c'),'-o',str(fixture)],check=True)
            for mode in ('thread','private','fork','guard'):
                trace=folder/(mode+'.log')
                with (folder/(mode+'.out')).open('wb') as log:
                    with observed_child(observer,[str(fixture),mode],trace,log,10,folder/(mode+'.watch'),['/dev/null']) as child:
                        parent=child.process.pid
                        self.assertEqual(child.process.wait(timeout=5),0)
                data=trace.read_text()
                proof=re.search(r'^(\d+) ioctl\([^\n]*K40_TASK\{tgid=(\d+), files=(-?\d+)\}',data,re.M)
                self.assertIsNotNone(proof,data)
                tid,group,files=map(int,proof.groups())
                if mode=='thread':self.assertEqual((group,files),(parent,0));self.assertNotEqual(tid,parent)
                elif mode=='private':self.assertEqual(group,parent);self.assertNotEqual(files,0)
                elif mode=='fork':self.assertNotEqual(group,parent)
                else:
                    self.assertIn('unshare(',data);self.assertIn('close_range(',data)
                    stream=TaskStream('synthetic',parent,23,target=str(fixture))
                    self.assertTrue(stream.feed(data.splitlines(keepends=True)[0]))
                    guard=next(line for line in data.splitlines(keepends=True) if 'unshare(' in line)
                    self.assertFalse(stream.feed(guard))
                self.assertIn('ENOTTY',data)

if __name__=='__main__':unittest.main()
