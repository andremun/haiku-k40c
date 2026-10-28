# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Render the fixed A7 guest job with complete-file publication and one open.

Pure text generation. The launcher serves this job within its one approved
launch. Host tests execute the installation/wait functions only with inert
fixtures. No standalone VM, network or file-writing entry point exists here.
"""
INSTALL = """install_artifact() {
    role=$1
    destination=$2
    expected_size=$3
    expected_sha=$4
    partial="${destination%/*}/.${destination##*/}.partial"
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
}"""
WAIT = """wait_a7_node() {
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
}"""


def job(port, artifacts):
    def install(role, destination):
        info = artifacts[role]
        return (
            f'install_artifact {role} "{destination}" {info["bytes"]} {info["sha256"]}'
        )

    host = f"http://10.0.2.2:{port}"
    return "\n".join(
        [
            "#!/bin/sh",
            "set -eu",
            f"host={host}",
            'finish() { code=$?; trap - EXIT; curl -fsS -T /tmp/a7.output "$host/job-output.txt" || true; echo "$code" > /tmp/a7.exit; curl -fsS -T /tmp/a7.exit "$host/job.exit" || true; }',
            "trap finish EXIT",
            "exec > /tmp/a7.output 2>&1",
            "echo A7-JOB-START",
            "uname -a > /tmp/a7.environment",
            'curl -fsS -T /tmp/a7.environment "$host/environment.txt"',
            'curl -fsS -T /boot/system/kernel_x86_64 "$host/kernel_x86_64"',
            "base=/boot/system/non-packaged/add-ons/kernel",
            'mkdir -p "$base/generic" "$base/drivers/bin" "$base/drivers/dev/misc"',
            INSTALL,
            WAIT,
            "echo K40-B5-BEGIN > /dev/dprintf",
            install("identity", "$base/drivers/bin/k40_identity_probe"),
            'ln -s ../../bin/k40_identity_probe "$base/drivers/dev/misc/k40_identity_probe"',
            "for pass in 1 2 3 4; do ls /dev/misc >/dev/null; sleep 1; done",
            "echo K40-B5-END > /dev/dprintf",
            install("owner", "$base/generic/k40c_a7_owner"),
            install("client", "$base/drivers/bin/k40_a7_stage"),
            'ln -s ../../bin/k40_a7_stage "$base/drivers/dev/misc/k40_a7_stage"',
            "wait_a7_node",
            "echo A7-OPEN-DEVICE",
            "exec 3<>/dev/misc/k40_a7_stage",
            "echo A7-DEVICE-OPEN",
            "dd bs=128 count=1 <&3 > /tmp/a7.request",
            'curl -fsS -T /tmp/a7.request "$host/request.bin"',
            'poll=0; while [ "$poll" -lt 120 ]; do',
            'if curl -fsS "$host/grant.bin" -o /tmp/a7.grant 2>/dev/null; then',
            "cat /tmp/a7.grant >&3; exec 3>&-; echo K40-A7-END > /dev/dprintf; exit 0; fi",
            "poll=$((poll+1)); sleep 1; done",
            "exit 1",
            "",
        ]
    )
