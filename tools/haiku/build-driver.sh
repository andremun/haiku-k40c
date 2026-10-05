#!/usr/bin/env bash
# Build a loadable Haiku kernel driver on Linux.
# Usage: tools/haiku/build-driver.sh NAME SOURCE.c [SOURCE.c ...]
# Output: build/haiku/NAME (ELF shared object linked against kernel.so).
# The link uses --no-undefined: every kernel symbol must exist in kernel.so.
set -e
. "$(dirname "$0")/config.sh"
[ $# -ge 2 ] || { echo "usage: $0 NAME SOURCE.c [SOURCE.c ...]" >&2; exit 2; }
name=$1; shift
out="$REPO_ROOT/build/haiku"; mkdir -p "$out/obj"
objs=()
for src in "$@"; do
    obj="$out/obj/${name}_$(basename "${src%.*}").o"
    "$(dirname "$0")/kcc" -O2 ${KCFLAGS:-} -c "$src" -o "$obj"
    objs+=("$obj")
done
"${HAIKU_GCC_PREFIX}gcc" -shared -nostdlib -z max-page-size=0x1000 -z noseparate-code -z norelro \
    -Wl,--no-undefined -Wl,-soname="$name" -o "$out/$name" "${objs[@]}" \
    -L"$HAIKU_KERNEL_SO_DIR" -l:kernel.so
echo "built $out/$name"
