# The Haiku build and test environment, as installed

Recorded on 2026-10-13 from the installation on `uld-jvnhw22`. Values
were read from the machine on that date. The short user guide is
`docs/HAIKU_BUILD_TEST.md`; this file is the full record of what is
installed, where it came from, and how it was set up.

## Summary

There is no Haiku installation on the workstation. Haiku code is
compiled on Ubuntu with a cross compiler, and tested by loading it into
a Haiku virtual machine that boots from a nightly image and is thrown
away after each test.

| Item | Value |
|---|---|
| Host | Ubuntu 22.04.5 LTS, kernel 6.8.0-138-generic, 2 × Xeon E5-2620 v2, 62 GB |
| Everything lives in | `~/haiku-cross` (12 GB), outside the repository |
| Built by | `tools/haiku/setup.sh`: no root, about 20 minutes, skips finished steps |
| Haiku source | commit `b42b90f5ec2839f8074400c849ee025b50d0f7f1` (2026-10-03) |
| Cross compiler | GCC 13.3.0, Binutils 2.41, target `x86_64-unknown-haiku` |
| Test image | Haiku nightly `hrev60207`, x86_64, "anyboot" |
| Virtual machine | QEMU 6.2 with KVM, UEFI firmware (OVMF 2022.02), 2 processors, 2 GB |
| First built | 2026-10-05; built again from the script on 2026-10-07 after the workstation was reinstalled |
| Self-test | `make haiku-selftest` must print `MMIO read16 [BAR2+0x500] = 0xb0c5` |

**The Haiku VM has no GPU.** It has an emulated VGA card and nothing
from NVIDIA. A Haiku guest that receives the K40c does not exist yet:
it is stage E0 of `docs/S1-PLAN.md`.

## 1. What is in `~/haiku-cross`

| Directory | Content | Source |
|---|---|---|
| `haiku/` | Haiku source tree, shallow clone | <https://github.com/haiku/haiku>, commit `b42b90f5ec2839f8074400c849ee025b50d0f7f1` |
| `buildtools/` | Haiku's GCC and Binutils sources, shallow clone | <https://github.com/haiku/buildtools>, commit `8375c2dbeaf109c520798cb234d57f0895463201` |
| `generated.x86_64/` | The built cross compiler, in `cross-tools-x86_64/bin/` with the prefix `x86_64-unknown-haiku-` | built here (section 2) |
| `hosttools/` | `bison`, `flex`, `m4`, `nasm` for the compiler build | Ubuntu packages, unpacked without root (section 2) |
| `lib/` | `kernel.so` and `kernel_x86_64`: the kernel of the test image, to link against | copied out of the running VM (section 3) |
| `vm/` | The test image, the UEFI variable file, the serial log | Haiku nightly server (section 3) |
| `linux-guest/` | The Ubuntu guest that gets the K40c for reference runs | section 6; not part of the Haiku environment |
| `env.sh` | Puts the host tools on the path | written by the setup script |

The repository's scripts find all of it through one variable,
`HAIKU_CROSS` (default `~/haiku-cross`), set in `tools/haiku/config.sh`.

## 2. The cross compiler

**Host tools.** The compiler build needs `bison`, `flex`, `m4` and
`nasm`, which were not installed and could not be installed without
root. The setup script fetches the Ubuntu packages and unpacks them
into `~/haiku-cross/hosttools`:

| Package | Version | How fetched |
|---|---|---|
| `bison` | 3.8.2+dfsg-1ubuntu0.22.04.1 | `apt-get download` |
| `flex`, `libfl2`, `libfl-dev` | 2.6.4-8build2 | `apt-get download` |
| `m4` | 1.4.18-5ubuntu2 | `apt-get download` |
| `nasm` | 2.15.05-1 | by URL from `mirror.aarnet.edu.au/ubuntu/pool/universe/n/nasm/`, because `apt-get download` selected a version that needs an Ubuntu Pro login |

`source ~/haiku-cross/env.sh` puts them on the path and sets
`BISON_PKGDATADIR`, `M4`, `LIBRARY_PATH` and `CPATH` so they work from
that location.

**Build.** Haiku's own `configure` builds the cross tools from the
`buildtools` tree. It must be run from the output directory:

```sh
source ~/haiku-cross/env.sh
cd ~/haiku-cross/generated.x86_64
../haiku/configure -j24 --use-gcc-pipe \
    --cross-tools-source ../buildtools --build-cross-tools x86_64
```

