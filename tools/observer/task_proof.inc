/* Copyright 2026 Mario Andres Munoz.
 * Distributed under the terms of the MIT License.
 * Original syscall-stop proof. Reads proc status and compares kernel resources.
 * Never attaches a process, changes a file table or calls a device operation.
 */
#include <errno.h>
#include <linux/kcmp.h>
#include <stdio.h>
#include <sys/syscall.h>
#include <unistd.h>

static void
k40_task_proof(struct tcb *tcp)
{
    char path[64], line[256];
    int group = 0;
    long same = -1;
    snprintf(path, sizeof(path), "/proc/%d/status", tcp->pid);
    FILE *input = fopen(path, "re");
    if (input) {
        unsigned count = 0;
        while (count++ < 128 && fgets(line, sizeof(line), input)) {
            if (sscanf(line, "Tgid: %d", &group) == 1) break;
        }
        fclose(input);
    }
    if (group > 0)
        same = syscall(SYS_kcmp, group, tcp->pid, KCMP_FILES, 0UL, 0UL);
    tprintf("K40_TASK{tgid=%d, files=%ld} ", group, same);
}
