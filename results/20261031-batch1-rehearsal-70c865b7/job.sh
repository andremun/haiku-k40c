#!/bin/sh
set -eu
host=http://10.0.2.2:35373
finish() { code=$?; trap - EXIT; curl -fsS -T /tmp/batch.output "$host/job-output.txt" || true; echo "$code" > /tmp/batch.exit; curl -fsS -T /tmp/batch.exit "$host/job.exit" || true; }
trap finish EXIT
exec > /tmp/batch.output 2>&1
echo BATCH-JOB-START
base=/boot/system/non-packaged/add-ons/kernel
mkdir -p "$base/generic" "$base/drivers/bin" "$base/drivers/dev/misc"
stage=/boot/system/non-packaged/.k40-memory-staging
mkdir "$stage"
install_artifact() {
    role=$1
    destination=$2
    expected_size=$3
    expected_sha=$4
    partial="$stage/$role.partial"
    test ! -e "$destination"
    test ! -e "$partial"
    curl -fsS -o "$partial" "$host/$role"
    test "$(stat -c %s "$partial")" = "$expected_size"
    actual_sha=$(sha256sum "$partial")
    test "${actual_sha%% *}" = "$expected_sha"
    chmod +x "$partial"
    before=$(stat -c %i "$partial")
    mv "$partial" "$destination"
    after=$(stat -c %i "$destination")
    test "$before" = "$after"
    test ! -e "$partial"
    echo "MEM-INSTALL $role size=$expected_size sha256=$expected_sha inode-before=$before inode-after=$after"
}
wait_node() { poll=0; while [ "$poll" -lt 30 ]; do ls /dev/misc >/dev/null; if [ -c "/dev/misc/$1" ]; then echo "MEM-NODE $1"; return 0; fi; poll=$((poll+1)); sleep 1; done; return 1; }
wait_gate() { poll=0; while [ "$poll" -lt 120 ]; do if curl --max-time 2 -fsS "$host/$1" -o /tmp/batch-gate 2>/dev/null; then return 0; fi; poll=$((poll+1)); sleep 1; done; return 1; }
install_artifact preflight_helper "/boot/system/non-packaged/.k40-preflight-open" 3936 55ade2fbc1bc0a695a4c5e32a7c33ba18c21fd5c3c4aea54ae4fedc35dcc59d1
install_artifact preflight "$base/drivers/bin/k40_mem_preflight" 6424 e5df732100e12bc34778beee436dd50101bf6140e065d8fc2ca38c1fcbc83ab5
ln -s ../../bin/k40_mem_preflight "$base/drivers/dev/misc/k40_mem_preflight"
wait_node k40_mem_preflight
printf '%s
' 'exec 3>&-' 'exit 0' > /tmp/mem-preflight-session.sh
preflight=0; /boot/system/non-packaged/.k40-preflight-open > /tmp/preflight.output 2>&1 || preflight=$?
cat /tmp/preflight.output
echo "$preflight" > /tmp/preflight.exit
curl -fsS -T /tmp/preflight.output "$host/preflight-output.txt"
curl -fsS -T /tmp/preflight.exit "$host/preflight-exit.txt"
curl -fsS -T /tmp/batch.output "$host/preflight-install.txt"
wait_gate advance-a7
curl -fsS http://10.0.2.2:39959/job.sh -o /tmp/batch-a7-child.sh
child=0; sh /tmp/batch-a7-child.sh || child=$?
echo "$child" > /tmp/batch-child.exit
curl -fsS -T /tmp/batch-child.exit "$host/child-result.txt"
wait_gate advance-memory
install_artifact memory_owner "$base/generic/k40c_memory_owner" 147992 96c612406b03ad8f2d2527591045cd66b31838cd8a1ebc2d0b569655d4493f38
install_artifact memory_client "$base/drivers/bin/k40_mem_stage" 7560 04848c9711e9b373b55e70d1e9b9b8c7d8995b42f69a53c0cffad57d9750172e
install_artifact memory_helper "/boot/system/non-packaged/.k40-memory-open" 3912 bfcd73611a07737593597e7622f93d335455b73a6560f23caad9c450cbe00d3f
ln -s ../../bin/k40_mem_stage "$base/drivers/dev/misc/k40_mem_stage"
wait_node k40_mem_stage
curl -fsS -T /tmp/batch.output "$host/memory-install.txt"
cat > /tmp/mem-session.sh <<'MEM_SESSION'
set -eu
dd bs=256 count=1 <&3 > /tmp/mem.request
curl -fsS -T /tmp/mem.request "$host/request.bin"
poll=0; while [ "$poll" -lt 120 ]; do
if curl --max-time 2 -fsS "$host/grant.bin" -o /tmp/mem.grant 2>/dev/null; then
cat /tmp/mem.grant >&3; exec 3>&-; echo K40-MEM-END > /dev/dprintf; exit 0; fi
poll=$((poll+1)); sleep 1; done
exit 1
MEM_SESSION
export host
memory=0; /boot/system/non-packaged/.k40-memory-open > /tmp/memory.output 2>&1 || memory=$?
cat /tmp/memory.output
echo "$memory" > /tmp/memory.exit
curl -fsS -T /tmp/memory.output "$host/memory-output.txt"
curl -fsS -T /tmp/memory.exit "$host/memory-exit.txt"
wait_gate finish-ok
echo BATCH-JOB-END
