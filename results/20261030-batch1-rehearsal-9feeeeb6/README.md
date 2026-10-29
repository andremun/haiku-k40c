# Combined cardless rehearsal

PASS_CARDLESS_NO_CARD. 

The exact combined installer and binaries run without VFIO, grant keys or
grants. Expected outcomes: G0 and memory open return B_ENTRY_NOT_FOUND
(0x80006003); original A7 open returns its unchanged B_ERROR (0xffffffff).
All artifacts require size/SHA-256 and same-inode moves from unwatched staging.
Final-name-only driver loads and resident Failed state through reload are checked.
This is Haiku installation/lifetime evidence only, not K40c/UC/VRAM/MMU evidence.
