#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Generate DMA source/evidence metadata. Never grants mapping/publication permission.

--check compares exact text without writing. --verify-external additionally checks
all downloaded sources in --external-root against the recorded content pins.
Normal check mode needs only repository inputs, not a network or private source cache.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'work/S1DMACONTRACT/evidence.json'
EXTERNAL_PINS = ({'path': 'haiku-area.cpp',
  'scope': 'Pinned Haiku source; live guest cache state not verified',
  'sha256': 'a08d7f6790121c60f11a8b4404893cdc129350175c8f99d7a8d0efa6599f7855',
  'url': 'https://raw.githubusercontent.com/haiku/haiku/49a0af9585d80e42240af63ab66e31e9873f59b8/src/system/kernel/vm/VMArea.cpp'},
 {'path': 'haiku-area.h',
  'scope': 'Pinned Haiku source; live guest cache state not verified',
  'sha256': '61d3eb5a990b9e474e0fe4eac6d87422b8043c8a87076d025e4823877a1db449',
  'url': 'https://raw.githubusercontent.com/haiku/haiku/49a0af9585d80e42240af63ab66e31e9873f59b8/headers/private/kernel/vm/VMArea.h'},
 {'path': 'haiku-map64.cpp',
  'scope': 'Pinned Haiku source; live guest cache state not verified',
  'sha256': '4b42bd1a8fa732e6de771f3e5a33110a33d89acce965e94a7f310bbe6b959f0a',
  'url': 'https://raw.githubusercontent.com/haiku/haiku/49a0af9585d80e42240af63ab66e31e9873f59b8/src/system/kernel/arch/x86/paging/64bit/X86VMTranslationMap64Bit.cpp'},
 {'path': 'haiku-paging64.h',
  'scope': 'Pinned Haiku source; live guest cache state not verified',
  'sha256': 'faebc7236d825529981a3dbdeb89429e6e8c1c61a73a153a51359fb2d56fcae2',
  'url': 'https://raw.githubusercontent.com/haiku/haiku/49a0af9585d80e42240af63ab66e31e9873f59b8/src/system/kernel/arch/x86/paging/64bit/X86PagingMethod64Bit.h'},
 {'path': 'haiku-vm.cpp',
  'scope': 'Pinned Haiku source; live guest cache state not verified',
  'sha256': 'dec556cf6beab908275718dfd386dab9d96ea1f70e3525a721086c2a6b0d5340',
  'url': 'https://raw.githubusercontent.com/haiku/haiku/49a0af9585d80e42240af63ab66e31e9873f59b8/src/system/kernel/vm/vm.cpp'},
 {'path': 'linux-vfio-type1.c',
  'scope': 'Upstream v6.8 baseline, not exact Ubuntu 6.8.0-138 source',
  'sha256': 'b51d88b911cbf8546b872ab72cfeccb4b56bfd77cdc26e670ce537b7fe0015d3',
  'url': 'https://raw.githubusercontent.com/torvalds/linux/v6.8/drivers/vfio/vfio_iommu_type1.c'},
 {'path': 'qemu-ubuntu.dsc',
  'scope': 'Ubuntu source metadata, signature not checked',
  'sha256': 'd13c0322809860a49ad377dd825ad597ece93f0b7f40e713a165dba59bb369ca',
  'url': 'https://security.ubuntu.com/ubuntu/pool/main/q/qemu/qemu_6.2+dfsg-2ubuntu6.31.dsc'},
 {'path': 'qemu-ubuntu/debian/patches/series',
  'scope': 'Exact package source after dpkg-source patch application: debian/patches/series',
  'sha256': 'c5c19fdd2dba8b2316c6a303b816a8c8c8a3090bcb72ee5d410a7e7919996748',
  'url': 'https://security.ubuntu.com/ubuntu/pool/main/q/qemu/qemu_6.2+dfsg-2ubuntu6.31.dsc'},
 {'path': 'qemu-ubuntu/hw/pci/pci.c',
  'scope': 'Exact package source after dpkg-source patch application: hw/pci/pci.c',
  'sha256': 'e879e66ab3ceb230bb3260bd98381e1a12c0654e9fceb0c3b5df5965ff40a178',
  'url': 'https://security.ubuntu.com/ubuntu/pool/main/q/qemu/qemu_6.2+dfsg-2ubuntu6.31.dsc'},
 {'path': 'qemu-ubuntu/hw/vfio/common.c',
  'scope': 'Exact package source after dpkg-source patch application: hw/vfio/common.c',
  'sha256': '4fa200c1500cb16673c779d2badae7a647a493b45c9c8aff37d19f571486db60',
  'url': 'https://security.ubuntu.com/ubuntu/pool/main/q/qemu/qemu_6.2+dfsg-2ubuntu6.31.dsc'},
 {'path': 'qemu-ubuntu/hw/vfio/pci.c',
  'scope': 'Exact package source after dpkg-source patch application: hw/vfio/pci.c',
  'sha256': '577b9dc21f7e0268700a8c66258035b4e008418132a8a5d96d709596f237252f',
  'url': 'https://security.ubuntu.com/ubuntu/pool/main/q/qemu/qemu_6.2+dfsg-2ubuntu6.31.dsc'},
 {'path': 'qemu-ubuntu/hw/vfio/trace-events',
  'scope': 'Exact package source after dpkg-source patch application: hw/vfio/trace-events',
  'sha256': '623e693f7965de9bbe676adfbe82988848f83d4daeeb953382e90b93b22a23bc',
  'url': 'https://security.ubuntu.com/ubuntu/pool/main/q/qemu/qemu_6.2+dfsg-2ubuntu6.31.dsc'},
 {'path': 'qemu_6.2+dfsg-2ubuntu6.31.debian.tar.xz',
  'scope': 'Ubuntu patch archive',
  'sha256': '97dd9f9b065452e02b00f87e70e94d9f6369716de7d739ae605240d2522183a2',
  'url': 'https://security.ubuntu.com/ubuntu/pool/main/q/qemu/qemu_6.2+dfsg-2ubuntu6.31.debian.tar.xz'},
 {'path': 'qemu_6.2+dfsg.orig.tar.xz',
  'scope': 'Ubuntu orig archive',
  'sha256': '470d4202ab6302f184bf934008d2306c144d3221aa3b8ceb8a710414755af61b',
  'url': 'https://security.ubuntu.com/ubuntu/pool/main/q/qemu/qemu_6.2+dfsg.orig.tar.xz'})
