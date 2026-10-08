# B6 REWORK 2 Plan

## Defects from second review

1. Add `"gk110": true/false` to every setup and launch entry (from `gk110_active`)
2. Build the MD other-chip table from `gk110` false entries instead of hand-written rows
3. Add line number to `class_source`

## Steps

1. In `extract_methods_with_branch_filter`: capture condition strings in cond_stack,
   add `"gk110"` and `"condition"` to each method entry.
2. In `clean_method`: include `"gk110"`, drop unused keys.
3. Fix `class_source` to include line number (209).
4. Update `build_md`: filter GK110 entries in sequence tables, build other-chip
   table from `gk110` false entries.
5. `make check`, handoff, stop.
