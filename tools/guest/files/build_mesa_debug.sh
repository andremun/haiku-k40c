#!/usr/bin/env bash
# Run in the Linux guest (no GPU needed, about 30 to 60 minutes, needs the
# network). Builds the same Mesa version as the Ubuntu package as a debug
# build with only the Nouveau driver and installs it in /opt/mesa-debug.
# Why: the Ubuntu package is a release build, and NV50_PROG_DEBUG=1 (the
# print of the generated GK110 shader code that task C5 needs) exists only
# in a debug build. run_test.sh uses /opt/mesa-debug when it is there.
set -euo pipefail
ver=$(dpkg-query -W -f='${Version}' libegl-mesa0)
[ -f /opt/mesa-debug/.done ] && { echo "already built: $(cat /opt/mesa-debug/.done)"; exit 0; }
if [ -f /opt/mesa-debug/lib/x86_64-linux-gnu/libEGL_mesa.so.0 ]; then   # installed, only the mark is missing
    n=$(strings -a /opt/mesa-debug/lib/x86_64-linux-gnu/libgallium*.so | grep -c NV50_PROG_DEBUG || true)
    [ "$n" -gt 0 ] && { echo "mesa $ver debug, nouveau only, $(date -I)" | sudo tee /opt/mesa-debug/.done; exit 0; }
fi
sudo sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources
sudo apt-get -qq update
sudo DEBIAN_FRONTEND=noninteractive apt-get -y -qq build-dep mesa
mkdir -p ~/mesa-src && cd ~/mesa-src
[ -d mesa-*/ ] || apt-get -qq source mesa="$ver"
cd mesa-*/
rm -rf build-debug
meson setup build-debug --prefix=/opt/mesa-debug --libdir=lib/x86_64-linux-gnu -Dbuildtype=debug \
    -Dgallium-drivers=nouveau -Dvulkan-drivers= -Dplatforms= -Dglx=disabled \
    -Degl=enabled -Dgbm=enabled -Dgles1=disabled -Dgles2=enabled -Dopengl=true -Dglvnd=enabled \
    -Dllvm=disabled -Dshared-llvm=disabled -Dgallium-va=disabled -Dgallium-vdpau=disabled \
    -Dvalgrind=disabled -Dlibunwind=disabled -Dlmsensors=disabled -Dzstd=enabled
ninja -C build-debug
sudo ninja -C build-debug install
# grep -c, not grep -q: with pipefail, grep -q ends the pipe early and the
# check fails although the string is there.
n=$(strings -a /opt/mesa-debug/lib/x86_64-linux-gnu/libgallium*.so | grep -c NV50_PROG_DEBUG || true)
[ "$n" -gt 0 ] || { echo "the build has no NV50_PROG_DEBUG"; exit 1; }
echo "mesa $ver debug, nouveau only, $(date -I)" | sudo tee /opt/mesa-debug/.done