LOCAL = (
    'tools/dma_contract.py', 'tools/haiku/card_run.py',
    'src/os/HaikuBackend.c', 'src/os/HaikuMemory.h', 'src/os/HaikuMemory.cpp',
    'src/os/NativeOwner.h', 'src/os/NativeOwner.cpp', 'src/runtime/PreStart.cpp',
    'reference/haiku/headers/private/kernel/arch/x86/64/atomic.h',
    'reference/nouveau/nvkm/subdev/fb/base.c', 'reference/nouveau/nvkm/subdev/fb/gf100.c',
    'reference/nouveau/nvkm/subdev/fb/gk110.c',
    'reference/nouveau/nvkm/subdev/bar/g84.c',
    'results/20261027-b5-identity/attempt-02/launch.json',
    'results/20261027-b5-identity/attempt-02/serial.log',
    'work/S1DMACONTRACT/host-inventory.log',
)


def report():
    capture=ROOT/'results/20261027-b5-identity/attempt-02'
    launch=json.loads((capture/'launch.json').read_text())
    args=launch['args']
    devices=[args[i+1] for i,a in enumerate(args[:-1]) if a=='-device']
    commands=sorted(set(re.findall(r'k40_os: PCI command 0x([0-9a-fA-F]{4})',
                                  (capture/'serial.log').read_text())))
    return dict(scope='SOURCE_AND_SAVED_EVIDENCE_ONLY; no live DMA contract',
        saved_launch=dict(machine=args[args.index('-machine')+1],ram_mib=int(args[args.index('-m')+1]),
            vfio_devices=sorted(d for d in devices if d.startswith('vfio-pci,')),
            explicit_guest_iommu_devices=sorted(d for d in devices if 'iommu' in d.lower()),
            pci_command_values=commands,source_commit=launch['source_commit'],
            scope=launch['scope'],host_snapshot=launch['host']),
        external_sources=list(EXTERNAL_PINS),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(LOCAL)},
        external_validation='Run --verify-external separately; pins alone do not verify a local cache',
        actual_b5_qemu_binary_identity_known=False,
        live_iova_mapping_verified=False,live_cache_contract_verified=False,
        physical_payload_visibility_verified=False,publication_enabled=False,production_eligible=False)


def verify_external(root):
    for pin in EXTERNAL_PINS:
        if hashlib.sha256((root/pin['path']).read_bytes()).hexdigest()!=pin['sha256']:
            raise ValueError('external source mismatch: '+pin['path'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--verify-external',action='store_true')
    parser.add_argument('--external-root',type=Path,default=Path('/tmp/k40-dma-sources'))
    args=parser.parse_args()
    if args.verify_external: verify_external(args.external_root)
    text=json.dumps(report(),indent=2,sort_keys=True)+'\n'
    if args.check:
        return 0 if OUTPUT.is_file() and OUTPUT.read_text()==text else 1
    OUTPUT.write_text(text)
    print('DMA evidence metadata generated; publication remains denied')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
