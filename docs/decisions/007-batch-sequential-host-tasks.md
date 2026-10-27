# 007. Batch sequential host tasks while reviews are pending

Date: 2026-10-27. Status: accepted (direct user instruction in this chat).

## Decision

Continue the planned tasks in order. Related macro tasks may share a review batch.
Do not wait for a separate Claude review after each macro task while Claude is busy.
Keep each task's plan, findings, result, checks, and small commits on main.
Report the completed batch and its remaining review work.

## Limits

This changes review scheduling only. It grants no write-stage permission.
A7 and first-write C3 stages still need the user's go-ahead.
ADR 006 still requires approval after any launcher-reported stop.
No root, push, host binding change, or manual GPU reset is authorized.
