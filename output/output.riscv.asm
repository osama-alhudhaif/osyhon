# ============================================================
#  Osyhon — RISC-V 64-bit (Linux / GNU AS RV64I)
# ============================================================
.option nopic
.attribute arch, "rv64i2p0_m2p0"
.text
.global _start

# ── _oy_print(a0=ptr, a1=len) ─────────────────────────────
_oy_print:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    mv      a2, a1              # len
    mv      a1, a0              # ptr
    li      a0, 1               # stdout (fd=1)
    li      a7, 64
    ecall
    ld      ra, 8(sp)
    addi    sp, sp, 16
    ret

# ── _oy_print_int(a0=number) ──────────────────────────────
# Frame layout (80 bytes):
#   sp+0..sp+7  : saved ra  (bottom, safe from buffer)
#   sp+8..sp+79 : digit buffer (top-down, max 20 digits + newline)
_oy_print_int:
    addi    sp, sp, -80
    sd      ra, 0(sp)            # save ra at bottom of frame
    addi    t0, sp, 79           # t0 = top of buffer
    li      t1, 0x0A
    sb      t1, 0(t0)            # trailing newline at sp+79
    addi    t0, t0, -1           # t0 = sp+78 (first digit slot)
    mv      t2, a0              # number
    li      t3, 10
.Lprint_int_loop:
    remu    t4, t2, t3          # remainder
    addi    t4, t4, 48          # '0' = 48
    sb      t4, 0(t0)
    addi    t0, t0, -1
    divu    t2, t2, t3
    bnez    t2, .Lprint_int_loop
    addi    a1, t0, 1           # start of number string
    addi    a2, sp, 80          # one past end (sp+80 = caller sp)
    sub     a2, a2, a1          # length = (sp+79 - t0)
    li      a0, 1               # stdout
    li      a7, 64
    ecall
    ld      ra, 0(sp)           # restore ra from bottom of frame
    addi    sp, sp, 80
    ret

# ── _oy_alloc(a0=size) -> a0=ptr ──────────────────────────
_oy_alloc:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    mv      a1, a0              # length
    li      a0, 0               # addr = NULL
    li      a2, 3               # PROT_READ | PROT_WRITE
    li      a3, 0x22            # MAP_PRIVATE | MAP_ANONYMOUS
    li      a4, -1              # fd = -1
    li      a5, 0               # offset = 0
    li      a7, 222
    ecall                       # a0 = ptr or -errno
    ld      ra, 8(sp)
    addi    sp, sp, 16
    ret

# ── _oy_free(a0=ptr, a1=size) ─────────────────────────────
_oy_free:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    li      a7, 215
    ecall
    ld      ra, 8(sp)
    addi    sp, sp, 16
    ret

# ── _oy_halt() ─────────────────────────────────────────────
_oy_halt:
    li      a7, 93
    li      a0, 0
    ecall

# ── _oy_port_write(a0=mmio_addr, a1=value) ────────────────
# ── NOTE: RISC-V uses MMIO — no IN/OUT instructions ────────
_oy_port_write:
    sw      a1, 0(a0)           # MMIO write: store value at address
    fence   ow, ow              # memory ordering fence
    ret

# ── _oy_memory_map(a0=addr, a1=size) -> a0=ptr ────────────
_oy_memory_map:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    li      a2, 3               # PROT_READ | PROT_WRITE
    li      a3, 0x32            # MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS
    li      a4, -1              # fd = -1
    li      a5, 0               # offset = 0
    li      a7, 222
    ecall
    ld      ra, 8(sp)
    addi    sp, sp, 16
    ret


# ── def greet ──────────────────────────────
oy_greet:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    sd      s0, 0(sp)
    addi    s0, sp, 16
    la      a0, _str0
    li      a1, 6
    call    _oy_print
    la      a0, _newline
    li      a1, 1
    call    _oy_print
    call    _oy_print_int
    ld      ra, 8(sp)
    ld      s0, 0(sp)
    addi    sp, sp, 16
    ret

# ── kernel_start ───────────────────────────────────────
oy_kernel_start:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    sd      s0, 0(sp)
    addi    s0, sp, 16
    li      a0, 1024
    call    _oy_alloc
    la      a0, _str1
    li      a1, 10
    call    _oy_print
    la      a0, _newline
    li      a1, 1
    call    _oy_print
    li      s1, 0           # loop counter = 0
    j       .Lcheck2
.Lloop1:
    mv      a0, s1
    call    _oy_print_int
    addi    s1, s1, 1
.Lcheck2:
    li      s2, 3
    blt     s1, s2, .Lloop1
    li      t0, 10
    bne     a0, t0, .Lelse3
    la      a0, _str2
    li      a1, 3
    call    _oy_print
    la      a0, _newline
    li      a1, 1
    call    _oy_print
    j       .Lend4
.Lelse3:
.Lend4:
    li      a0, 4276092928
    li      a1, 4096
    call    _oy_memory_map
    call    _oy_halt
    ld      ra, 8(sp)
    ld      s0, 0(sp)
    addi    sp, sp, 16
    ret

# ── entry point ───────────────────────────────────────────
_start:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    sd      s0, 0(sp)
    addi    s0, sp, 16
    call    oy_kernel_start
    li      a7, 93
    li      a0, 0
    ecall

.data
_str0:
    .string "hello "
.set _str0_len, . - _str0 - 1
_str1:
    .string "OS started"
.set _str1_len, . - _str1 - 1
_str2:
    .string "yes"
.set _str2_len, . - _str2 - 1

_newline:
    .byte 0x0A
.set _newline_len, 1
