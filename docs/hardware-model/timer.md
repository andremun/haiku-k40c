# timer: Hardware Model

## Purpose
PTIMER provides a hardware clock counter used by nvkm_msec for every wait and delay across all subsystems. It configures a frequency from the crystal clock via write registers, reads a 64-bit counter with a double-read loop to avoid torn values, and provides alarm interrupts when the counter matches a programmed value.

## Nouveau files

- Constructor: **nv41_timer_new** (`nvkm/subdev/timer/nv41.c:82`)
- Function table: **nv41_timer** (`nvkm/subdev/timer/nv41.c:72`)

## Members

| Member | Function | Role | Needed | Registers |
|--------|----------|------|--------|-----------|
| init | nv41_timer_init | init | True | 0 |
| intr | nv04_timer_intr | interrupt | False | 0 |
| read | nv04_timer_read | runtime | True | 0 |
| time | nv04_timer_time | runtime | False | 0 |
| alarm_init | nv04_timer_alarm_init | runtime | False | 0 |
| alarm_fini | nv04_timer_alarm_fini | teardown | False | 0 |

## Dependencies
(none identified)

## KNOWN

- **init**: Calculates frequency dividers from the crystal clock and writes the multiplier, numerator and denominator registers to configure the timer to 31.25 MHz (`nvkm/subdev/timer/nv41.c:28`)
- **intr**: Reads the interrupt status register and acknowledges the alarm interrupt bit then triggers the alarm handler if set (`nvkm/subdev/timer/nv04.c:72`)
- **read**: Reads the 64-bit timer counter from two 32-bit registers in a retry loop to avoid torn reads and returns the combined value (`nvkm/subdev/timer/nv04.c:43`)
- **time**: Writes a 64-bit time value split into high and low 32-bit parts to two hardware registers to compare or set the timer (`nvkm/subdev/timer/nv04.c:28`)
- **alarm_init**: Writes a target time value to the alarm register and enables the alarm interrupt bit in the interrupt enable register (`nvkm/subdev/timer/nv04.c:64`)
- **alarm_fini**: Writes zero to the interrupt enable register to disable all timer alarm interrupts (`nvkm/subdev/timer/nv04.c:57`)

## INFERRED

(none)

## UNKNOWN

(none)
