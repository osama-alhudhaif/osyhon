// ============================================================
//  Osyhon — ARM64 / AArch64 (Linux / GNU AS)
// ============================================================
.arch armv8-a
.text
.global _start

// ── _oy_print(x0=ptr, x1=len) ─────────────────────────────
_oy_print:
    stp     x29, x30, [sp, #-16]!
    mov     x29, sp
    mov     x2,  x1             // len
    mov     x1,  x0             // ptr
    mov     x0,  #1             // stdout
    mov     x8,  #64
    svc     #0
    ldp     x29, x30, [sp], #16
    ret

// ── _oy_print_int(x0=number) ──────────────────────────────
_oy_print_int:
    stp     x29, x30, [sp, #-64]!
    mov     x29, sp
    mov     x9,  sp
    add     x9,  x9, #63
    mov     x10, #0x0A
    strb    w10, [x9]
    sub     x9,  x9, #1
    mov     x1,  x0             // number
    mov     x11, #10
.Lprint_int_loop:
    udiv    x12, x1, x11
    msub    x13, x12, x11, x1   // remainder
    add     w13, w13, #'0'
    strb    w13, [x9]
    sub     x9,  x9, #1
    mov     x1,  x12
    cbnz    x1,  .Lprint_int_loop
    add     x1,  x9, #1         // start of number
    add     x2,  sp,  #64
    sub     x2,  x2,  x1        // length
    mov     x0,  #1             // stdout
    mov     x8,  #64
    svc     #0
    ldp     x29, x30, [sp], #64
    ret

// ── _oy_alloc(x0=size) -> x0=ptr ──────────────────────────
_oy_alloc:
    stp     x29, x30, [sp, #-16]!
    mov     x29, sp
    mov     x1,  x0             // length
    mov     x0,  #0             // addr = NULL
    mov     x2,  #3             // PROT_READ | PROT_WRITE
    mov     x3,  #0x22          // MAP_PRIVATE | MAP_ANONYMOUS
    mov     x4,  #-1            // fd = -1
    mov     x5,  #0             // offset = 0
    mov     x8,  #222
    svc     #0                  // x0 = ptr or -errno
    ldp     x29, x30, [sp], #16
    ret

// ── _oy_free(x0=ptr, x1=size) ─────────────────────────────
_oy_free:
    stp     x29, x30, [sp, #-16]!
    mov     x29, sp
    mov     x8,  #215
    svc     #0
    ldp     x29, x30, [sp], #16
    ret

// ── _oy_halt() ─────────────────────────────────────────────
_oy_halt:
    mov     x8,  #93
    mov     x0,  #0
    svc     #0

// ── _oy_port_write(x0=port, x1=value) ─────────────────────
// ── NOTE: ARM64 has no IN/OUT — use MMIO instead ───────────
_oy_port_write:
    str     w1, [x0]            // MMIO: write value to port address
    ret

// ── _oy_memory_map(x0=addr, x1=size) -> x0=ptr ────────────
_oy_memory_map:
    stp     x29, x30, [sp, #-16]!
    mov     x29, sp
    mov     x2,  #3             // PROT_READ | PROT_WRITE
    mov     x3,  #0x32          // MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS
    mov     x4,  #-1
    mov     x5,  #0
    mov     x8,  #222
    svc     #0
    ldp     x29, x30, [sp], #16
    ret


// ── def greet ──────────────────────────────
oy_greet:
    stp     x29, x30, [sp, #-16]!
    mov     x29, sp
    adr     x0, _str0
    mov     x1, #_str0_len
    bl      _oy_print
    adr     x0, _newline
    mov     x1, #1
    bl      _oy_print
    bl      _oy_print_int
    ldp     x29, x30, [sp], #16
    ret

// ── kernel_start ───────────────────────────────────────
oy_kernel_start:
    stp     x29, x30, [sp, #-16]!
    mov     x29, sp
    mov     x0, #1024
    bl      _oy_alloc
    adr     x0, _str1
    mov     x1, #_str1_len
    bl      _oy_print
    adr     x0, _newline
    mov     x1, #1
    bl      _oy_print
    mov     x19, #0         // loop counter = 0
    b       .Lcheck2
.Lloop1:
    mov     x0, x19
    bl      _oy_print_int
    add     x19, x19, #1
.Lcheck2:
    mov     x20, #3
    cmp     x19, x20
    b.lt    .Lloop1
    mov     x1, #10
    cmp     x0, x1
    b.ne     .Lelse3
    adr     x0, _str2
    mov     x1, #_str2_len
    bl      _oy_print
    adr     x0, _newline
    mov     x1, #1
    bl      _oy_print
    b       .Lend4
.Lelse3:
.Lend4:
    mov     x0, #4276092928
    mov     x1, #4096
    bl      _oy_memory_map
    bl      _oy_halt
    ldp     x29, x30, [sp], #16
    ret

// ── entry point ───────────────────────────────────────────
_start:
    stp     x29, x30, [sp, #-16]!
    mov     x29, sp
    bl      oy_kernel_start
    mov     x8,  #93
    mov     x0,  #0
    svc     #0

.data
_str0:
    .asciz "hello "
_str0_len = . - _str0 - 1
_str1:
    .asciz "OS started"
_str1_len = . - _str1 - 1
_str2:
    .asciz "yes"
_str2_len = . - _str2 - 1

_newline:
    .byte 0x0A
_newline_len = 1
