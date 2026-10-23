# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Shared settings for the Haiku tools. Sourced, not run.
# HAIKU_CROSS holds the cross compiler, the Haiku source tree, kernel.so and
# the test VM (see docs/HAIKU_BUILD_TEST.md for how it was built).
: "${HAIKU_CROSS:=$HOME/haiku-cross}"
HAIKU_GCC_PREFIX="$HAIKU_CROSS/generated.x86_64/cross-tools-x86_64/bin/x86_64-unknown-haiku-"
HAIKU_HEADERS="$HAIKU_CROSS/haiku/headers"
HAIKU_KERNEL_SO_DIR="$HAIKU_CROSS/lib"
HAIKU_VM_DIR="$HAIKU_CROSS/vm"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
