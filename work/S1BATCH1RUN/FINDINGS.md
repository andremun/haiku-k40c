# Findings

- Claude accepted acb2aca. The user answered “Approved” to the one-run request.
  Unchanged package and live host checks passed immediately before launch.
- Exactly one combined launch passed in 148.54 seconds. Its consumed marker
  remains. No retry, root command, manual reset or host binding change occurred.
- KNOWN / HARDWARE_VERIFIED under Haiku: A7 POST/readiness passed. The arm page
  was 0x15d2000; 0x100c10 read zero after POST. Re-arm ran; Q11 stays open.
- KNOWN / HARDWARE_VERIFIED for this finite BAR1 context: physical word patterns
  and complements passed, as did two complete mapped pages, A/B to B/B to A/B,
  three targeted invalidations and owned-context disable. Seven allocations
  remained retained. Selected per-phase guest faults and IO rejections were zero.
- Explicit UC mapping requests were accepted. Effective cache type is unmeasured.
- Public grant signatures, fresh mapping coverage/currentness and full observer
  replay pass offline. This proves no host DMA payload visibility; Q7 stays open.
- R5 selected logs are byte-identical (15998 bytes); no allowed line was used.
  Owned process teardown passed; host PCI command was 0x0002, mastering off.
- S1 remains incomplete. Channel translation, PBDMA fetch, command submission
  and safe reuse/retire remain outside this result. No S2/S3 success claim.
- Raw captures are unchanged. tools/batch1_result.py is an offline verifier/report
  generator outside the reviewed launcher source set; it never launches or signs.
- Offline verifier fault injection on temporary copies rejects altered A7 and
  memory signatures, changed selected kernel evidence and a truncated observer
  line, while accepting the unchanged capture. See verifier-check.log.
