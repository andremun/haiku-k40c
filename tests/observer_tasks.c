/* Copyright 2026 Mario Andres Munoz.
 * Distributed under the terms of the MIT License.
 * Owned host-only task fixture. Its only ioctl target is /dev/null.
 */
#define _GNU_SOURCE
#include <fcntl.h>
#include <sched.h>
#include <linux/vfio.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>
static int fd;
static int done;
static unsigned char stack[65536] __attribute__((aligned(16)));
static void *worker(void *unused)
{
    (void)unused;
    ioctl(fd, VFIO_SET_IOMMU, VFIO_TYPE1v2_IOMMU);
    return NULL;
}
static int private_worker(void *unused)
{
    worker(unused);
    __atomic_store_n(&done, 1, __ATOMIC_RELEASE);
    return 0;
}
int main(int argc, char **argv)
{
    sleep(1);
    fd = open("/dev/null", O_RDWR);
    if (fd < 0) return 2;
    printf("fixture pid=%ld\n", (long)getpid()); fflush(stdout);
    if (argc == 2 && !strcmp(argv[1], "guard")) {
        unshare(CLONE_FILES);
        syscall(SYS_close_range, 10000U, 10000U, 0U);
        worker(NULL);
    } else if (argc == 2 && !strcmp(argv[1], "fork")) {
        pid_t child = fork();
        if (child == 0) {worker(NULL); _exit(0);}
        if (child < 0 || waitpid(child, NULL, 0) < 0) return 3;
    } else if (argc == 2 && !strcmp(argv[1], "private")) {
        if (clone(private_worker, stack + sizeof(stack),
            CLONE_VM | CLONE_SIGHAND | CLONE_THREAD, NULL) < 0) return 6;
        while (!__atomic_load_n(&done, __ATOMIC_ACQUIRE)) sched_yield();
    } else {
        pthread_t thread;
        if (pthread_create(&thread, NULL, worker, NULL)) return 4;
        if (pthread_join(thread, NULL)) return 5;
    }
    close(fd);
    return 0;
}
