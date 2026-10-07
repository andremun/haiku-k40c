#!/usr/bin/env bash
# Build everything in $HAIKU_CROSS (default ~/haiku-cross) that the other
# scripts here need: host tools, Haiku sources, the cross compiler, the
# test image and kernel.so. No root. No GPU. Each step is skipped when its
# result exists, so the script can be run again after a failure.
# Needs: git, gcc, make, gawk, makeinfo, curl, unzip, elfedit, qemu with
# KVM and OVMF (/usr/share/OVMF), about 4 GB of disk and 20 minutes.
# Usage: tools/haiku/setup.sh
set -euo pipefail
. "$(dirname "$0")/config.sh"
T="$(cd "$(dirname "$0")" && pwd)"
H=$HAIKU_CROSS
HAIKU_COMMIT=b42b90f5ec2839f8074400c849ee025b50d0f7f1
BUILDTOOLS_COMMIT=8375c2dbeaf109c520798cb234d57f0895463201
HREV=hrev60207          # test image; kernel.so must come from this image
IMG=haiku-master-${HREV}-x86_64-anyboot
CDN=https://haiku-nightly.cdn.haiku-os.org/x86_64
mkdir -p "$H/hosttools/debs" "$H/vm" "$H/lib" "$H/generated.x86_64"

# 1. Host tools from Ubuntu packages, unpacked without root.
if [ ! -x "$H/hosttools/usr/bin/nasm" ]; then
    ( cd "$H/hosttools/debs"
      apt-get download bison flex m4 libfl2 libfl-dev
      # nasm: the candidate version is in the ESM archive (needs a login).
      curl -sfLO https://mirror.aarnet.edu.au/ubuntu/pool/universe/n/nasm/nasm_2.15.05-1_amd64.deb
      for d in *.deb; do dpkg -x "$d" "$H/hosttools"; done )
fi
cat > "$H/env.sh" <<'ENV'
# Host tools for the Haiku cross-tools build, unpacked without root.
# Usage: source ~/haiku-cross/env.sh
HAIKU_CROSS="${HAIKU_CROSS:-$HOME/haiku-cross}"
export PATH="$HAIKU_CROSS/hosttools/usr/bin:$PATH"
export BISON_PKGDATADIR="$HAIKU_CROSS/hosttools/usr/share/bison"
export M4="$HAIKU_CROSS/hosttools/usr/bin/m4"
export LIBRARY_PATH="$HAIKU_CROSS/hosttools/usr/lib/x86_64-linux-gnu${LIBRARY_PATH:+:$LIBRARY_PATH}"
export CPATH="$HAIKU_CROSS/hosttools/usr/include${CPATH:+:$CPATH}"
ENV
. "$H/env.sh"

# 2. Sources at the pinned commits (shallow).
fetch() { # dir url commit
    [ "$(git -C "$1" rev-parse HEAD 2>/dev/null)" = "$3" ] && return 0
    [ -d "$1/.git" ] || { git init -q "$1"; git -C "$1" remote add origin "$2"; }
    git -C "$1" fetch -q --depth 1 origin "$3"
    git -C "$1" -c advice.detachedHead=false checkout -q FETCH_HEAD
}
fetch "$H/haiku" https://github.com/haiku/haiku.git "$HAIKU_COMMIT"
fetch "$H/buildtools" https://github.com/haiku/buildtools.git "$BUILDTOOLS_COMMIT"

# 3. Cross compiler. configure must run in generated.x86_64.
if [ ! -x "${HAIKU_GCC_PREFIX}gcc" ]; then
    ( cd "$H/generated.x86_64"
      ../haiku/configure -j"$(nproc)" --use-gcc-pipe --cross-tools-source "$H/buildtools" \
          --build-cross-tools x86_64 > "$H/cross-build.log" 2>&1 ) \
        || { echo "cross-tools build failed: see $H/cross-build.log" >&2; exit 1; }
fi

# 4. Test image, checked against the published SHA-256.
if [ ! -f "$H/vm/$IMG.iso" ]; then
    ( cd "$H/vm"
      curl -sfLO "$CDN/$IMG.zip"; curl -sfLO "$CDN/$IMG.zip.sha256"
      want=$(awk '{print $NF}' "$IMG.zip.sha256"); got=$(sha256sum "$IMG.zip" | cut -d' ' -f1)
      [ "$want" = "$got" ] || { echo "SHA-256 mismatch for $IMG.zip" >&2; exit 1; }
      unzip -o -q "$IMG.zip" "$IMG.iso" )
fi

# 5. kernel.so: the image's own kernel, copied out of the running VM.
if [ ! -f "$H/lib/kernel.so" ]; then
    V=$H/vm; up=$(mktemp -d); log=$V/serial.log
    python3 - "$up" <<'PY' &
import http.server, os, sys
class H(http.server.BaseHTTPRequestHandler):
    def do_PUT(self):
        left = int(self.headers.get("Content-Length", 0))
        with open(os.path.join(sys.argv[1], os.path.basename(self.path)), "wb") as f:
            while left:
                b = self.rfile.read(min(left, 1 << 16))
                if not b:
                    break
                f.write(b); left -= len(b)
        self.send_response(201); self.end_headers()
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", 8001), H).serve_forever()
PY
    srv=$!
    hmp() { python3 "$T/qemu_hmp.py" "$V/monitor.sock" cmd "$1" >/dev/null; }
    waitlog() { local i; for ((i = 0; i < $2; i++)); do grep -aq "$1" "$log" 2>/dev/null && return 0; sleep 1; done; return 1; }
    trap '[ -S "$V/monitor.sock" ] && hmp quit; kill $srv 2>/dev/null; rm -f "$V/monitor.sock"' EXIT
    rm -f "$log" "$V/monitor.sock"; cp /usr/share/OVMF/OVMF_VARS_4M.fd "$V/ovmf-vars.fd"
    # Same VM as vm-test.sh: no host devices.
    qemu-system-x86_64 -name haiku-test -enable-kvm -machine q35 -cpu host -smp 2 -m 2048 -snapshot \
        -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
        -drive if=pflash,format=raw,file="$V/ovmf-vars.fd" \
        -drive file="$V/$IMG.iso",format=raw,if=none,id=d0 -device ide-hd,drive=d0,bus=ide.0 \
        -vga std -netdev user,id=n0,restrict=off -device e1000,netdev=n0 \
        -display none -serial file:"$log" -monitor unix:"$V/monitor.sock",server,nowait \
        >"$V/qemu.out" 2>&1 &
    waitlog "ps2: keyboard found" 180 || { echo "Haiku did not boot (see $log)" >&2; exit 1; }
    sleep 20; hmp "sendkey ret"
    waitlog "first login script" 120 || { echo "desktop did not start" >&2; exit 1; }
    sleep 12; hmp "sendkey alt-meta_l-t"; sleep 8
    python3 "$T/qemu_hmp.py" "$V/monitor.sock" type \
        "curl -s -T /boot/system/kernel_x86_64 http://10.0.2.2:8001/kernel_x86_64; echo UPLOAD-END > /dev/dprintf"
    waitlog "UPLOAD-END" 90 || { echo "kernel copy did not finish" >&2; exit 1; }
    cp "$up/kernel_x86_64" "$H/lib/kernel_x86_64"; cp "$up/kernel_x86_64" "$H/lib/kernel.so"
    elfedit --output-type dyn "$H/lib/kernel.so"
    rm -rf "$up"
fi
echo "Ready: $H. Test with: make haiku-selftest"
