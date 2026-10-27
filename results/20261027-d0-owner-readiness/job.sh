#!/bin/sh
set -eu
host=http://10.0.2.2:37441
uname -a > /tmp/k40-environment.txt
curl -fsS -T /tmp/k40-environment.txt "$host/environment.txt"
curl -fsS -T /boot/system/kernel_x86_64 "$host/kernel_x86_64"
trap 'status=$?; echo "$status" > /tmp/k40-job.exit; curl -fsS -T /tmp/k40-job.exit "$host/job.exit"' EXIT
addons=$(finddir B_USER_NONPACKAGED_ADDONS_DIRECTORY)
mkdir -p "$addons/kernel/generic"
curl -fsS -o "$addons/kernel/generic/k40c_owner" "$host/owner_module"
chmod +x "$addons/kernel/generic/k40c_owner"
base="$addons/kernel/drivers"
mkdir -p "$base/bin" "$base/dev/misc"
curl -fsS -o "$base/bin/k40_cardless_probe" "$host/probe"
chmod +x "$base/bin/k40_cardless_probe"
ln -sf ../../bin/k40_cardless_probe "$base/dev/misc/k40_cardless_probe"
echo K40-CARDLESS-BEGIN > /dev/dprintf
ls /dev/misc >/dev/null
sleep 1
ls /dev/misc >/dev/null
sleep 1
ls /dev/misc >/dev/null
sleep 1
ls /dev/misc >/dev/null
sleep 1
echo K40-CARDLESS-END > /dev/dprintf
