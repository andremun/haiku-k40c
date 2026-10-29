# Native A7 logging mechanics — cardless

The fixed inert probe replays the 528 captured run6 instruction records through
live serial formatting, resident buffering and deferred drain. Each native load
runs three samples. Reloads are retained as additional samples, not GPU evidence.
The exact probe, kernel, launch and observer mode are recorded in launch.json.
All hashes and raw samples are bound by work/S1A7BUFFER/native-logging.json.

No GPU device, A7 owner, grant key, card permit, MMIO or DMA was used. This is
logger timing in init_driver context, not a POST or authenticated-write timing
measurement. Host workload was not isolated. Brief host/I2C checks overlapped
the observed guest. The sample range is retained. See docs/A7-BUFFER-REVIEW.md.
