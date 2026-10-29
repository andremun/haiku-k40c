# Plan

1. Serialize gk104 17/12 VRAM PTE/SPT/PDE and instance fields in freestanding
   bounded encoders, with independent decoding tests and address-role checks.
2. Build tables through the owned slow window, select mode 17, invalidate only
   the owned PDB, then enable BAR1 at 0x1704 with the sourced two-flush wait.
3. Verify A/B, remap VA0 to B, invalidate and verify B/B, restore A/B and verify;
   disable only the owned context on success, retain on any uncertain failure.
4. Test order, masks, bounds, stale translations, poll/clock faults and partial
   enable/disable. Native build and reports/checks, no VM/card.
