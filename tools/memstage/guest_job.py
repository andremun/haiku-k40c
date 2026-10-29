# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""One fixed combined guest job; identical in cardless and physical modes.

The host's continuation gates differ by mode. Only a physical, reviewed launch
can sign grants. The job never selects a role, path or address from user input.
"""
from tools.a7.guest_job import INSTALL


def job(port, a7_port, suite):
    artifacts = suite["guest_artifacts"]

    def install(role, destination):
        info = artifacts[role]
        return (
            f'install_artifact {role} "{destination}" {info["bytes"]} {info["sha256"]}'
        )

    lines = [
        "#!/bin/sh",
        "set -eu",
        f"host=http://10.0.2.2:{port}",
        'finish() { code=$?; trap - EXIT; curl -fsS -T /tmp/batch.output "$host/job-output.txt" || true; echo "$code" > /tmp/batch.exit; curl -fsS -T /tmp/batch.exit "$host/job.exit" || true; }',
        "trap finish EXIT",
        "exec > /tmp/batch.output 2>&1",
        "echo BATCH-JOB-START",
        "base=/boot/system/non-packaged/add-ons/kernel",
        'mkdir -p "$base/generic" "$base/drivers/bin" "$base/drivers/dev/misc"',
        "stage=/boot/system/non-packaged/.k40-memory-staging",
        'mkdir "$stage"',
        INSTALL.replace("A7-INSTALL", "MEM-INSTALL"),
        'wait_node() { poll=0; while [ "$poll" -lt 30 ]; do ls /dev/misc >/dev/null; if [ -c "/dev/misc/$1" ]; then echo "MEM-NODE $1"; return 0; fi; poll=$((poll+1)); sleep 1; done; return 1; }',
        'wait_gate() { poll=0; while [ "$poll" -lt 120 ]; do if curl --max-time 2 -fsS "$host/$1" -o /tmp/batch-gate 2>/dev/null; then return 0; fi; poll=$((poll+1)); sleep 1; done; return 1; }',
        install("preflight_helper", "/boot/system/non-packaged/.k40-preflight-open"),
        install("preflight", "$base/drivers/bin/k40_mem_preflight"),
        'ln -s ../../bin/k40_mem_preflight "$base/drivers/dev/misc/k40_mem_preflight"',
        "wait_node k40_mem_preflight",
        "printf '%s\n' 'exec 3>&-' 'exit 0' > /tmp/mem-preflight-session.sh",
        "preflight=0; /boot/system/non-packaged/.k40-preflight-open > /tmp/preflight.output 2>&1 || preflight=$?",
        "cat /tmp/preflight.output",
        'echo "$preflight" > /tmp/preflight.exit',
        'curl -fsS -T /tmp/preflight.output "$host/preflight-output.txt"',
        'curl -fsS -T /tmp/preflight.exit "$host/preflight-exit.txt"',
        'curl -fsS -T /tmp/batch.output "$host/preflight-install.txt"',
        "wait_gate advance-a7",
        f"curl -fsS http://10.0.2.2:{a7_port}/job.sh -o /tmp/batch-a7-child.sh",
        "child=0; sh /tmp/batch-a7-child.sh || child=$?",
        'echo "$child" > /tmp/batch-child.exit',
        'curl -fsS -T /tmp/batch-child.exit "$host/child-result.txt"',
        "wait_gate advance-memory",
        install("memory_owner", "$base/generic/k40c_memory_owner"),
        install("memory_client", "$base/drivers/bin/k40_mem_stage"),
        install("memory_helper", "/boot/system/non-packaged/.k40-memory-open"),
        'ln -s ../../bin/k40_mem_stage "$base/drivers/dev/misc/k40_mem_stage"',
        "wait_node k40_mem_stage",
        'curl -fsS -T /tmp/batch.output "$host/memory-install.txt"',
        "cat > /tmp/mem-session.sh <<'MEM_SESSION'",
        "set -eu",
        "dd bs=256 count=1 <&3 > /tmp/mem.request",
        'curl -fsS -T /tmp/mem.request "$host/request.bin"',
        'poll=0; while [ "$poll" -lt 120 ]; do',
        'if curl --max-time 2 -fsS "$host/grant.bin" -o /tmp/mem.grant 2>/dev/null; then',
        "cat /tmp/mem.grant >&3; exec 3>&-; echo K40-MEM-END > /dev/dprintf; exit 0; fi",
        "poll=$((poll+1)); sleep 1; done",
        "exit 1",
        "MEM_SESSION",
        "export host",
        "memory=0; /boot/system/non-packaged/.k40-memory-open > /tmp/memory.output 2>&1 || memory=$?",
        "cat /tmp/memory.output",
        'echo "$memory" > /tmp/memory.exit',
        'curl -fsS -T /tmp/memory.output "$host/memory-output.txt"',
        'curl -fsS -T /tmp/memory.exit "$host/memory-exit.txt"',
        "wait_gate finish-ok",
        "echo BATCH-JOB-END",
        "",
    ]
    return "\n".join(lines)
