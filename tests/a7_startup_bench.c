/* Copyright 2026 Mario Andres Munoz.
 * Distributed under the terms of the MIT License.
 * Inert regular-file writes and gettid syscalls. No devices or guest.
 */
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
int main(int argc,char** argv)
{
    if(argc!=5)return 2;
    const unsigned total=(unsigned)strtoul(argv[2],NULL,10);
    const unsigned chunk=(unsigned)strtoul(argv[3],NULL,10);
    const unsigned extra=(unsigned)strtoul(argv[4],NULL,10);
    if(!total || total>100000 || !chunk || chunk>4096 || extra>2)return 3;
    int fd=open(argv[1],O_WRONLY|O_CREAT|O_EXCL,0600);if(fd<0)return 4;
    char bytes[4096];memset(bytes,'x',sizeof(bytes));
    struct timespec start,end;clock_gettime(CLOCK_MONOTONIC,&start);
    unsigned written=0,calls=0;
    while(written<total) {
        unsigned count=total-written;if(count>chunk)count=chunk;
        if(write(fd,bytes,count)!=(ssize_t)count)return 5;
        for(unsigned i=0;i<extra;++i)(void)syscall(SYS_gettid);
        written+=count;++calls;
    }
    clock_gettime(CLOCK_MONOTONIC,&end);close(fd);
    double elapsed=(end.tv_sec-start.tv_sec)+(end.tv_nsec-start.tv_nsec)/1e9;
    printf("%.9f %u %u\n",elapsed,calls,calls*extra);return 0;
}
