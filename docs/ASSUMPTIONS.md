# Assumptions

| ID | Assumption | Why | Revisit when |
|---|---|---|---|
| S1 | Development targets the K40c at `0000:04:00.0`. The card at `0000:03:00.0` stays in reserve (it was at `0000:81:00.0` until 2026-10-07). | Specification section 3. | Hardware experiments start. |
| S2 | The Quadro K600 at `0000:82:00.0` (at `0000:03:00.0` until 2026-10-07) stays the display adapter. | Specification section 3. | Never, for phase 1. |
