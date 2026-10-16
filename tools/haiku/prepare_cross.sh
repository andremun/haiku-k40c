#!/usr/bin/env bash
# Copyright 2026 Mario Andrés Muñoz.
# Distributed under the terms of the MIT License.
# Rebuild only the pinned cross compiler. No sudo, VM or physical devices.
set -euo pipefail
repo_dir="$(cd "$(dirname "$0")/../.." && pwd)"
: "${HAIKU_CROSS:=$repo_dir/build/haiku-cross}"
haiku_pin=b42b90f5ec2839f8074400c849ee025b50d0f7f1
buildtools_pin=8375c2dbeaf109c520798cb234d57f0895463201
compiler="$HAIKU_CROSS/generated.x86_64/cross-tools-x86_64/bin/x86_64-unknown-haiku-gcc"
if [[ ${1:-} == --check ]]; then
    [[ $(git -C "$HAIKU_CROSS/haiku" rev-parse HEAD) == "$haiku_pin" ]]
    [[ $(git -C "$HAIKU_CROSS/buildtools" rev-parse HEAD) == "$buildtools_pin" ]]
    [[ -x $compiler && $("$compiler" -dumpmachine) == x86_64-unknown-haiku ]]
    echo "Pinned Haiku cross compiler ready; kernel/guest verification is separate."
    exit 0
fi
[[ $# == 0 ]] || { echo 'usage: prepare_cross.sh [--check]' >&2; exit 2; }
mkdir -p "$HAIKU_CROSS/hosttools/debs" "$HAIKU_CROSS/generated.x86_64" "$HAIKU_CROSS/lib" "$HAIKU_CROSS/vm"
if [[ ! -x $HAIKU_CROSS/hosttools/usr/bin/nasm ]]; then
    (
        cd "$HAIKU_CROSS/hosttools/debs"
        apt-get download bison flex m4 libfl2 libfl-dev
        curl -fLsSO https://mirror.aarnet.edu.au/ubuntu/pool/universe/n/nasm/nasm_2.15.05-1_amd64.deb
        for package in *.deb; do dpkg-deb -x "$package" ..; done
    )
fi
fetch_pin() {
    local path=$1 url=$2 pin=$3
    if [[ -d $path/.git ]]; then
        [[ $(git -C "$path" rev-parse HEAD) == "$pin" ]] || { echo "refuse to reset mismatched $path" >&2; return 1; }
        [[ -z $(git -C "$path" status --porcelain) ]] || { echo "refuse modified sources: $path" >&2; return 1; }
    else
        git init -q "$path"
        git -C "$path" remote add origin "$url"
        git -C "$path" fetch --depth=1 origin "$pin"
        git -C "$path" checkout --detach FETCH_HEAD
    fi
}
fetch_pin "$HAIKU_CROSS/haiku" https://github.com/haiku/haiku.git "$haiku_pin"
fetch_pin "$HAIKU_CROSS/buildtools" https://github.com/haiku/buildtools.git "$buildtools_pin"
export PATH="$HAIKU_CROSS/hosttools/usr/bin:$PATH"
export BISON_PKGDATADIR="$HAIKU_CROSS/hosttools/usr/share/bison"
export M4="$HAIKU_CROSS/hosttools/usr/bin/m4"
export LIBRARY_PATH="$HAIKU_CROSS/hosttools/usr/lib/x86_64-linux-gnu${LIBRARY_PATH:+:$LIBRARY_PATH}"
export CPATH="$HAIKU_CROSS/hosttools/usr/include${CPATH:+:$CPATH}"
if [[ ! -x $compiler ]]; then
    (
        cd "$HAIKU_CROSS/generated.x86_64"
        ../haiku/configure -j2 --use-gcc-pipe --cross-tools-source "$HAIKU_CROSS/buildtools" --build-cross-tools x86_64
    ) > "$HAIKU_CROSS/cross-build.log" 2>&1
fi
"$compiler" --version | head -n1
echo "Compiler built. Export HAIKU_CROSS=$HAIKU_CROSS for kcc/build-driver.sh."
