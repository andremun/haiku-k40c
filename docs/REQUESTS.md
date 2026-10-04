# Requests to the user

Actions the agent cannot do (root, installs, hardware). The agent adds
entries. The user marks them done.

| ID | Request | Why | Status |
|---|---|---|---|
| R1 | Install analysis tools: `sudo apt install ripgrep universal-ctags clang clangd bear` | Specification section 5. Only `grep` is available now. | open |
| R2 | Run `sudo scripts/capture_root.sh` (read-only PCI captures) | Full config space, capabilities, BAR and interrupt details need root. | open |
| R3 | Optional: `llm-mode.sh one`, then `sudo scripts/read_boot0.sh` (read-only, one register) | Closes open question Q1: the chipset that Nouveau would select. | open |
