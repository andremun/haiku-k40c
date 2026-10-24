# shellcheck shell=bash
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
# Checks for the scripts that run as root (sudo). Sourced, not run.
# The agents edit this repository with the account of the user. So root runs
# only files that are equal to origin/main (merged through a pull request),
# git runs as the user (hooks and core.fsmonitor are user code), and root
# never writes into the repository: root_guard_save copies as the user.
ROOT_GUARD_REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)
# Files that a root script runs or sources.
ROOT_GUARD_PATHS=(scripts tools/guest/config.sh)

root_guard_die() { echo "ERROR: $*" >&2; exit 1; }

# Stop unless sudo was run from a user account (SUDO_USER). Root itself is refused.
root_guard_user() {
    [[ -n ${SUDO_USER:-} && ${SUDO_USER} != root ]] || root_guard_die "run with sudo from your own account, not as root"
}

# git as the user, with hooks and fsmonitor off.
root_guard_git() {
    runuser -u "${SUDO_USER}" -- git -C "${ROOT_GUARD_REPO}" \
        -c core.fsmonitor=false -c core.hooksPath=/dev/null "$@"
}

# Stop unless the root-run files are equal to origin/main. Does nothing without root.
root_guard_check() {
    [[ ${EUID} -eq 0 ]] || return 0
    root_guard_user
    local changed
    changed=$(root_guard_git status --porcelain --untracked-files=all -- "${ROOT_GUARD_PATHS[@]}") \
        || root_guard_die "git status failed in ${ROOT_GUARD_REPO}"
    [[ -z ${changed} ]] || root_guard_die "uncommitted changes in files that run as root:
${changed}
Commit them through a pull request, or remove them, then run again."
    root_guard_git diff --quiet origin/main -- "${ROOT_GUARD_PATHS[@]}" \
        || root_guard_die "the files that run as root differ from origin/main.
See: git diff origin/main -- ${ROOT_GUARD_PATHS[*]}
Merge the change through a pull request and pull, or run git fetch, then run again."
    echo "Root-run files are equal to origin/main ($(root_guard_git rev-parse --short origin/main))."
}

# Stop unless $1 is a full PCI address (domain:bus:slot.function).
root_guard_bdf() {
    [[ $1 =~ ^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]$ ]] || root_guard_die "not a PCI address: '$1'"
}

# Copy FILE... into the repository folder DEST (relative to the repository) as the user.
root_guard_save() {
    local dest=$1 file
    shift
    root_guard_user
    runuser -u "${SUDO_USER}" -- mkdir -p -- "${ROOT_GUARD_REPO}/${dest}"
    for file in "$@"; do
        runuser -u "${SUDO_USER}" -- sh -c 'cat > "$1"' sh "${ROOT_GUARD_REPO}/${dest}/$(basename "${file}")" < "${file}" \
            || root_guard_die "could not write ${dest}/$(basename "${file}")"
    done
}
