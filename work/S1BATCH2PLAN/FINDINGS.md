# Findings

- KNOWN / HARDWARE_VERIFIED: bf67465 records finite A7/BAR1 success, selected
  R5 unchanged and host mastering off. No channel or S1 result follows.
- KNOWN / SOURCE_ONLY: selected GK110B dispatch uses GK110 FIFO/GK104 VMM.
  A software-only group selects channel preemption and channel-only runlist entries.
- KNOWN from current code: the batch-1 BAR1 mapper ends disabled and retains
  seven arena objects. Channel work needs an explicit same-owner handoff.
  A separate allocator could overlap retained backing and is excluded.
- KNOWN / SOURCE_ONLY: channel registers start at 0x800000, outside the current
  8 MiB BAR0 view. The new mapping scope must be validated and reviewed.
- KNOWN / SOURCE_ONLY: USERD uses physical addresses in RAMFC, BAR VA in 0x2254,
  and a 0x200-byte stride. The source allocates one slot per channel ID (4096).
  A writable CPU BAR1 slot view is a new effect, unlike the prior read-only test.
- KNOWN / SOURCE_ONLY: channel invalidation differs from BAR HUB_ONLY. GP_GET
  and payload GET differ. The finite progress predicate must state both meanings.
- KNOWN / SOURCE_ONLY: normal FIFO/queue init enables interrupts. The polling-only
  policy needs an explicit deviation and raw leaf fault evidence, not masked status.
- UNKNOWN: GR-free scheduling. The full Linux trace includes GR setup.
- UNKNOWN: generic hardware quiescence/live reuse. Source recovery idle loops
  do not prove arbitrary freeing. Plan requires finite detach plus retention
  through guest end, with separate primary/cleanup results and no release shortcut.
- Six tasks put contract first and teardown before submission. The final exact
  combined package needs cardless rehearsal, Claude review and a new explicit yes.
- KNOWN / SOURCE_ONLY: nouveau_chan.c:302-307 supplies devm=BIT(0)
  separately from runlist/runq. The task texts prohibit deriving that RAMFC field
  from an unrelated engine or PBDMA mask. It needs its own source binding.
