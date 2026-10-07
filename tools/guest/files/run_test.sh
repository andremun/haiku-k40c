#!/usr/bin/env bash
# Run in the Linux guest. Builds and runs the reference compute job and
# writes the logs to ./out (copy them to reference/linux-run/ on the host).
#   ./run_test.sh           software renderer, or Nouveau if it is loaded
#   ./run_test.sh --k40c    load Nouveau under mmiotrace first, then run
set -uo pipefail
mkdir -p out
cc -O2 -o compute_test compute_test.c -lEGL -lGLESv2 -lgbm || exit 2
if [ "${1:-}" = "--k40c" ]; then
    lspci -nn -d 10de: | tee out/lspci.txt
    [ -s out/lspci.txt ] || { echo "No NVIDIA device in this guest: start it with --gpu." | tee out/RESULT.txt; exit 2; }
    if ! lsmod | grep -q '^nouveau'; then
        # Trace every register access of the driver load (kernel side of S1-S3).
        sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null
        echo 64000 | sudo tee /sys/kernel/tracing/buffer_size_kb >/dev/null
        echo mmiotrace | sudo tee /sys/kernel/tracing/current_tracer >/dev/null
        sudo sh -c 'cat /sys/kernel/tracing/trace_pipe > /tmp/mmiotrace.txt' & tp=$!
        sudo modprobe nouveau; sleep 15
        echo "MARK compute_test start" | sudo tee /sys/kernel/tracing/trace_marker >/dev/null
    fi
    sudo dmesg | grep -iE 'nouveau|drm' > out/dmesg-nouveau.txt
fi
NV50_PROG_DEBUG=1 ./compute_test > out/compute_test.log 2>&1; rc=$?
if [ -n "${tp:-}" ]; then
    echo "MARK compute_test end" | sudo tee /sys/kernel/tracing/trace_marker >/dev/null
    echo nop | sudo tee /sys/kernel/tracing/current_tracer >/dev/null
    sleep 2; sudo kill "$tp" 2>/dev/null
    sudo cp /tmp/mmiotrace.txt out/mmiotrace.txt; sudo chown "$USER" out/mmiotrace.txt
    xz -f -T0 out/mmiotrace.txt
fi
{ grep -E '^(device|renderer|version|elements|PASS|FAIL)' out/compute_test.log; uname -r
  dpkg-query -W -f='mesa ${Version}\n' libegl-mesa0 2>/dev/null; } | tee out/RESULT.txt
exit $rc
