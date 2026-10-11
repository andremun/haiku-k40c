# Register Database
One YAML file per subsystem, one entry per distinct register.
All registers have status `SOURCE_ONLY` — traced to Nouveau source
but not yet verified against hardware captures.
## Summary
| File | Entries | Named | No address |
|---|---|---|---|
| bar.yaml | 7 | 3 | 0 |
| bus.yaml | 4 | 4 | 0 |
| ce.yaml | 3 | 3 | 0 |
| fb.yaml | 31 | 11 | 1 |
| fifo.yaml | 89 | 34 | 22 |
| gr.yaml | 254 | 146 | 27 |
| imem.yaml | 3 | 3 | 0 |
| ltc.yaml | 23 | 11 | 2 |
| mc.yaml | 7 | 5 | 0 |
| mmu.yaml | 3 | 3 | 0 |
| pbdma.yaml | 10 | 10 | 0 |
| pci.yaml | 6 | 5 | 0 |
| privring.yaml | 21 | 15 | 0 |
| top.yaml | 1 | 0 | 0 |
| **Total** | **462** | **253** | **52** |
## Not named — mc
| Address | Function(s) |
|---|---|
| 0x000260 | gf100_mc_unk260 |
| 0x001850 | nv04_mc_init |
## Not named — fb
| Address | Function(s) |
|---|---|
| 0x10ecc0 | gk104_ram_init |
| 0x10f400 | gk104_ram_prog_0 |
| 0x10f410 | gk104_ram_prog_0 |
| 0x10f420 | gk104_ram_prog_0 |
| 0x10f430 | gk104_ram_prog_0 |
| 0x10f440 | gk104_ram_prog_0 |
| 0x10f444 | gk104_ram_prog_0 |
| 0x10f468 | gk104_ram_prog_0 |
| 0x10f584 | gk104_ram_init |
| 0x10f900 | gk104_ram_train_init_0 |
| 0x10f918 | gf100_ram_init |
| 0x10f918 | gk104_ram_train_init_0 |
| 0x10f91c | gf100_ram_init |
| 0x10f920 | gf100_ram_init |
| 0x10f920 | gk104_ram_train_init_0 |
| 0x10f924 | gf100_ram_init |
| 0x10f968 | gf100_ram_init |
| 0x10f968 | gk104_ram_train_init_0 |
| 0x10f96c | gf100_ram_init |
| (variable) | gk104_ram_nuts |
## Not named — fifo
| Address | Function(s) |
|---|---|
| 0x002044 | nv50_fifo_init |
| 0x002204 | gf100_fifo_init_pbdmas |
| 0x002208 | gf100_fifo_init_pbdmas |
| 0x00220c | gf100_fifo_init_pbdmas |
| 0x002210 | gf100_fifo_init_pbdmas |
| 0x002214 | gf100_fifo_init_pbdmas |
| 0x002218 | gf100_fifo_init_pbdmas |
| 0x00221c | gf100_fifo_init_pbdmas |
| 0x00227c | gf100_runl_pending |
| 0x002500 | nv50_fifo_init |
| 0x00250c | nv50_fifo_init |
| 0x0025a4 | gf100_fifo_intr_engine |
| 0x0025a8 | gf100_fifo_intr_engine_unit |
| 0x002600 | nv50_chan_bind, nv50_chan_start, nv50_chan_stop, nv50_chan_unbind |
| 0x002600 | nv50_fifo_init |
| 0x002628 | gf100_fifo_init, gf100_fifo_intr_engine_unit |
| 0x003200 | nv50_fifo_init |
| 0x003220 | nv04_fifo_intr_dma_pusher |
| 0x003228 | nv04_fifo_intr_dma_pusher |
| 0x003240 | nv04_fifo_intr_dma_pusher |
| 0x003244 | nv04_fifo_intr_dma_pusher |
| 0x003250 | nv04_fifo_intr_cache_error, nv50_fifo_init |
| 0x003258 | nv04_fifo_swmthd |
| 0x003280 | nv04_fifo_swmthd |
| 0x0032ec | nv50_runl_commit, nv50_runl_pending |
| 0x0032f4 | nv50_runl_commit |
| 0x0032fc | nv50_ectx_bind |
| 0x003320 | nv04_fifo_intr_dma_pusher |
| 0x003328 | nv04_fifo_intr_dma_pusher |
| 0x003330 | nv04_fifo_intr_dma_pusher |
| 0x003334 | nv04_fifo_intr_dma_pusher |
| 0x003364 | nv04_fifo_intr_dma_pusher |
| 0x00b860 | nv50_ectx_bind |
| (variable) | nv04_chan_stop, nv04_fifo_intr, nv04_fifo_intr_cache_error |
| (variable) | nv04_chan_stop, nv04_fifo_init, nv04_fifo_intr_cache_error |
| (variable) | nv04_chan_stop, nv04_fifo_init, nv04_fifo_intr |
| (variable) | nv04_chan_stop |
| (variable) | __acquires, __releases, nv04_chan_stop, nv04_fifo_init, nv04_fifo_intr |
| (variable) | __acquires, nv04_fifo_init, nv04_fifo_intr, nv04_fifo_intr_cache_error |
| (variable) | nv04_fifo_init, nv04_fifo_intr |
| (variable) | nv04_fifo_init |
| (variable) | nv04_fifo_init |
| (variable) | nv04_fifo_init |
| (variable) | nv04_fifo_intr_cache_error |
| (variable) | nv04_chan_stop, nv04_fifo_intr_cache_error |
| (variable) | __acquires, nv04_fifo_intr_cache_error |
| (variable) | nv04_fifo_intr_cache_error |
| (variable) | __acquires, __releases, nv04_chan_stop, nv04_fifo_init, nv04_fifo_intr, nv04_fifo_intr_cache_error |
| (variable) | nv04_fifo_init |
| (variable) | nv04_fifo_init |
| (variable) | nv04_chan_start, nv04_chan_stop |
| (variable) | nv04_fifo_intr |
| (variable) | nv04_fifo_intr_cache_error |
| (variable) | nv04_fifo_intr_cache_error |
| (variable) | nv04_chan_stop |
