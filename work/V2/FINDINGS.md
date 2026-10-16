# V2 findings

2026-10-16. All work offline/cardless; no reviewer implementation opened.

- Restored all five exact source pins through original symlink targets. Existing
  source contents and reference links/pins were not changed. Acquisition was
  public read-only Git fetch/checkout; caches remain outside the project Git.
- Installed isolated PyYAML 6.0.2 and diagnostic pytest 8.3.5. With sources,
  repository checker reports zero failures; D4 and R1 positive-input tests pass.
- Found existing pytest suppression: conftest discarded collected items and
  forced exit zero. A deliberate assertion failure exited 0. Removed those
  hooks/config and redundant pytest recipe. Standalone tests are the actual
  test entry point; they all pass. Same pytest negative control now exits 1.
- Built pinned nvbios manually from its upstream library source lists, using
  extracted bison/flex/m4 packages without sudo or installation. Upstream sources
  remain unchanged. Repeatable builder and input checker added.
- Fresh full decode equals saved mediaflux output byte for byte (SHA-256
  dce802b40173ececd2df0217e9e3adbb816614a64d7c0b0f1d00ad26646df0bf).
  Script-only decode: 2742 stdout lines; seven main-script pointers reported.
  This is not the reachable-instruction inventory or an A3 acceptance result.
- Generic BIT parser warnings coexist with a separate manual initialization
  pointer/script path (nvbios.c:1100-1123,1282-1318). Reproducing the output does
  not prove listing completeness, runtime branch coverage or helper semantics.
- All source gates and ROM identity now pass the offline inventory. Native
  cross compiler/header/kernel inputs are still absent; no ABI/VM claims made.
