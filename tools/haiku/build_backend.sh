#!/usr/bin/env bash
# Copyright 2026 Mario Andrés Muñoz.
# Distributed under the terms of the MIT License.
# Compile both native probe configurations and all freestanding core objects.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/../.." && pwd)"
: "${HAIKU_CROSS:=$repo_dir/build/haiku-cross}"
export HAIKU_CROSS
cd "$repo_dir"
[[ $# == 0 || ( $# == 1 && $1 == --objects-only ) ]] || { echo 'usage: build_backend.sh [--objects-only]' >&2; exit 2; }
bash tools/haiku/prepare_cross.sh --check
mkdir -p build/haiku
tools/haiku/kcc -std=gnu11 -Werror -Isrc/os -c src/os/HaikuBackend.c -o build/haiku/HaikuBackend.o
tools/haiku/kcc -std=gnu11 -Werror -DK40_CARDLESS_TEST -Isrc/os -c src/os/HaikuProbe.c -o build/haiku/HaikuProbe.o
tools/haiku/kcc -std=gnu11 -Werror -Isrc/os -c src/os/HaikuProbe.c -o build/haiku/HaikuProbe.identity.o
for source in devinit/Interpreter memory/Memory runtime/Bootstrap runtime/S1Experiment os/HaikuMemory; do
    tools/haiku/kcc -std=c++17 -Werror -Isrc -c "src/$source.cpp" -o "build/haiku/${source##*/}.o"
done
tools/haiku/kcc -std=c++17 -Werror -Isrc -c tools/haiku/selftest/memory.cpp -o build/haiku/MemoryProbe.o
if [[ ${1:-} == --objects-only ]]; then
    echo 'Native objects compile; no kernel link/load result is claimed.'
    exit 0
fi
[[ -f $HAIKU_CROSS/lib/kernel.so ]] || { echo 'Matching kernel.so absent. Retrieve the guest kernel with cardless_run.py, preserve its hash/environment, then convert a copy with elfedit --output-type dyn.' >&2; exit 2; }
KCFLAGS="-std=gnu11 -Werror -DK40_CARDLESS_TEST -Isrc/os" tools/haiku/build-driver.sh k40_cardless_probe src/os/HaikuBackend.c src/os/HaikuProbe.c
KCFLAGS="-std=gnu11 -Werror -Isrc/os" tools/haiku/build-driver.sh k40_identity_probe src/os/HaikuBackend.c src/os/HaikuProbe.c
KCFLAGS="-Werror -Isrc" tools/haiku/build-driver.sh k40_memory_probe src/os/HaikuBackend.c src/memory/Memory.cpp src/os/HaikuMemory.cpp tools/haiku/selftest/memory.cpp
python3 tools/haiku/probe_stage.py build/haiku/k40_identity_probe
echo 'Linked probes. B5 uses card_run.py under ADR 005. Cardless checks use cardless_run.py.'