Result: `x86_64-unknown-haiku-gcc (GCC) 13.3.0` and `GNU ld (GNU
Binutils) 2.41`. The log is `~/haiku-cross/cross-build.log`. Only the
cross tools are built. Haiku itself is not built: the test VM runs a
ready-made nightly image.

## 3. The test image and its kernel

**Image.** `haiku-master-hrev60207-x86_64-anyboot`, downloaded as a zip
from `https://haiku-nightly.cdn.haiku-os.org/x86_64/` together with its
published SHA-256 file. The setup script compares the two and stops on
a mismatch, then unpacks the `.iso`.

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `vm/haiku-master-hrev60207-x86_64-anyboot.iso` | 690,814,976 | `4cd0765e078414681cd64b1063f5d6c0d19dc6daa51c142c544cc4d614260e35` |
| `vm/haiku-master-hrev60207-x86_64-anyboot.zip` | 484,636,114 | checked against the published value at download |

**Kernel to link against.** A Haiku driver is linked against the kernel
so that every kernel function it uses is checked at link time. The
kernel must be the one of the image the driver will run in. The setup
script gets it this way:

1. Start the image in the VM (the same VM as the tests).
2. Wait for the desktop, open a Terminal by sending keys through the
   QEMU monitor.
3. Type a `curl` command that uploads `/boot/system/kernel_x86_64` to a
   small HTTP server on the host (the guest reaches the host at
   `10.0.2.2`).
4. Save it twice: `lib/kernel_x86_64` unchanged, and `lib/kernel.so`
   after `elfedit --output-type dyn`, which marks it as a shared object
   so the linker accepts it.

| File | Size (bytes) | SHA-256 |
|---|---|---|
| `lib/kernel_x86_64` | 2,306,657 | `2da9a5b98719b40a61893836fb9c9e393e92e44f470e8af2024e76d50e2d2c62` |
| `lib/kernel.so` | 2,306,657 | `e521c87b34e8af92f5e1a203f25b031ea4781a798296224c07f6aae9b40b767c` |

The image and `kernel.so` must be replaced together. The Haiku source
tree (2026-10-03) and the image (`hrev60207`) are close in date but are
not the same build: the headers come from the source tree and the
kernel from the image. This has worked so far; a mismatch would show
as a link error or a load failure.

## 4. Compiling and linking a driver

| Step | Command | What it does |
|---|---|---|
| Compile one file | `tools/haiku/kcc -c file.c -o file.o` | The cross compiler with Haiku's kernel headers |
| Build a driver | `tools/haiku/build-driver.sh NAME a.c b.c` | Compiles and links to `build/haiku/NAME` |

Compiler options used by `kcc`: `-D_KERNEL_MODE -ffreestanding
-fno-builtin -mno-red-zone -fno-omit-frame-pointer -Wall
-Wno-multichar`, and for C++ also `-fno-exceptions -fno-rtti`. The
include paths are 25 directories under `haiku/headers` (public,
`private/kernel`, architecture-specific) plus
`haiku/build/config_headers`. `build-driver.sh` adds `-O2`.

Link options: `-shared -nostdlib -z max-page-size=0x1000
-z noseparate-code -z norelro -Wl,--no-undefined -Wl,-soname=NAME`
against `lib/kernel.so`. `--no-undefined` means a kernel function that
the image's kernel does not export fails at link time, on the host.

Kernel add-ons are position-independent code, which is the compiler's
default. `-fno-pic` and `-mcmodel=kernel` are for the kernel itself and
must not be used.

Drivers use the legacy driver interface (`api_version`,
`init_hardware`, `init_driver`, `uninit_driver`, `publish_devices`,
`find_device`). The example is `tools/haiku/selftest/hello_pci.c`.

## 5. The test virtual machine

`tools/haiku/vm-test.sh build/haiku/NAME [dev-subdirectory]` loads one
driver in Haiku and prints what it wrote to the kernel log. About two
minutes for each test.

The QEMU command (the same in the setup script and the test script):

```sh
qemu-system-x86_64 -name haiku-test -enable-kvm -machine q35 -cpu host \
  -smp 2 -m 2048 -snapshot \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=$V/ovmf-vars.fd \
  -drive file=$V/haiku-master-hrev60207-x86_64-anyboot.iso,format=raw,if=none,id=d0 \
  -device ide-hd,drive=d0,bus=ide.0 \
  -vga std -netdev user,id=n0,restrict=off -device e1000,netdev=n0 \
  -display none -serial file:$V/serial.log \
  -monitor unix:$V/monitor.sock,server,nowait
```

