# RISC-V 64 — اختبار يدوي للوظائف الأساسية
# as -o t.o simple_riscv_test.s && ld -o t t.o && qemu-riscv64 ./t

.option nopic
.attribute arch, "rv64i2p0_m2p0"
.text
.global _start

# _oy_print(a0=ptr, a1=len)
_oy_print:
    addi    sp, sp, -16
    sd      ra, 8(sp)
    mv      a2, a1
    mv      a1, a0
    li      a0, 1
    li      a7, 64
    ecall
    ld      ra, 8(sp)
    addi    sp, sp, 16
    ret

# _oy_print_int(a0=number) — يبني الرقم بالـ stack ويطبعه
_oy_print_int:
    addi    sp, sp, -32
    sd      ra, 24(sp)
    # buffer: sp+0..sp+23 (24 bytes كافية لـ 20 رقم + newline)
    addi    t0, sp, 22          # t0 = نهاية Buffer (نبدأ من اليمين)
    li      t1, 0x0A
    sb      t1, 0(t0)           # newline في النهاية
    addi    t0, t0, -1
    mv      t2, a0
    li      t3, 10
    # حالة خاصة: رقم 0
    bnez    t2, .Lconv_loop
    li      t4, 48              # '0'
    sb      t4, 0(t0)
    addi    t0, t0, -1
    j       .Lconv_done
.Lconv_loop:
    remu    t4, t2, t3
    addi    t4, t4, 48
    sb      t4, 0(t0)
    addi    t0, t0, -1
    divu    t2, t2, t3
    bnez    t2, .Lconv_loop
.Lconv_done:
    addi    a1, t0, 1           # بداية النص
    addi    a2, sp, 23          # نهاية النص (بعد newline)
    sub     a2, a2, t0          # الطول = نهاية - بداية + 1
    li      a0, 1
    li      a7, 64
    ecall
    ld      ra, 24(sp)
    addi    sp, sp, 32
    ret

_start:
    # اختبار 1: طباعة نص
    la      a0, str_os
    li      a1, 10
    call    _oy_print
    la      a0, nl
    li      a1, 1
    call    _oy_print

    # اختبار 2: طباعة أرقام (حلقة for i in range 3)
    li      s1, 0
.Lloop:
    mv      a0, s1
    call    _oy_print_int
    addi    s1, s1, 1
    li      t0, 3
    blt     s1, t0, .Lloop

    # اختبار 3: نص نهائي
    la      a0, str_done
    li      a1, 5
    call    _oy_print
    la      a0, nl
    li      a1, 1
    call    _oy_print

    # خروج
    li      a7, 93
    li      a0, 0
    ecall

.data
str_os:   .string "OS started"
str_done: .string "done!"
nl:       .byte   0x0A
