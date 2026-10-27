# 006. Ask before another run after a launcher stop

Date: 2026-10-27. Status: accepted (user-supplied Claude S1B5 review).

## Decision

After a launcher reports a stop, report the result and ask the user before
another run. This includes stops later attributed to a host-parser false alarm.
Host-only diagnosis and regression tests may continue while approval is pending.
Do not rewrite the stopped run's original evidence.

## Context

The first B5 attempt stopped on a normal Haiku banner misclassified as panic.
The host parser was corrected, and the next read-only attempt passed.
Claude accepted S1B5 but asked for an explicit user decision before future retries.

## Unchanged limits

Actual hangs and panics still require a stop without a modified retry.
Write stages still require the user's go-ahead. ADR 005's first-run read-only
permission does not authorize another run after a reported stop.
