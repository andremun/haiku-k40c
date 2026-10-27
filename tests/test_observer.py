#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Source-format fixtures. Replaced return values below are synthetic, not VFIO evidence."""
from pathlib import Path
import re
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.observer.normalize import Stream, payload, MAP, UNMAP, InvalidTrace

ROOT=Path(__file__).resolve().parents[1]
# Original captured /dev/null errors remain immutable inputs. Success tests change
# only strings in memory; no ioctl, observer process or VFIO path is opened here.
RAW=(ROOT/'work/S1D0OBSERVER/null-trace.log').read_text().splitlines(keepends=True)


def fixture():
    return [re.sub(r'^\d+','100',re.sub(r'-1 ENOTTY \(Inappropriate ioctl for device\)','0',line))
            .replace('returned=error','returned=0x2000') for line in RAW]


class ObserverTests(unittest.TestCase):
    def admitted(self):
        stream=Stream('unit',fixture=True)
        for line in fixture()[:3]:self.assertTrue(stream.feed(line),stream.error)
        return stream

    def query(self,stream):return stream.coverage(3,gpa=0x500000,iova=0x1000,size=0x2000)

    def test_actual_error_stream_cannot_cover(self):
        stream=Stream('actual-null',fixture=True)
        self.assertTrue(stream.feed(RAW[0]));self.assertFalse(stream.feed(RAW[1]))
        self.assertIsNone(self.query(stream))
        production=Stream('production')
        self.assertFalse(production.feed(RAW[0]));self.assertIsNone(self.query(production))

    def test_original_decoder_payload_fields(self):
        mapping=re.search(r'K40_MAP\{[^}]+\}',RAW[2])[0]
        self.assertEqual(payload(MAP,mapping,-1),dict(hva=0x100000,iova=0x1000,size=0x2000,read=True,write=True))
        unmap=re.search(r'K40_UNMAP\{[^}]+\}',RAW[3])[0]
        self.assertEqual(payload(UNMAP,unmap,-1)['size'],0x2000)
        with self.assertRaises(InvalidTrace):payload(UNMAP,unmap,0)

    def test_synthetic_success_and_removal(self):
        stream=self.admitted();witness=self.query(stream)
        self.assertIsNotNone(witness);self.assertTrue(stream.current(3,witness))
        self.assertEqual(witness.gpa,0x500000)
        self.assertTrue(stream.feed(fixture()[3]));self.assertIsNone(self.query(stream))
        self.assertFalse(stream.current(3,witness));self.assertTrue(stream.feed(fixture()[4]))

    def test_close_reuse_cannot_inherit(self):
        stream=self.admitted();old=self.query(stream)
        self.assertTrue(stream.feed(fixture()[4]));self.assertFalse(stream.current(3,old))
        self.assertTrue(stream.feed(fixture()[0]));self.assertIsNone(self.query(stream))
        self.assertFalse(stream.current(3,old))
        self.assertTrue(stream.feed(fixture()[1]));self.assertTrue(stream.feed(fixture()[2]))
        self.assertNotEqual(self.query(stream).identity,old.identity)

    def test_invalid_framing_completion_process_and_injection(self):
        changes=[lambda x:x.rstrip('\n'),lambda x:x+'extra\n',lambda x:x.replace('100 ','101 ',1),
                 lambda x:x.replace(' = 0',' = 0 (INJECTED)'),lambda x:x.replace(' = 0',' <unfinished ...>'),
                 lambda x:x.replace(' = 0',' = ? ERESTARTSYS (To be restarted)'),
                 lambda x:x.replace('0x2000','unreadable'),lambda x:x.replace('3</dev/null>','4</dev/null>')]
        for change in changes:
            stream=Stream('unit',fixture=True)
            for line in fixture()[:2]:self.assertTrue(stream.feed(line))
            self.assertFalse(stream.feed(change(fixture()[2])))
            self.assertFalse(stream.feed(fixture()[2]));self.assertIsNone(self.query(stream))

    def test_unknown_layout_backend_permissions_and_request(self):
        for source,old,new in ((1,'K40_SETUP{3}','K40_SETUP{6}'),(2,'argsz=32','argsz=40'),
                (2,'flags=0x3','flags=0x4'),(2,'0x3b71','0x3b79'),(2,'K40_MAP{','{')):
            stream=Stream('unit',fixture=True)
            for line in fixture()[:source]:self.assertTrue(stream.feed(line))
            self.assertFalse(stream.feed(fixture()[source].replace(old,new)))
            self.assertIsNone(self.query(stream))

    def test_unmap_return_size_not_request(self):
        stream=self.admitted()
        self.assertFalse(stream.feed(fixture()[3].replace('returned=0x2000','returned=0x1000')))
        self.assertIsNone(self.query(stream))

    def test_duplication_capacity_and_metadata_cutoff(self):
        stream=self.admitted();old=self.query(stream)
        self.assertTrue(stream.feed('100 ioctl(3</dev/null>, 0x3b65, 0x3) = 1\n'))
        self.assertFalse(stream.current(3,old));self.assertIsNotNone(self.query(stream))
        self.assertFalse(stream.feed('100 dup(3</dev/null>) = 4</dev/null>\n'))
        stream=Stream('unit',fixture=True,max_lines=2)
        self.assertTrue(stream.feed(fixture()[0]));self.assertTrue(stream.feed(fixture()[1]))
        self.assertFalse(stream.feed(fixture()[2]))
        stream=Stream('unit',fixture=True,max_bytes=8);self.assertFalse(stream.feed(fixture()[0]))


if __name__=='__main__':unittest.main()
