# 002. Restore the pinned reference sources from this repository

Date: 2026-10-23. Status: accepted (alignment plan decision D7).

## Context

`reference/*` are symbolic links into `~/llm-server/agent-refs/`, a folder that the
`llm-server` repository ignores. This repository cannot check its own sources without
that folder.

## Decision

`tools/restore_verification_refs.py` becomes the way to get the pinned sources. It
fetches each source at the commit in `reference/MANIFEST.md` into a folder outside Git
and checks it. The link target becomes a setting (`K40_REFS`), with
`~/llm-server/agent-refs` as the default for the T7610.

## Consequences

Phase 2 work. `make check` on a new machine needs one restore step first.