| Setting | Meaning |
|---|---|
| `-snapshot` | Nothing is written to the image. Every test starts from the same clean system. |
| `-machine q35`, OVMF | A modern PC with UEFI firmware. A fresh copy of the UEFI variable file is made for each test. |
| `-vga std`, `e1000` | Emulated graphics (PCI ID `1234:1111`) and network. No host device is passed in. |
| `-serial file:` | Haiku's kernel log goes to `~/haiku-cross/vm/serial.log`. This is how results come out. |
| `-monitor unix:` | The script sends keys and typed text through `tools/haiku/qemu_hmp.py`. |
| `-display none` | No window. |

What a test does, step by step:

1. Serve the driver file from a temporary directory with a small HTTP
   server on the host (port 8000).
2. Start the VM and wait for `ps2: keyboard found` in the log (up to
   120 s), then press Return on the "Try Haiku" dialog.
3. Wait for `first login script` (the desktop), then open a Terminal
   with a keyboard shortcut.
4. Type commands that download the driver into
   `/boot/system/non-packaged/add-ons/kernel/drivers/bin`, link it into
   `dev/<subdirectory>`, and list that `/dev` directory. Listing it
   makes Haiku load the driver.
5. Markers `VMTEST-BEGIN` and `VMTEST-END` are written to the kernel
   log around this; the script prints what is between them.
6. Stop the VM. Exit status 0 = the commands ran, 1 = a timeout, 3 = a
   kernel panic. Exit 0 does not mean the driver is correct.

The interaction is by typed keys and fixed waits because the nightly
image has no remote login set up. It is slow but has been reliable.

**Self-test of the whole chain.** `make haiku-selftest` builds
`hello_pci.c`, loads it, and must print
`MMIO read16 [BAR2+0x500] = 0xb0c5`: the driver found the emulated VGA
card through Haiku's PCI interface, mapped one of its memory regions,
and read the card's identity value. This proves the compile, link,
load, PCI and memory-mapping path on the Haiku side. It proves nothing
about the K40c.

## 6. The other guest: Ubuntu with the K40c

For completeness, since it shares the directory and the QEMU set-up.
`tools/guest/linux-setup.sh` creates it and `tools/guest/linux-run.sh
--gpu` starts it with the development card.

| Item | Value |
|---|---|
| Base | Ubuntu 24.04 server cloud image, `https://cloud-images.ubuntu.com/releases/24.04/release/` |
| Disk | 20 GB copy-on-write disk over the base image (`qemu-img`), persistent |
| Set-up | cloud-init: one user with an SSH key, development packages, Nouveau kept from loading at boot |
| Access | SSH on host port 2222 |
| Guest kernel | 6.8.0-146-generic |
| Graphics library | Ubuntu's Mesa 25.2.8, plus a debug build of the same version in `/opt/mesa-debug` (built in the guest) |
| Card | `0000:04:00.0`, passed with `-device vfio-pci`, 4 GB guest memory, no virtual IOMMU |
| Used for | the reference runs in `reference/linux-run/` and `reference/linux-run-debug/` |

## 7. Host packages the environment relies on

| Package | Version | Used for |
|---|---|---|
| `qemu-system-x86` | 1:6.2+dfsg-2ubuntu6.31 | both guests |
| `qemu-utils` | 1:6.2+dfsg-2ubuntu6.31 | `qemu-img` for the Linux guest |
| `ovmf` | 2022.02-3ubuntu0.22.04.7 | UEFI firmware (`/usr/share/OVMF/OVMF_CODE_4M.fd`, `OVMF_VARS_4M.fd`) |
| `git`, `gcc`, `make`, `gawk`, `makeinfo`, `curl`, `unzip`, `elfedit` | system | the setup script |

These were already installed on the workstation. KVM access needs the
user to be allowed to use `/dev/kvm`, which it is.

## 8. Limits and things to know

- **One VM test at a time.** A test uses 2 processor threads and 2 GB
  and slows the language model while it runs.
- **Nothing persists** in the Haiku VM. A driver is downloaded and
  loaded again in every test.
- **No GPU, by rule.** `vm-test.sh` takes no QEMU options and must not
  be given host devices. A result from this VM is evidence for the
  Haiku side of the code only.
- **Not yet built:** a Haiku guest with the K40c; a way to get more
  than the kernel log out of Haiku; a persistent Haiku disk; a build
  of Haiku itself from the source tree.
- **Not recorded here:** the exact build date of image `hrev60207`,
  and the result of comparing its headers with the source tree's.
