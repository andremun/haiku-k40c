/* Copyright 2026 Mario Andres Munoz.
 * Distributed under the terms of the MIT License.
 * Fixed one-open endpoint. No path or command is accepted from arguments.
 */
#include <OS.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>
#include <syscalls.h>
extern char **argv_save;
extern thread_id __main_thread_id;
#ifdef MEMORY_PREFLIGHT
#define NODE "/dev/misc/k40_mem_preflight"
#define SESSION "/tmp/mem-preflight-session.sh"
#define ROLE "preflight"
#else
#define NODE "/dev/misc/k40_mem_stage"
#define SESSION "/tmp/mem-session.sh"
#define ROLE "memory"
#endif
int _start(int argc,char **argv,char **environment)
{
    (void)argc;argv_save=argv;__main_thread_id=find_thread(NULL);
    const int fd=_kern_open(-1,NODE,O_RDWR,0);
    printf("MEM-OPEN-RESULT role=" ROLE " status=0x%08x\n",(unsigned)(fd<0?fd:B_OK));fflush(stdout);
    if(fd<0)return 1;
    if(fd!=3){if(dup2(fd,3)!=3)return 2;close(fd);}
    char *const args[]={"/bin/sh",SESSION,NULL};execve(args[0],args,environment);return 3;
}
