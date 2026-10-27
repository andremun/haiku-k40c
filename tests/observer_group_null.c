// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Read decoder fields from inert /dev/null calls. No VFIO device can be opened.
#include <errno.h>
#include <fcntl.h>
#include <linux/vfio.h>
#include <sys/ioctl.h>
#include <unistd.h>
int main(void)
{
    int fd=open("/dev/null",O_RDWR|O_CLOEXEC);
    if(fd<0)return 1;
    struct vfio_group_status status={.argsz=sizeof(status)};
    int ok=ioctl(fd,VFIO_GROUP_GET_STATUS,&status)==-1 && errno==ENOTTY;
    int attached=ioctl(fd,VFIO_GROUP_SET_CONTAINER,&fd);
    ok=(attached==-1 && errno==ENOTTY) && ok;
    int device=ioctl(fd,VFIO_GROUP_GET_DEVICE_FD,"0000:04:00.0");
    ok=(device==-1 && errno==ENOTTY) && ok;
    int detached=ioctl(fd,VFIO_GROUP_UNSET_CONTAINER);
    ok=(detached==-1 && errno==ENOTTY) && ok;
    return close(fd)==0 && ok?0:1;
}
