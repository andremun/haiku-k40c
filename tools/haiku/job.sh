#!/bin/sh
# Copyright (c) 2026 Mario Andres Munoz
# Distributed under the terms of the MIT License. See LICENSE.
#
# Run one shell job in the persistent cardless Haiku guest and wait for its result.
# Usage: job.sh FRESH_NUMBER 'shell commands' [wait_timeout_s]
# Inputs: the work folder $HAIKU_JOB_ROOT (default: the current folder). The request
# goes to <root>/share/jobN.sh, which the guest job loop reads through the transfer
# server. The result arrives in <root>/logs/jobN.out. Its last line is "exit=N".
# A wait timeout does not cancel the guest job.
# Merged on 2026-10-23 from opencode-haiku tools/job.sh (alignment plan decision D4).
set -eu
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then echo 'Usage: job.sh N COMMANDS [TIMEOUT]' >&2; exit 2; fi
R=${HAIKU_JOB_ROOT:-$(pwd)}
N=$1
T=${3:-300}
for value in "$N" "$T"; do
 case "$value" in ''|*[!0-9]*|0|0*) echo 'Job number and timeout must be canonical positive integers.' >&2; exit 2;; esac
done
mkdir -p "$R/share" "$R/logs"
request=$R/share/job$N.sh
result=$R/logs/job$N.out
if [ -e "$request" ] || [ -e "$result" ]; then echo 'Job number already used; choose a fresh number.' >&2; exit 2; fi
pending=$(mktemp "$R/share/.job$N.XXXXXX")
trap 'rm -f "$pending"' EXIT HUP INT TERM
printf '%s\n' "$2" > "$pending"
mv "$pending" "$request"
i=0
while [ ! -f "$result" ]; do
 if [ "$i" -ge "$T" ]; then echo 'TIMEOUT waiting for result; guest execution has not been cancelled.' >&2; exit 124; fi
 sleep 1
 i=$((i+1))
done
cat "$result"
last=$(tail -n 1 "$result")
case "$last" in exit=*) rc=${last#exit=};; *) echo 'Missing guest exit status.' >&2; exit 125;; esac
case "$rc" in ''|*[!0-9]*) echo 'Invalid guest exit status.' >&2; exit 125;; esac
if [ "$rc" -gt 255 ]; then echo 'Invalid guest exit status.' >&2; exit 125; fi
exit "$rc"
