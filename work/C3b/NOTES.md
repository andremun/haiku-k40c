# C3b notes

Start: tools/hwmodel.py lists privring, ltc and timer; their JSON and Markdown files are generated with no decisions yet.

timer done: 6 members (init/intr/read/time/alarm_init/alarm_fini), all KNOWN, depends_on=[], no mmio accesses tracked for timer.
privring done: 3 members (preinit/init/intr), all KNOWN, depends_on=[], preinit and init both call gk104_privring_init.
