#!/usr/bin/env bash
# Reference job again, with Nouveau's own debug log (debug=trace) next to
# the register trace. Run in the Linux guest with the K40c. 2026-10-13.
set -u
cd ~/files && mkdir -p dbg && cc -O2 -o compute_test compute_test.c -lEGL -lGLESv2 -lgbm || exit 2
lsmod | grep -q '^nouveau' && { echo "nouveau is already loaded: restart the guest"; exit 2; }
sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null
echo 64000 | sudo tee /sys/kernel/tracing/buffer_size_kb >/dev/null
echo mmiotrace | sudo tee /sys/kernel/tracing/current_tracer >/dev/null
sudo sh -c 'cat /sys/kernel/tracing/trace_pipe > /tmp/mmiotrace.txt' & tp=$!
sudo sh -c 'dmesg -w > /tmp/dmesg.txt' & dp=$!
sudo modprobe nouveau debug=trace; sleep 15
echo "MARK compute_test start" | sudo tee /sys/kernel/tracing/trace_marker >/dev/null
echo "MARK compute_test start" | sudo tee /dev/kmsg >/dev/null
D=/opt/mesa-debug/lib/x86_64-linux-gnu
sudo env LD_LIBRARY_PATH=$D GBM_BACKENDS_PATH=$D/gbm __EGL_VENDOR_LIBRARY_DIRS=/opt/mesa-debug/share/glvnd/egl_vendor.d ./compute_test > dbg/compute_test.log 2>&1
echo "exit status $?" >> dbg/compute_test.log
echo "MARK compute_test end" | sudo tee /sys/kernel/tracing/trace_marker >/dev/null
echo "MARK compute_test end" | sudo tee /dev/kmsg >/dev/null
sleep 3
echo nop | sudo tee /sys/kernel/tracing/current_tracer >/dev/null 2>&1
sleep 2; sudo kill $tp $dp 2>/dev/null; sudo pkill -f trace_pipe; sudo pkill -f 'dmesg -w'
sudo cp /tmp/mmiotrace.txt /tmp/dmesg.txt dbg/; sudo chown $USER dbg/*
grep -E '^(renderer|elements|PASS|FAIL)' dbg/compute_test.log; wc -l dbg/dmesg.txt dbg/mmiotrace.txt
xz -f -T0 dbg/mmiotrace.txt dbg/dmesg.txt 2>/dev/null; ls -la dbg
