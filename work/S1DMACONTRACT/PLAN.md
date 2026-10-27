# S1DMACONTRACT plan

1. Record existing launcher, allocation, flush-target and denied-provider evidence.
2. Identify installed QEMU and kernel versions without starting a guest. Consult
   exact primary QEMU/VFIO and pinned Haiku address/ordering source ranges.
   Save additional sources outside reference/ with exact hashes and URLs.
3. Describe CPU VA -> GPA -> VFIO IOVA -> host physical mapping, distinguishing
   source behavior from observed runtime configuration and physical verification.
4. Specify supported provider obligations and a smallest separate verification
   design. Keep publication denied. Do not implement or execute physical effects.
5. Generate deterministic source/evidence metadata with --check. Update Q7,
   licensing, status and handoff. Run make check and commit on main.

No VM, physical card, PCI/BAR, root, binding, reset, DMA publication or push.
