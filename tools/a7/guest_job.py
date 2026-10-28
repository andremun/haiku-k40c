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
    test ! -e "$destination"
    mkdir "$stage/$role"
    curl -fsS -o "$stage/$role/addon" "$host/$role"
    chmod +x "$stage/$role/addon"
    ln "$stage/$role/addon" "$destination"
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


def job(port):
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
            "base=$(finddir B_USER_NONPACKAGED_ADDONS_DIRECTORY)",
            'stage="$base/.k40-a7-staging"',
            'mkdir -p "$base"',
            'mkdir "$stage"',
            'mkdir -p "$base/kernel/generic" "$base/kernel/drivers/bin" "$base/kernel/drivers/dev/misc"',
            INSTALL,
            WAIT,
            "echo K40-B5-BEGIN > /dev/dprintf",
            'install_artifact identity "$base/kernel/drivers/bin/k40_identity_probe"',
            'ln -s ../../bin/k40_identity_probe "$base/kernel/drivers/dev/misc/k40_identity_probe"',
            "for pass in 1 2 3 4; do ls /dev/misc >/dev/null; sleep 1; done",
            "echo K40-B5-END > /dev/dprintf",
            'install_artifact owner "$base/kernel/generic/k40c_a7_owner"',
            'install_artifact client "$base/kernel/drivers/bin/k40_a7_stage"',
            'ln -s ../../bin/k40_a7_stage "$base/kernel/drivers/dev/misc/k40_a7_stage"',
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
