#!/bin/sh
set -eu
host=http://10.0.2.2:38387
finish() { code=$?; trap - EXIT; curl -fsS -T /tmp/a7.output "$host/job-output.txt" || true; echo "$code" > /tmp/a7.exit; curl -fsS -T /tmp/a7.exit "$host/job.exit" || true; }
trap finish EXIT
exec > /tmp/a7.output 2>&1
echo A7-JOB-START
uname -a > /tmp/a7.environment
curl -fsS -T /tmp/a7.environment "$host/environment.txt"
curl -fsS -T /boot/system/kernel_x86_64 "$host/kernel_x86_64"
base=/boot/system/non-packaged/add-ons/kernel
mkdir -p "$base/generic" "$base/drivers/bin" "$base/drivers/dev/misc"
stage=/boot/system/non-packaged/.k40-a7-staging
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
    echo "A7-INSTALL $role size=$expected_size sha256=$expected_sha inode-before=$before inode-after=$after"
}
wait_a7_node() {
    node_poll=0
    while [ "$node_poll" -lt 30 ]; do
        ls /dev/misc >/dev/null
        if [ -c /dev/misc/k40_a7_stage ]; then
            echo A7-DEVICE-PUBLISHED
            return 0
        fi
        node_poll=$((node_poll+1))
        sleep 1
    done
    echo A7-DEVICE-PUBLICATION-TIMEOUT >&2
    return 1
}
echo K40-B5-BEGIN > /dev/dprintf
install_artifact identity "$base/drivers/bin/k40_identity_probe" 8696 8c45ec7bf2a2a16f3981431a3d0e5ee3588cfa9df63429ea51b01cc93fdf9d2f
ln -s ../../bin/k40_identity_probe "$base/drivers/dev/misc/k40_identity_probe"
for pass in 1 2 3 4; do ls /dev/misc >/dev/null; sleep 1; done
echo K40-B5-END > /dev/dprintf
install_artifact owner "$base/generic/k40c_a7_owner" 368672 944bdaf424789914a7b8a8b8fe3af272ea1f4d93d387e931d336aa084ce4c087
install_artifact client "$base/drivers/bin/k40_a7_stage" 7552 d11b0d3773e8f1a206a98b79b85a1c6e7c73948dbe096001d472ef0ee66ee122
ln -s ../../bin/k40_a7_stage "$base/drivers/dev/misc/k40_a7_stage"
wait_a7_node
install_artifact helper "/boot/system/non-packaged/.k40-a7-open" 3888 58bec7c51730bf95f541c61c8ed9b8379b97f1c2b335702de0f9542698914977
cat > /tmp/a7-session.sh <<'A7_SESSION'
dd bs=128 count=1 <&3 > /tmp/a7.request
curl -fsS -T /tmp/a7.request "$host/request.bin"
poll=0; while [ "$poll" -lt 120 ]; do
if curl -fsS "$host/grant.bin" -o /tmp/a7.grant 2>/dev/null; then
cat /tmp/a7.grant >&3; exec 3>&-; echo K40-A7-END > /dev/dprintf; exit 0; fi
poll=$((poll+1)); sleep 1; done
exit 1
A7_SESSION
export host
echo A7-OPEN-DEVICE
/boot/system/non-packaged/.k40-a7-open
