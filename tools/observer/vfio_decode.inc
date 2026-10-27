/* Copyright 2026 Mario Andres Munoz.
 * Distributed under the terms of the MIT License.
 * Original narrow Type1 observation decoder for the pinned strace build.
 * No mapping call is issued here. Unsupported payloads remain opaque.
 */
#include <linux/vfio.h>

static int
k40_vfio_decode(struct tcb *tcp, unsigned int code, kernel_ulong_t arg)
{
    if (code == VFIO_SET_IOMMU) {
        tprint_arg_next();
        tprintf("K40_SETUP{%llu}", (unsigned long long)arg);
        return RVAL_IOCTL_DECODED;
    }
    if (code == VFIO_IOMMU_MAP_DMA) {
        struct vfio_iommu_type1_dma_map map;
        tprint_arg_next();
        if (umove_or_printaddr(tcp, arg, &map))
            return RVAL_IOCTL_DECODED;
        tprintf("K40_MAP{argsz=%u, flags=%#x, hva=%#llx, iova=%#llx, size=%#llx}",
                map.argsz, map.flags, (unsigned long long)map.vaddr,
                (unsigned long long)map.iova, (unsigned long long)map.size);
        return RVAL_IOCTL_DECODED;
    }
    if (code == VFIO_IOMMU_UNMAP_DMA) {
        struct vfio_iommu_type1_dma_unmap unmap;
        if (entering(tcp)) {
            tprint_arg_next();
            if (umove_or_printaddr(tcp, arg, &unmap))
                return RVAL_IOCTL_DECODED;
            tprintf("K40_UNMAP{argsz=%u, flags=%#x, iova=%#llx, size=%#llx",
                    unmap.argsz, unmap.flags, (unsigned long long)unmap.iova,
                    (unsigned long long)unmap.size);
            return 0; /* Continue on syscall exit to capture the returned size. */
        }
        if (syserror(tcp))
            tprints(", returned=error}");
        else if (umove(tcp, arg, &unmap))
            tprints(", returned=unreadable}");
        else
            tprintf(", returned=%#llx}", (unsigned long long)unmap.size);
        return RVAL_IOCTL_DECODED;
    }
    return 0;
}
