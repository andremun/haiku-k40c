# Requests to the user

Actions the agent cannot do (root, installs, hardware). The agent adds
entries. The user marks them done.

| ID | Request | Why | Status |
|---|---|---|---|
| R1 | Install analysis tools: `sudo apt install ripgrep universal-ctags clang clangd bear` | Specification section 5. Only `grep` is available now. | done 2026-10-05 |
| R2 | Run `sudo scripts/capture_root.sh` (read-only PCI captures) | Full config space, capabilities, BAR and interrupt details need root. | done 2026-10-05 |
| R3 | Optional: `llm-mode.sh one`, then `sudo scripts/read_boot0.sh` (read-only, one register) | Closes open question Q1: the chipset that Nouveau would select. | done 2026-10-05 |
| R4 | Run `sudo scripts/capture_root.sh` again | The run of 2026-10-07 used the old address list. It covers both K40c, but not the K600 at 82:00.0, and `iomem.txt` and `dmesg-gpu.txt` used the old pattern. | open |
