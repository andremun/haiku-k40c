/* Copyright 2026 Mario Andres Munoz.
 * Distributed under the terms of the MIT License.
 * Open the fixed stage exactly once and retain descriptor 3 across exec.
 */
#include <OS.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <syscalls.h>
extern char **argv_save;
extern thread_id __main_thread_id;

/* runtime_loader calls entry(argc, argv, env). No constructors are needed.
 * Consulted Haiku start_dyn.c:31-46 and runtime_loader.cpp:770-771.
 */
int _start(int argc, char **argv, char **environment)
{
    (void)argc;
    argv_save = argv;
    __main_thread_id = find_thread(NULL);
    /* Raw syscall result avoids libc's errno translation of status_t.
     * Haiku syscalls.h:273-274 declares this interface.
     */
    int fd = _kern_open(-1, "/dev/misc/k40_a7_stage", O_RDWR, 0);
    printf("A7-OPEN-RESULT status=0x%08x\n", (unsigned)(fd < 0 ? fd : B_OK));
    fflush(stdout);
    if (fd < 0)
        return 1;
    if (fd != 3) {
        if (dup2(fd, 3) != 3)
            return 2;
        close(fd);
    }
    char *const args[] = {"/bin/sh", "/tmp/a7-session.sh", NULL};
    execve(args[0], args, environment);
    return 3;
}
