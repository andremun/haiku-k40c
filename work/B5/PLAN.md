# B5 Rework Plan

## 12 failures to fix

1-4. Change `top`, `ltc`, `timer`, `privring` from optional to **needed** with correct reasons sourced from grep output.
5. Change `imem` reason: "instantiated" → "instance memory" (GPU objects like page tables, RAMFC).
6. Change `mc` reason: "memory controller" → "master control" (engine enable bits, interrupts).
7. Change `privring` reason: "ring buffer" → "PRI ring" (register bus to engines).
8. Change `top` reason: "multi-gpu" → "device topology table" (lists engines and runlists).
9. Change HWW reason: "workqueue" → "hardware warning" (error report).
10. Add channel step with: `gf100_gr_init_ctxctl_int`, `gk104_chan_ramfc_write`, `gk104_runl_commit`, `gf100_gr_chan_new`, `gf100_grctx_generate`.
11. Steps 1,3,4,5: add init functions or use `partly-known`.
12. GR hook `init`: change use from `compute` → `both`.
13. After launch: add steps for job completion and result reading (unknown status).
