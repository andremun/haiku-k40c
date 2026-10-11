#!/usr/bin/env python3
"""Extract Linux dependency symbols from Nouveau source files listed in
analysis/files.json and classify them for Haiku driver replacement.

Outputs analysis/linux_deps.json: a list sorted by symbol, one entry for each
Linux symbol found in the 70 non-other-chip files.

--check  writes nothing and exits 0 when the JSON file is exactly what
the tool generates, else 1.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NV = os.path.join(ROOT, "reference", "nouveau")
HAIKU = os.path.join(ROOT, "reference", "haiku")
FILES_JSON = os.path.join(ROOT, "analysis", "files.json")
OUTPUT = os.path.join(ROOT, "analysis", "linux_deps.json")

C_KEYWORDS = frozenset(
    "if for while switch return sizeof defined do else case "
    "typeof __typeof__ offsetof".split()
)


def load_files():
    """Return entries from files.json that are not other-chip."""
    files = json.load(open(FILES_JSON))
    return [f for f in files if f["class"] != "other-chip"]


def collect_defined_names():
    """Collect all Nouveau-defined function and macro names from all .c/.h files."""
    defined = set()
    for d, _, fs in os.walk(NV, followlinks=True):
        for f in fs:
            if f.endswith((".c", ".h")):
                text = open(os.path.join(d, f), errors="replace").read()
                defined |= set(re.findall(r"^(\w+)\s*\(", text, re.M))
                defined |= set(re.findall(r"^#\s*define\s+(\w+)", text, re.M))
    return defined


def extract_calls(files):
    """For each file, strip comments, find function-call-like identifiers.
    Returns {symbol: count} and {symbol: set of (file, line)}."""
    defined = collect_defined_names()
    counts = {}
    locations = {}
    for entry in files:
        path = os.path.join(NV, entry["path"])
        try:
            text = open(path, errors="replace").read()
        except OSError:
            continue
        # Strip block comments preserving line count
        text = re.sub(
            r"/\*.*?\*/",
            lambda m: "\n" * m.group(0).count("\n"),
            text,
            flags=re.S,
        )
        for m in re.finditer(r"(?<![\w.>])([A-Za-z_]\w*)\s*\(", text):
            name = m.group(1)
            if name in C_KEYWORDS or name in defined:
                continue
            counts[name] = counts.get(name, 0) + 1
            line = text.count("\n", 0, m.start()) + 1
            locations.setdefault(name, set()).add((entry["path"], line))
    return counts, locations


# ---------------------------------------------------------------------------
# Classification map: symbol -> {category, haiku_api, header, note}
# ---------------------------------------------------------------------------

CLASSIFY = {
    # --- Memory allocation (C-replace) ---
    "kzalloc": {
        "category": "C-replace", "haiku_api": ["calloc"],
        "header": None,
        "note": "kzalloc allocates kernel memory zeroed. Haiku calloc allocates and zeroes; kmalloc does not zero."
    },
    "kmalloc": {
        "category": "C-replace", "haiku_api": ["malloc"],
        "header": None,
        "note": "kmalloc allocates kernel memory without zeroing. Haiku malloc has the same semantics."
    },
    "kfree": {
        "category": "C-replace", "haiku_api": ["free"],
        "header": None,
        "note": "kfree releases memory previously allocated by kmalloc or kzalloc. Haiku free handles both."
    },
    "kvmalloc": {
        "category": "C-replace", "haiku_api": ["malloc"],
        "header": None,
        "note": "kvmalloc allocates virtually contiguous memory, falling back to page allocations. Haiku has no direct equivalent."
    },
    "kvmalloc_array": {
        "category": "C-replace", "haiku_api": ["malloc"],
        "header": None,
        "note": "kvmalloc_array allocates an array with overflow check. Haiku malloc needs manual overflow check."
    },
    "kvcalloc": {
        "category": "C-replace", "haiku_api": ["calloc"],
        "header": None,
        "note": "kvcalloc allocates zeroed virtually contiguous memory for arrays. Haiku calloc does not zero page-sized blocks."
    },
    "vfree": {
        "category": "C-replace", "haiku_api": ["free"],
        "header": None,
        "note": "vfree releases memory allocated by kvmalloc or vmap. Haiku free handles standard allocations but not vmapped regions."
    },
    "kvfree": {
        "category": "C-replace", "haiku_api": ["free"],
        "header": None,
        "note": "kvfree releases memory from kmalloc or kvmalloc. Haiku free handles both but cannot distinguish allocation type."
    },
    "kvzalloc": {
        "category": "C-replace", "haiku_api": ["calloc"],
        "header": None,
        "note": "kvzalloc allocates zeroed virtually contiguous memory. Haiku has no direct equivalent for zeroed virtual allocation."
    },
    "struct_size": {
        "category": "C-replace", "haiku_api": ["malloc"],
        "header": None,
        "note": "struct_size computes size of struct with flexible array member with overflow check."
    },
    "kmemdup": {
        "category": "C-replace", "haiku_api": ["malloc", "memcpy"],
        "header": None,
        "note": "kmemdup allocates and copies a memory region in one call. Haiku needs malloc then memcpy separately."
    },
    "alloc_page": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "alloc_page allocates a single kernel page. Haiku needs a page-level allocator, no direct equivalent."
    },
    "__free_page": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "__free_page releases a single kernel page. Haiku has no page allocator in this driver context."
    },
    "vmap": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "vmap maps page frames into contiguous virtual address space. Haiku has no equivalent; driver must design its own mapping."
    },
    "vunmap": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "vunmap releases virtual mapping created by vmap. Haiku needs matching unmap for vmapped regions."
    },
    "memcpy_toio": {
        "category": "C-replace", "haiku_api": ["memcpy"],
        "header": None,
        "note": "memcpy_toio copies to MMIO address space. Haiku memcpy works on both; IO memory access may need special barriers."
    },
    "memcpy_fromio": {
        "category": "C-replace", "haiku_api": ["memcpy"],
        "header": None,
        "note": "memcpy_fromio copies from MMIO address space. Haiku memcpy works on both; IO memory access may need special barriers."
    },
    "memset_io": {
        "category": "C-replace", "haiku_api": ["memset"],
        "header": None,
        "note": "memset_io sets MMIO address space to a value. Haiku memset works on both but IO barriers may be needed."
    },

    # --- Locking (C-replace) ---
    "mutex_lock": {
        "category": "C-replace", "haiku_api": ["mutex_lock"],
        "header": "headers/private/kernel/lock.h",
        "note": "mutex_lock acquires a mutex, sleeping if necessary. Haiku mutex_lock also sleeps and returns status code."
    },
    "mutex_unlock": {
        "category": "C-replace", "haiku_api": ["mutex_unlock"],
        "header": "headers/private/kernel/lock.h",
        "note": "mutex_unlock releases a mutex. Haiku mutex_unlock has the same semantics."
    },
    "mutex_init": {
        "category": "C-replace", "haiku_api": ["mutex_init"],
        "header": "headers/private/kernel/lock.h",
        "note": "mutex_init initializes an unlocked mutex with a name. Haiku mutex_init takes a name parameter for debugging."
    },
    "mutex_destroy": {
        "category": "C-replace", "haiku_api": ["mutex_destroy"],
        "header": "headers/private/kernel/lock.h",
        "note": "mutex_destroy releases resources held by a mutex after use. Haiku mutex_destroy has the same API."
    },
    "mutex_is_locked": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "mutex_is_locked checks if a mutex is held. Haiku has no public mutex state query; this is a debug assertion."
    },
    "spin_lock": {
        "category": "C-replace", "haiku_api": ["acquire_spinlock"],
        "header": "headers/os/drivers/KernelExport.h",
        "note": "spin_lock acquires a spinlock, busy-waiting. Haiku acquire_spinlock has the same semantics without interrupt disable."
    },
    "spin_unlock": {
        "category": "C-replace", "haiku_api": ["release_spinlock"],
        "header": "headers/os/drivers/KernelExport.h",
        "note": "spin_unlock releases a spinlock. Haiku release_spinlock has the same semantics."
    },
    "spin_lock_irqsave": {
        "category": "C-replace", "haiku_api": ["acquire_spinlock", "disable_interrupts"],
        "header": "headers/os/drivers/KernelExport.h",
        "note": "spin_lock_irqsave acquires spinlock and disables interrupts. Haiku requires disable_interrupts then acquire_spinlock."
    },
    "spin_unlock_irqrestore": {
        "category": "C-replace", "haiku_api": ["release_spinlock", "restore_interrupts"],
        "header": "headers/os/drivers/KernelExport.h",
        "note": "spin_unlock_irqrestore releases spinlock and restores interrupt state. Haiku restore_interrupts replaces enable_interrupts."
    },
    "spin_lock_irq": {
        "category": "C-replace", "haiku_api": ["acquire_spinlock", "disable_interrupts"],
        "header": "headers/os/drivers/KernelExport.h",
        "note": "spin_lock_irq acquires spinlock and disables interrupts. Haiku needs disable_interrupts then acquire_spinlock."
    },
    "spin_unlock_irq": {
        "category": "C-replace", "haiku_api": ["release_spinlock", "restore_interrupts"],
        "header": "headers/os/drivers/KernelExport.h",
        "note": "spin_unlock_irq releases spinlock and enables interrupts. Haiku restore_interrupts replaces enable_interrupts."
    },
    "spin_lock_init": {
        "category": "C-replace", "haiku_api": ["B_INITIALIZE_SPINLOCK", "B_SPINLOCK_INITIALIZER"],
        "header": "headers/os/drivers/KernelExport.h",
        "note": "spin_lock_init initializes a spinlock to unlocked state. Haiku uses B_INITIALIZE_SPINLOCK or B_SPINLOCK_INITIALIZER."
    },

    # --- List operations ---
    "INIT_LIST_HEAD": {
        "category": "C-replace", "haiku_api": ["list_init"],
        "header": "headers/private/kernel/util/list.h",
        "note": "INIT_LIST_HEAD initializes a doubly-linked list head. Haiku list_init has the same semantics."
    },
    "list_add_tail": {
        "category": "C-replace", "haiku_api": ["list_add_link_to_tail"],
        "header": "headers/private/kernel/util/list.h",
        "note": "list_add_tail adds an element to the tail of a list. Haiku list_add_link_to_tail adds to tail of struct list."
    },
    "list_add": {
        "category": "C-replace", "haiku_api": ["list_add_link_to_head"],
        "header": "headers/private/kernel/util/list.h",
        "note": "list_add adds an element to the head of a list. Haiku list_add_link_to_head adds to head of struct list."
    },
    "list_del": {
        "category": "C-replace", "haiku_api": ["list_remove_link"],
        "header": "headers/private/kernel/util/list.h",
        "note": "list_del removes an element from a list. Haiku list_remove_link removes a link from a list."
    },
    "list_del_init": {
        "category": "C-replace", "haiku_api": ["list_remove_link", "list_init"],
        "header": "headers/private/kernel/util/list.h",
        "note": "list_del_init removes and reinitializes a list entry. Haiku uses list_remove_link then list_init."
    },
    "list_for_each_entry": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "list_for_each_entry is a container_of-based loop macro. Haiku needs manual iteration with list traversal."
    },
    "list_for_each_entry_safe": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "list_for_each_entry_safe allows deleting entries during iteration. Haiku needs manual temp pointer."
    },
    "list_first_entry_or_null": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "list_first_entry_or_null returns the first entry or NULL. Haiku needs manual empty check then first element."
    },
    "list_first_entry": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "list_first_entry returns the first entry of a list. Haiku needs manual iteration for first element."
    },
    "list_last_entry": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "list_last_entry returns the last entry of a list. Haiku struct list has no tail pointer; linear scan needed."
    },
    "list_move_tail": {
        "category": "C-replace", "haiku_api": ["list_move_to_list"],
        "header": "headers/private/kernel/util/list.h",
        "note": "list_move_tail moves all entries from one list to another. Haiku list_move_to_list transfers items between lists."
    },
    "list_empty": {
        "category": "C-replace", "haiku_api": ["list_is_empty"],
        "header": "headers/private/kernel/util/list.h",
        "note": "list_empty checks if a list has no entries. Haiku list_is_empty has the same semantics."
    },
    "list_entry": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "list_entry is a container_of macro to get struct from list member. Haiku needs manual offset computation."
    },

    # --- Red-black tree (A-reimplement) ---
    "rb_entry": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "rb_entry is a container_of macro for rb_node embedded in a struct. Haiku needs manual offset computation."
    },
    "rb_erase": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "rb_erase removes a node from a red-black tree. Haiku has no built-in RB-tree; must implement or use another structure."
    },
    "rb_link_node": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "rb_link_node links a node into a parent tree. Haiku needs RB-tree implementation."
    },
    "rb_insert_color": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "rb_insert_color rebalances the RB-tree after insertion. Haiku needs full RB-tree implementation."
    },
    "rb_first": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "rb_first returns the leftmost (smallest) node. Haiku needs RB-tree implementation."
    },
    "rb_next": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "rb_next returns the next node in in-order traversal. Haiku needs RB-tree implementation."
    },

    # --- Atomics (C-replace where possible) ---
    "atomic_set": {
        "category": "C-replace", "haiku_api": ["atomic_set"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "atomic_set assigns a value to an atomic variable. Haiku atomic_set uses inline functions."
    },
    "atomic_read": {
        "category": "C-replace", "haiku_api": ["atomic_get"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "atomic_read returns the value of an atomic variable. Haiku atomic_get provides the same semantics."
    },
    "atomic_inc": {
        "category": "C-replace", "haiku_api": ["atomic_add"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "atomic_inc atomically increments by one. Haiku has no atomic_inc; use atomic_add with +1."
    },
    "atomic_dec": {
        "category": "C-replace", "haiku_api": ["atomic_add"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "atomic_dec atomically decrements by one. Haiku has no atomic_dec; use atomic_add with -1."
    },
    "atomic_inc_return": {
        "category": "C-replace", "haiku_api": ["atomic_add"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "atomic_inc_return increments and returns the new value. Haiku atomic_add returns the old value; compute new from old."
    },
    "atomic_dec_and_test": {
        "category": "C-replace", "haiku_api": ["atomic_add"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "atomic_dec_and_test decrements and tests for zero. Haiku atomic_add returns the old value; check if old was one."
    },
    "atomic_xchg": {
        "category": "C-replace", "haiku_api": ["atomic_get_and_set"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "atomic_xchg atomically exchanges a value and returns the old one. Haiku atomic_get_and_set provides the same functionality."
    },
    "atomic_cmpxchg": {
        "category": "C-replace", "haiku_api": ["atomic_test_and_set"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "atomic_cmpxchg atomically compares and swaps. Haiku atomic_test_and_set provides compare-and-swap semantics."
    },

    # --- Reference counts ---
    "refcount_set": {
        "category": "C-replace", "haiku_api": ["atomic_set"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "refcount_set initializes a reference count. Haiku atomic_set works the same; refcount has no overflow check."
    },
    "refcount_inc": {
        "category": "C-replace", "haiku_api": ["atomic_add"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "refcount_inc increments a reference count with overflow check. Haiku atomic_add does not overflow-check."
    },
    "refcount_dec_and_test": {
        "category": "C-replace", "haiku_api": ["atomic_add"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "refcount_dec_and_test decrements and tests zero with overflow check. Haiku atomic_add does the decrement."
    },
    "refcount_inc_not_zero": {
        "category": "C-replace", "haiku_api": ["atomic_test_and_set"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "refcount_inc_not_zero increments only if non-zero. Haiku needs atomic_test_and_set loop for this pattern."
    },
    "refcount_dec_and_mutex_lock": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "refcount_dec_and_mutex_lock decrements and acquires a mutex when count reaches zero. Haiku needs manual implementation."
    },
    "kref_put": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "kref_put decrements a kref and calls the release callback when it reaches zero. Haiku needs manual refcount + callback pattern."
    },
    "kref_get": {
        "category": "C-replace", "haiku_api": ["atomic_add"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "kref_get atomically increments a kref reference count. Haiku atomic_add does the same increment."
    },
    "kref_init": {
        "category": "C-replace", "haiku_api": ["atomic_set"],
        "header": "headers/os/support/SupportDefs.h",
        "note": "kref_init initializes a kref with count one. Haiku atomic_set works the same."
    },

    # --- Time and sleep (C-replace) ---
    "msleep": {
        "category": "C-replace", "haiku_api": ["snooze"],
        "header": "headers/os/kernel/OS.h",
        "note": "msleep sleeps for a specified number of milliseconds with guaranteed resolution. Haiku snooze takes microseconds."
    },
    "usleep_range": {
        "category": "C-replace", "haiku_api": ["snooze"],
        "header": "headers/os/kernel/OS.h",
        "note": "usleep_range sleeps within a range to allow batching. Haiku snooze takes exact microseconds; range requires extra logic."
    },
    "msecs_to_jiffies": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "msecs_to_jiffies converts milliseconds to jiffies. Haiku time is in microseconds; conversion is direct division."
    },
    "time_before": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "time_before checks if one jiffy timestamp is before another with wraparound. Haiku uses bigtime_t without wraparound."
    },
    "timeout": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "timeout is a helper macro for timeout loops with jiffies. Haiku uses bigtime_t and direct comparison."
    },

    # --- Scheduling and workqueues (A-reimplement) ---
    "schedule_work": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "schedule_work queues a work item on a workqueue for deferred execution. Haiku has no workqueue; use threads or timers."
    },
    "INIT_WORK": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "INIT_WORK initializes a work item with a handler function. Haiku has no workqueue; use thread functions instead."
    },
    "flush_work": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "flush_work waits for a work item to complete. Haiku has no workqueue; use thread join instead."
    },

    # --- Firmware loading (D-ignore — not used by GK110 path) ---
    "request_firmware": {
        "category": "D-ignore", "haiku_api": [],
        "header": None,
        "note": "request_firmware loads firmware from filesystem. Only gf100_gr_load_fw calls this for external files the driver does not use."
    },
    "release_firmware": {
        "category": "D-ignore", "haiku_api": [],
        "header": None,
        "note": "release_firmware frees a firmware blob from request_firmware. The driver uses built-in firmware arrays, not external files."
    },

    # --- DMA operations ---
    "dma_map_page": {
        "category": "C-replace", "haiku_api": ["get_memory_map", "lock_memory"],
        "header": "headers/os/drivers/KernelExport.h",
        "note": "dma_map_page maps a page for device DMA access. Haiku get_memory_map and lock_memory provide bus address access."
    },
    "dma_unmap_page": {
        "category": "C-replace", "haiku_api": ["unlock_memory"],
        "header": "headers/os/drivers/KernelExport.h",
        "note": "dma_unmap_page unmaps a page previously mapped for DMA. Haiku unlock_memory releases the locked memory."
    },
    "dma_mapping_error": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "dma_mapping_error checks if a DMA mapping failed. Haiku DMA implementation needs its own error checking."
    },
    "dma_free_coherent": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "dma_free_coherent releases coherent DMA memory. Haiku has no coherent DMA API; needs custom implementation."
    },
    "sg_next": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "sg_next returns the next scatterlist entry. Haiku has no scatterlist; driver uses its own descriptor format."
    },
    "sg_dma_len": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "sg_dma_len returns the DMA length of a scatterlist entry. Haiku has no scatterlist; driver manages its own descriptors."
    },

    # --- PCI subsystem (D-ignore — AGP, unnecessary) ---
    "agp_enable": {
        "category": "D-ignore", "haiku_api": [],
        "header": None,
        "note": "agp_enable enables AGP mode. Haiku driver does not use AGP; it uses direct BAR access."
    },
    "agp_backend_acquire": {
        "category": "D-ignore", "haiku_api": [],
        "header": None,
        "note": "agp_backend_acquire acquires the AGP backend. Haiku driver does not use AGP."
    },
    "agp_backend_release": {
        "category": "D-ignore", "haiku_api": [],
        "header": None,
        "note": "agp_backend_release releases the AGP backend. Haiku driver does not use AGP."
    },
    "agp_copy_info": {
        "category": "D-ignore", "haiku_api": [],
        "header": None,
        "note": "agp_copy_info copies AGP GATT table info. Haiku driver does not use AGP."
    },
    "arch_phys_wc_add": {
        "category": "D-ignore", "haiku_api": [],
        "header": None,
        "note": "arch_phys_wc_add adds a write-combining memory region. Haiku driver uses direct BAR access without WC."
    },
    "arch_phys_wc_del": {
        "category": "D-ignore", "haiku_api": [],
        "header": None,
        "note": "arch_phys_wc_del removes a write-combining region. Haiku driver does not use write-combining."
    },
    "pci_enable_msi": {
        "category": "D-ignore", "haiku_api": [],
        "header": None,
        "note": "pci_enable_msi enables MSI interrupts. Haiku driver uses a different interrupt mechanism."
    },
    "pci_disable_msi": {
        "category": "D-ignore", "haiku_api": [],
        "header": None,
        "note": "pci_disable_msi disables MSI interrupts. Haiku driver does not use MSI interrupts."
    },
    "pci_is_pcie": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "pci_is_pcie checks if a device is PCIe. Haiku driver reads PCI config space directly for this check."
    },

    # --- Arithmetic and bit macros (A-reimplement — not Linux functions) ---
    "BIT": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "BIT(x) is a compile-time shift macro, not a function call. Haiku can use 1 << x directly."
    },
    "BIT_ULL": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "BIT_ULL(x) is a compile-time 64-bit shift macro. Haiku can use 1ULL << x directly."
    },
    "upper_32_bits": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "upper_32_bits extracts the upper 32 bits of a 64-bit value. Haiku can use (u64 >> 32) directly."
    },
    "lower_32_bits": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "lower_32_bits extracts the lower 32 bits of a 64-bit value. Haiku can use (u64 & 0xFFFFFFFF) directly."
    },
    "ALIGN": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "ALIGN(x, a) rounds x up to the next multiple of a. Haiku can use ((x + a - 1) & ~(a - 1)) directly."
    },
    "ALIGN_DOWN": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "ALIGN_DOWN(x, a) rounds x down to the previous multiple of a. Haiku can use (x & ~(a - 1)) directly."
    },
    "min": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "min(x, y) is a compile-time comparison macro with type safety. Haiku can use standard min function or ternary operator."
    },
    "min_t": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "min_t(type, x, y) is a typed comparison macro. Haiku can use standard min with explicit casting."
    },
    "max": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "max(x, y) is a compile-time comparison macro with type safety. Haiku can use standard max function or ternary operator."
    },
    "max_t": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "max_t(type, x, y) is a typed comparison macro. Haiku can use standard max with explicit casting."
    },
    "DIV_ROUND_UP": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "DIV_ROUND_UP(n, d) computes (n + d - 1) / d at compile time. Haiku can use inline formula."
    },
    "order_base_2": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "order_base_2(n) computes the log2 of the next power of two. Haiku can use ilog2 or a loop."
    },
    "ARRAY_SIZE": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "ARRAY_SIZE(x) is a compile-time array size macro. Haiku can use sizeof(x) / sizeof(x[0])."
    },
    "unlikely": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "unlikely(x) is a branch prediction hint macro. Haiku has no branch prediction attribute; the compiler optimizes independently."
    },
    "likely": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "likely(x) is a branch prediction hint macro. Haiku has no branch prediction attribute; the compiler optimizes independently."
    },
    "IS_ERR": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "IS_ERR() checks if a pointer is an error value (encoded errno). Haiku needs its own error pointer scheme."
    },
    "PTR_ERR": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "PTR_ERR() extracts the errno from an error pointer. Haiku needs matching error pointer scheme."
    },
    "ERR_PTR": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "ERR_PTR() encodes an errno as an error pointer. Haiku needs matching error pointer scheme."
    },
    "IS_ALIGNED": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "IS_ALIGNED(x, a) checks if x is aligned to a. Haiku can use (x & (a - 1)) == 0 directly."
    },
    "WARN_ON": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "WARN_ON(condition) logs a warning if condition is true. Haiku has no equivalent; use a debug logging macro."
    },
    "BUG_ON": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "BUG_ON(condition) triggers a kernel panic. Haiku driver should handle errors gracefully instead of panicking."
    },
    "BUG": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "BUG() triggers a kernel panic unconditionally. Haiku driver should handle errors gracefully instead of panicking."
    },

    # --- Bit manipulation (A-reimplement) ---
    "__ffs": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "__ffs finds the first set bit in a 64-bit value. Haiku has no __ffs; use built-in bit scanning or a loop."
    },
    "for_each_set_bit": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "for_each_set_bit iterates over set bits in a bitmap. Haiku has no equivalent; needs custom bit iteration."
    },
    "find_first_zero_bit": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "find_first_zero_bit finds the first unset bit in a bitmap. Haiku has no equivalent; needs custom bit search."
    },
    "ilog2": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "ilog2 computes the integer log2 of a value. Haiku has no ilog2; use a loop or built-in __builtin_clz."
    },
    "hweight32": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "hweight32 counts set bits in a 32-bit value. Haiku has no hweight; implement with bit-counting algorithm."
    },
    "hweight8": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "hweight8 counts set bits in a byte. Haiku has no hweight; implement with bit-counting algorithm."
    },
    "do_div": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "do_div divides a 64-bit value by a 32-bit divisor, modifying it in place. Haiku can use standard 64-bit division."
    },
    "container_of": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "container_of computes struct pointer from member address. Haiku can use pointer arithmetic with offset."
    },

    # --- Print and debug ---
    "printk": {
        "category": "A-reimplement", "haiku_api": [],
        "header": None,
        "note": "printk is the Linux kernel logging function with log levels. Haiku has no printk; use kernel logging API."
    },
    "snprintf": {
        "category": "C-replace", "haiku_api": ["snprintf"],
        "header": None,
        "note": "snprintf formats into a buffer with size limit. Standard C function available in Haiku."
    },
    "sprintf": {
        "category": "C-replace", "haiku_api": ["sprintf"],
        "header": None,
        "note": "sprintf formats into a buffer without size limit. Standard C function available in Haiku."
    },
    "strscpy": {
        "category": "C-replace", "haiku_api": ["strlcpy"],
        "header": None,
        "note": "strscpy copies a string with size limit and NUL-termination. Haiku strlcpy has the same behavior."
    },

    # --- Standard memory (C-replace, standard C) ---
    "memcpy": {
        "category": "C-replace", "haiku_api": ["memcpy"],
        "header": None,
        "note": "memcpy copies a block of memory. Standard C function available in Haiku."
    },
    "memset": {
        "category": "C-replace", "haiku_api": ["memset"],
        "header": None,
        "note": "memset sets a block of memory to a value. Standard C function available in Haiku."
    },
    "memcmp": {
        "category": "C-replace", "haiku_api": ["memcmp"],
        "header": None,
        "note": "memcmp compares two memory blocks. Standard C function available in Haiku."
    },
}

# Symbols not in the classification table — classify them
HW_CONSTS = {"FBP", "LTC", "GPC_UNIT", "TPC_UNIT", "VMM_DEBUG",
             "CASE", "REF_PTES", "MAP_PTES", "CLR_PTES", "PTE"}
GPU_FUNCS = {"gf100_grctx_patch_wr32", "nvkm_wr32", "nvkm_rd32",
             "ram_mask", "ram_wr32", "ramfuc_reg", "nvkm_mask",
             "nvkm_wo32", "nvkm_error", "nvkm_debug", "nvkm_msec",
             "nvkm_memory_unref", "nvkm_memory_size", "nvkm_kmap",
             "nvkm_subdev_new_", "nvkm_top_addr", "nvkm_top_intr_mask",
             "nvkm_top_fault", "nvkm_top_parse", "nvkm_top_dtor", "nvkm_top",
             "gk104_top_parse", "gk104_top_new", "d", "nvif_unpack"}


def classify_unknown(name):
    """Classify symbols not in CLASSIFY table."""
    if name in HW_CONSTS:
        return {"category": "X-not-linux", "haiku_api": [],
                "header": None,
                "note": "This is a hardware constant or macro, not a Linux function. No replacement needed."}
    if name in GPU_FUNCS:
        return {"category": "X-not-linux", "haiku_api": [],
                "header": None,
                "note": "This is a Nouveau-internal function, not a Linux kernel function. No Haiku replacement needed."}
    return {"category": "X-not-linux", "haiku_api": [],
            "header": None,
            "note": "This symbol is not standard Linux kernel infrastructure. It may be a Nouveau-local macro or function."}


def build_entries(counts, locations):
    """Build the sorted list of dependency entries."""
    entries = []
    for symbol in sorted(counts.keys()):
        count = counts[symbol]
        first_file, first_line = sorted(locations[symbol])[0]
        if symbol in CLASSIFY:
            info = CLASSIFY[symbol]
        else:
            info = classify_unknown(symbol)
        entry = {
            "symbol": symbol,
            "count": count,
            "example": {"file": first_file, "line": first_line},
            "category": info["category"],
            "haiku_api": info["haiku_api"],
            "header": info["header"],
            "note": info["note"],
        }
        entries.append(entry)
    return entries


def main():
    files = load_files()
    counts, locations = extract_calls(files)

    # Check mode
    if "--check" in sys.argv:
        if not os.path.exists(OUTPUT):
            print(f"{OUTPUT}: missing (need to generate first)", file=sys.stderr)
            sys.exit(1)
        existing = json.load(open(OUTPUT))
        generated = build_entries(counts, locations)
        if existing != generated:
            print(f"{OUTPUT}: content differs from what the tool generates", file=sys.stderr)
            sys.exit(1)
        print("OK: analysis/linux_deps.json matches tool output")
        sys.exit(0)

    # Generate output
    entries = build_entries(counts, locations)
    with open(OUTPUT, "w") as f:
        json.dump(entries, f, indent=2)
        f.write("\n")
    print(f"Generated {len(entries)} symbols in {OUTPUT}")


if __name__ == "__main__":
    main()
