#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Offline checks for owner staging and complete native reload evidence."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('owner_runner',ROOT/'tools/haiku/cardless_run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
GOOD = '''k40_owner_test: host-bytes-cleanup PASS; publication DENIED
k40_owner_test: phase1 init lease=1 token=2
k40_owner_test: phase1 uninit lease=1 token=2 retained
k40_owner_test: phase2 init lease=2 token=2 state=3 owned=1 quarantine=1
k40_owner_test: phase2 uninit lease=2 token=2 retained
k40_os: PASS native owner reload only; DMA denied
K40-CARDLESS-END
'''


class OwnerRunnerTests(unittest.TestCase):
    def test_complete_lifetime(self):
        self.assertTrue(runner.owner_complete(GOOD))
        extra = GOOD.replace('K40-CARDLESS-END\n','') + GOOD[GOOD.index('k40_owner_test: phase2'):].replace('lease=2','lease=3')
        self.assertTrue(runner.owner_complete(extra))
        self.assertFalse(runner.owner_complete('Welcome to kernel debugger output!\n'))

    def test_incomplete_and_changed_state(self):
        mutations = [
            ('phase1 uninit lease=1 token=2 retained\n',''),
            ('phase2 uninit lease=2 token=2 retained\n',''),
            ('phase2','phase1'), ('lease=2','lease=1'),
            ('phase2 init lease=2 token=2','phase2 init lease=2 token=3'),
            ('state=3','state=0'), ('quarantine=1','quarantine=0'),
            ('host-bytes-cleanup PASS','host-bytes-cleanup MISSING'),
            ('k40_os: PASS native owner reload only; DMA denied','k40_os: PASS other probe'),
        ]
        for old,new in mutations:
            with self.subTest(old=old),self.assertRaises(RuntimeError):
                runner.owner_complete(GOOD.replace(old,new))
        with self.assertRaises(RuntimeError):
            runner.owner_complete('k40_os: FAIL first load\n'+GOOD)
        with self.assertRaises(RuntimeError):
            runner.owner_complete(GOOD+'k40_owner_test: phase3 malformed\n')

    def test_fixed_user_staging(self):
        job = runner.guest_commands(1234,True,True)
        self.assertIn('finddir B_USER_NONPACKAGED_ADDONS_DIRECTORY',job)
        self.assertIn('"$addons/kernel/generic/k40c_owner"',job)
        self.assertLess(job.index('"$host/owner_module"'),job.index('"$host/probe"'))
        self.assertEqual(job.count('ls /dev/misc'),4)
        self.assertIn("' EXIT",job)
        self.assertNotIn('/boot/system/non-packaged',job)
        for text in ('sudo','vfio','-device','rescan','reset'):
            self.assertNotIn(text,job)
        plain = runner.guest_commands(1234,True)
        self.assertIn('/boot/system/non-packaged',plain)
        self.assertEqual(plain.count('ls /dev/misc'),1)
        self.assertNotIn('owner_module',plain)
        self.assertNotIn('probe',runner.guest_commands(1234,False))

    def test_pair_validation_before_launch(self):
        with tempfile.TemporaryDirectory() as name:
            folder = Path(name)
            client, owner = folder/'client',folder/'owner'
            client.write_bytes(b'\x7fELF CARDLESS_OWNER_ONLY')
            owner.write_bytes(b'\x7fELF generic/k40c_owner/v1')
            with patch.object(runner.subprocess,'check_output',return_value='12: 4300 16 OBJECT GLOBAL DEFAULT 17 modules\n'):
                runner.validate_owner_pair(client,owner)
            for symbols in ('12: 4300 16 OBJECT GLOBAL DEFAULT UND modules\n','no module table'):
                with patch.object(runner.subprocess,'check_output',return_value=symbols),self.assertRaises(ValueError):
                    runner.validate_owner_pair(client,owner)
            with self.assertRaises(ValueError):
                runner.validate_owner_pair(None,owner)
            with self.assertRaises(ValueError):
                runner.validate_owner_pair(owner,client)


if __name__ == '__main__':
    unittest.main()
