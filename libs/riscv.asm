# ============================================================
#  Osyhon — RISC-V 64-bit Runtime Library
#  Target : Linux  |  Syntax: GNU AS (RV64I)
#
#  Syscalls used (Linux RV64):
#    SYS_READ   = 63     SYS_WRITE  = 64
#    SYS_MMAP   = 222    SYS_MUNMAP = 215
#    SYS_EXIT   = 93
#
#  ABI: RISC-V LP64
#    args  : a0–a7
#    return: a0 (a0–a1 for 128-bit)
#    syscall: a7 = number, args in a0–a5
#    instruction: ecall
# ============================================================

.option nopic
.attribute arch, "rv64i2p0"
.text

# ── _oy_print(a0=ptr, a1=len) ─────────────────────────────
# Writes 'len' bytes from 'ptr' to stdout.
.global _oy_print
_oy_print:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    mv      a2, a1              # len  → arg3
    mv      a1, a0              # ptr  → arg2
    li      a0, 1               # fd   = stdout (arg1)
    li      a7, 64              # SYS_write
    ecall
    ld      ra, 8(sp)
    addi    sp, sp, 16
    ret

# ── _oy_print_int(a0=unsigned 64-bit int) ─────────────────
# Converts integer to decimal and prints it + newline.
.global _oy_print_int
_oy_print_int:
    addi    sp, sp, -80
    sd      ra, 72(sp)
    addi    t0, sp, 79          # end of buffer
    li      t1, 0x0A
    sb      t1, 0(t0)           # trailing newline
    addi    t0, t0, -1
    mv      t2, a0              # working copy of number
    li      t3, 10
.Lprint_loop:
    remu    t4, t2, t3          # remainder = number % 10
    addi    t4, t4, 48          # '0' = 48
    sb      t4, 0(t0)
    addi    t0, t0, -1
    divu    t2, t2, t3
    bnez    t2, .Lprint_loop
    addi    a1, t0, 1           # start of string
    addi    a2, sp, 80
    sub     a2, a2, a1          # length
    li      a0, 1               # stdout
    li      a7, 64              # SYS_write
    ecall
    ld      ra, 72(sp)
    addi    sp, sp, 80
    ret

# ── _oy_alloc(a0=size) -> a0=ptr ──────────────────────────
# Allocates 'size' bytes via mmap(MAP_PRIVATE|MAP_ANONYMOUS).
.global _oy_alloc
_oy_alloc:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    mv      a1, a0              # length
    li      a0, 0               # addr   = NULL
    li      a2, 3               # prot   = PROT_READ | PROT_WRITE
    li      a3, 0x22            # flags  = MAP_PRIVATE | MAP_ANONYMOUS
    li      a4, -1              # fd     = -1
    li      a5, 0               # offset = 0
    li      a7, 222             # SYS_mmap
    ecall                       # a0 = ptr or -errno
    ld      ra, 8(sp)
    addi    sp, sp, 16
    ret

# ── _oy_free(a0=ptr, a1=size) ─────────────────────────────
# Releases a block previously returned by _oy_alloc.
.global _oy_free
_oy_free:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    li      a7, 215             # SYS_munmap
    ecall
    ld      ra, 8(sp)
    addi    sp, sp, 16
    ret

# ── _oy_halt() ─────────────────────────────────────────────
# Terminates the process with exit code 0.
.global _oy_halt
_oy_halt:
    li      a7, 93              # SYS_exit
    li      a0, 0               # status = 0
    ecall

# ── _oy_port_write(a0=mmio_addr, a1=value) ─────────────────
# RISC-V has no IN/OUT — uses Memory-Mapped I/O.
# Writes 32-bit 'value' to MMIO address 'mmio_addr'.
.global _oy_port_write
_oy_port_write:
    sw      a1, 0(a0)           # 32-bit MMIO store
    fence   ow, ow              # ordering fence (output, memory)
    ret

# ── _oy_port_read(a0=mmio_addr) -> a0=value ─────────────────
.global _oy_port_read
_oy_port_read:
    lw      a0, 0(a0)           # 32-bit MMIO load
    fence   ir, ir              # ordering fence (input, memory)
    ret

# ── _oy_memory_map(a0=addr, a1=size) -> a0=ptr ─────────────
# Maps a fixed address range for MMIO / hardware registers.
.global _oy_memory_map
_oy_memory_map:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    # a0 = addr, a1 = size already set
    li      a2, 3               # PROT_READ | PROT_WRITE
    li      a3, 0x32            # MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS
    li      a4, -1              # fd = -1
    li      a5, 0               # offset = 0
    li      a7, 222             # SYS_mmap
    ecall
    ld      ra, 8(sp)
    addi    sp, sp, 16
    ret

# ── _oy_cpu_mvendorid() -> a0=mvendorid ────────────────────
# Reads the Machine Vendor ID CSR.
# Returns 0 if running in user mode (no access to M-mode CSRs).
.global _oy_cpu_mvendorid
_oy_cpu_mvendorid:
    csrr    a0, mvendorid
    ret

# ── _oy_cpu_marchid() -> a0=marchid ────────────────────────
# Reads the Machine Architecture ID CSR.
.global _oy_cpu_marchid
_oy_cpu_marchid:
    csrr    a0, marchid
    ret
