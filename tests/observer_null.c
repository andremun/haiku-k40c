// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Inert owned-child fixture. This program can open only /dev/null, never VFIO.
#include <errno.h>
#include <fcntl.h>
#include <linux/vfio.h>
#include <stdint.h>
#include <sys/ioctl.h>
#include <unistd.h>
int main(void)
{
    int fd=open("/dev/null",O_RDWR|O_CLOEXEC);
    if(fd<0)return 1;
    struct vfio_iommu_type1_dma_map map={.argsz=sizeof(map),
        .flags=VFIO_DMA_MAP_FLAG_READ|VFIO_DMA_MAP_FLAG_WRITE,
        .vaddr=UINT64_C(0x100000),.iova=UINT64_C(0x1000),.size=UINT64_C(0x2000)};
    struct vfio_iommu_type1_dma_unmap unmap={.argsz=sizeof(unmap),
        .iova=UINT64_C(0x1000),.size=UINT64_C(0x2000)};
    int ok=ioctl(fd,VFIO_SET_IOMMU,VFIO_TYPE1v2_IOMMU)==-1 && errno==ENOTTY;
    ok=ok && ioctl(fd,VFIO_IOMMU_MAP_DMA,&map)==-1 && errno==ENOTTY;
    ok=ok && ioctl(fd,VFIO_IOMMU_UNMAP_DMA,&unmap)==-1 && errno==ENOTTY;
    return close(fd)==0 && ok?0:1;
}
