# A3 independent rework result

2026-10-16. Independently implemented; rejected branch and reviewer implementation were not read.

Log: 598 instructions, 560 executed, 38 skipped; 24 names.
Listing: 7 scripts, 2041 formatted listing rows; 1519 distinct listing offsets not logged.

Board operations by name:
- CONDITION_TIME: 9
- GPIO: 1
- GPIO_NE: 1
- IO: 1
- TIME: 8
- ZM_CR: 2
- ZM_I2C_BYTE: 2

Eight offset disagreements explained: offset zero is a repeat-loop trace; seven COPY_NV_REG starts have a byte-only first line and a named continuation at +16. ROM bytes and both pinned source paths confirm this. They are not missing scripts.

The prescribed listing-row count includes numeric table rows and one duplicate DONE. Early parser drafts wrongly counted only named opcodes, then mishandled byte-only wrapping and an unpadded non-script table; corrected to follow the decoder formatting, with regressions. These prescribed named-line comparison counts do not prove complete static reachability or bytecode boundaries. A4/A6 must use raw ROM plus dispatch/control-flow semantics, not this presentation-oriented listing parser.

Input/offset evidence: evidence.json. ROM and complete decoded text remain outside Git. Both --check runs pass; full repository check result is recorded in the parent ABC1 handoff.
Full make check passed after these corrections (build/tests/abc-a3-pass.log); all inventory fields agree with reviewer counts. The reviewer implementation was not read.
