// ============================================================
//  Osyhon — ARM64 / AArch64 Runtime Library
//  Target : Linux  |  Syntax: GNU AS
//
//  Syscalls used (Linux AArch64):
//    SYS_READ   = 63     SYS_WRITE  = 64
//    SYS_MMAP   = 222    SYS_MUNMAP = 215
//    SYS_EXIT   = 93
//
//  ABI: AAPCS64
//    args  : x0–x7
//    return: x0 (x0–x1 for 128-bit)
//    syscall: x8 = number, args in x0–x5
//    instruction: svc #0
// ============================================================

.arch armv8-a
.text

// ── _oy_print(x0=ptr, x1=len) ─────────────────────────────
// Writes 'len' bytes from 'ptr' to stdout.
.global _oy_print
_oy_print:
    stp     x29, x30, [sp, #-16]!
    mov     x29, sp
    mov     x2,  x1             // len
    mov     x1,  x0             // ptr
    mov     x0,  #1             // fd = stdout
    mov     x8,  #64            // SYS_write
    svc     #0
    ldp     x29, x30, [sp], #16
    ret

// ── _oy_print_int(x0=unsigned 64-bit int) ─────────────────
// Converts integer to decimal and prints it + newline.
.global _oy_print_int
_oy_print_int:
    stp     x29, x30, [sp, #-80]!
    mov     x29, sp
    // build string right-to-left in [sp+16 .. sp+79]
    add     x9,  sp, #79
    mov     w10, #0x0A
    strb    w10, [x9]           // trailing newline
    sub     x9,  x9,  #1
    mov     x11, x0             // number
    mov     x12, #10
.Lprint_loop:
    udiv    x13, x11, x12
    msub    x14, x13, x12, x11  // remainder = x11 - x13*10
    add     w14, w14, #48       // '0'
    strb    w14, [x9]
    sub     x9,  x9,  #1
    mov     x11, x13
    cbnz    x11, .Lprint_loop
    add     x1,  x9,  #1        // start ptr
    add     x2,  sp,  #80
    sub     x2,  x2,  x1        // length
    mov     x0,  #1             // stdout
    mov     x8,  #64            // SYS_write
    svc     #0
    ldp     x29, x30, [sp], #80
    ret

// ── _oy_alloc(x0=size) -> x0=ptr ──────────────────────────
// Allocates 'size' bytes via mmap(MAP_PRIVATE|MAP_ANONYMOUS).
.global _oy_alloc
_oy_alloc:
    stp     x29, x30, [sp, #-16]!
    mov     x29, sp
    mov     x1,  x0             // length
    mov     x0,  #0             // addr = NULL
    mov     x2,  #3             // PROT_READ | PROT_WRITE
    mov     x3,  #0x22          // MAP_PRIVATE | MAP_ANONYMOUS
    mov     x4,  #-1            // fd = -1
    mov     x5,  #0             // offset = 0
    mov     x8,  #222           // SYS_mmap
    svc     #0                  // x0 = ptr or -errno
    ldp     x29, x30, [sp], #16
    ret

// ── _oy_free(x0=ptr, x1=size) ─────────────────────────────
// Releases a block previously returned by _oy_alloc.
.global _oy_free
_oy_free:
    stp     x29, x30, [sp, #-16]!
    mov     x29, sp
    mov     x8,  #215           // SYS_munmap
    svc     #0
    ldp     x29, x30, [sp], #16
    ret

// ── _oy_halt() ─────────────────────────────────────────────
// Terminates the process with exit code 0.
.global _oy_halt
_oy_halt:
    mov     x8,  #93            // SYS_exit
    mov     x0,  #0             // status = 0
    svc     #0

// ── _oy_port_write(x0=mmio_addr, x1=value) ─────────────────
// ARM64 has no IN/OUT — hardware I/O uses Memory-Mapped I/O.
// Writes 32-bit 'value' to MMIO address 'mmio_addr'.
.global _oy_port_write
_oy_port_write:
    str     w1, [x0]            // 32-bit MMIO store
    dsb     sy                  // data synchronisation barrier
    ret

// ── _oy_port_read(x0=mmio_addr) -> x0=value ─────────────────
.global _oy_port_read
_oy_port_read:
    ldr     w0, [x0]            // 32-bit MMIO load
    dsb     sy
    ret

// ── _oy_memory_map(x0=addr, x1=size) -> x0=ptr ─────────────
// Maps a fixed address range (MMIO / hardware registers).
.global _oy_memory_map
_oy_memory_map:
    stp     x29, x30, [sp, #-16]!
    mov     x29, sp
    // x0 = addr, x1 = size already set
    mov     x2,  #3             // PROT_READ | PROT_WRITE
    mov     x3,  #0x32          // MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS
    mov     x4,  #-1            // fd = -1
    mov     x5,  #0             // offset = 0
    mov     x8,  #222           // SYS_mmap
    svc     #0
    ldp     x29, x30, [sp], #16
    ret

// ── _oy_cpu_id() -> x0=MIDR_EL1 ────────────────────────────
// Reads the Main ID Register — identifies the CPU implementer,
// architecture, variant, part, and revision.
.global _oy_cpu_id
_oy_cpu_id:
    mrs     x0, midr_el1
    ret
