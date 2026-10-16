#!/usr/bin/env python3
# Copyright 2026 Mario Andrés Muñoz.
# Distributed under the terms of the MIT License.
"""Package committed HEAD only; no caches, ROM or decoded firmware outputs.

Creates a local ZIP and Git bundle under ignored build/review/. It never pushes
or opens source implementations. --check compares hashes/revision, writes nothing.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'build/review'

def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args],text=True).strip()
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if git('status','--porcelain'):raise ValueError('commit the reviewed work before packaging')
    commit=git('rev-parse','HEAD');manifest=OUT/'manifest.json'
    if args.check:
        record=json.loads(manifest.read_text())
        if record['commit']!=commit:raise ValueError('bundle is for another commit')
        for name,expected in record['sha256'].items():
            if digest(OUT/name)!=expected:raise ValueError('bundle hash mismatch: '+name)
        print('Review artifacts match committed HEAD and hashes');return 0
    tracked=git('ls-tree','-r','--name-only','HEAD').splitlines()
    if any(name.lower().endswith('.rom') for name in tracked):raise ValueError('refuse to package tracked ROM image')
    OUT.mkdir(parents=True,exist_ok=True)
    archive=OUT/'haiku-k40c-cardless.zip';bundle=OUT/'haiku-k40c-cardless.bundle'
    subprocess.run(['git','-C',str(ROOT),'archive','--format=zip','HEAD','-o',str(archive)],check=True)
    subprocess.run(['git','-C',str(ROOT),'bundle','create',str(bundle),'HEAD'],check=True)
    record=dict(commit=commit,sha256={p.name:digest(p) for p in (archive,bundle)},scope='committed source/captures only; no caches or external firmware',instructions='docs/ABC-CARDLESS-OUTCOME.md',external_inputs=['five pinned source caches','verified offline ROM and decoded listing','matching Haiku kernel/guest for native load'])
    manifest.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    print(manifest);return 0
if __name__=='__main__':raise SystemExit(main())
