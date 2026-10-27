# Requests to the user

Actions the agent cannot do (root, installs, hardware). The agent adds
entries. The user marks them done.

The root scripts (`capture_root.sh`, `read_boot0.sh`, `passthrough.sh`)
stop unless `scripts/` and `tools/guest/config.sh` are equal to
`origin/main`. So a change to them must be merged through a pull request
before it runs as root. Root writes no file in the repository: your
account copies the results (`scripts/root-guard.sh`).

| ID | Request | Why | Status |
|---|---|---|---|
| R1 | Install analysis tools: `sudo apt install ripgrep universal-ctags clang clangd bear` | Specification section 5. Only `grep` is available now. | done 2026-10-05 |
| R2 | Run `sudo scripts/capture_root.sh` (read-only PCI captures) | Full config space, capabilities, BAR and interrupt details need root. | done 2026-10-05 |
| R3 | Optional: `llm-mode.sh one`, then `sudo scripts/read_boot0.sh` (read-only, one register) | Closes open question Q1: the chipset that Nouveau would select. | done 2026-10-05 |
| R4 | Run `sudo scripts/capture_root.sh` again | The run of 2026-10-07 used the old address list. It covers both K40c, but not the K600 at 82:00.0, and `iomem.txt` and `dmesg-gpu.txt` used the old pattern. | done 2026-10-07 |
| R5 | In a separate terminal, run `sudo journalctl -k -b -f --no-pager --output=short-monotonic > /tmp/k40-s1-kernel.log` and tell Codex when it is running. Leave it running for the S1 hardware stages. This reads the current boot kernel journal and streams future entries to a user-owned file. | The account cannot read the system kernel journal. D0 and later physical stages require IOMMU/VFIO fault baselines and monitoring. The agent cannot use root. | requested 2026-10-27; host package work continues |
