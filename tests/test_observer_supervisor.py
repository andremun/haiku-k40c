#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Owned Python sleep children only. No guest, device or VFIO call."""
from pathlib import Path
import os
import signal
import sys
import tempfile
import time
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.observer.supervise import observed_child
OBSERVER=Path(__file__).resolve().parents[1]/'build/observer/strace-source/src/strace'

@unittest.skipUnless(OBSERVER.exists(),'pinned observer build not available')
class SupervisorTests(unittest.TestCase):
    def test_direct_child_and_normal_cleanup(self):
        with tempfile.TemporaryDirectory() as d,open(os.devnull,'wb') as log:
            root=Path(d)
            with observed_child(OBSERVER,[sys.executable,'-c','import time; time.sleep(20)'],root/'trace',log,10,root/'watch',[]) as child:
                self.assertNotEqual(child.process.pid,child.tracer)
                child.check();process=child.process
            self.assertIsNotNone(process.poll());self.assertFalse((root/'watch').exists())

    def test_observer_death_fails_and_target_is_stopped(self):
        with tempfile.TemporaryDirectory() as d,open(os.devnull,'wb') as log:
            root=Path(d)
            with self.assertRaisesRegex(RuntimeError,'observer'):
                with observed_child(OBSERVER,[sys.executable,'-c','import time; time.sleep(20)'],root/'trace',log,10,root/'watch',[]) as child:
                    process=child.process;signal.pidfd_send_signal(child.tracer_fd,signal.SIGKILL)
                    for _ in range(100):
                        time.sleep(0.01);child.check()
                    self.fail('tracer loss undetected')
            self.assertIsNotNone(process.poll())

    def test_independent_deadline_targets_tracee(self):
        with tempfile.TemporaryDirectory() as d,open(os.devnull,'wb') as log:
            root=Path(d)
            with observed_child(OBSERVER,[sys.executable,'-c','import time; time.sleep(20)'],root/'trace',log,1,root/'watch',[]) as child:
                process=child.process
                process.wait(timeout=4)
                self.assertEqual(process.returncode,-signal.SIGKILL)
            self.assertTrue((root/'watch').exists())

if __name__=='__main__':unittest.main()
