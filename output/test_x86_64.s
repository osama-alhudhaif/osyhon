# Osyhon x86_64 — Quick run test (GNU AS / AT&T syntax)
# Tests: print string, print int, alloc memory, for loop, cpu.halt
#
# Assemble & link:
#   as -o test_x86_64.o test_x86_64.s && ld -o test_x86_64 test_x86_64.o
# Run:
#   ./test_x86_64

.intel_syntax noprefix
.text
.global _start

# ── _oy_print(rdi=ptr, rsi=len) ─────────────────────────
_oy_print:
    push    rbp
    mov     rbp, rsp
    mov     rdx, rsi
    mov     rsi, rdi
    mov     rdi, 1
    mov     rax, 1
    syscall
    pop     rbp
    ret

# ── _oy_print_int(rdi=number) ───────────────────────────
_oy_print_int:
    push    rbp
    mov     rbp, rsp
    sub     rsp, 32
    lea     r8,  [rsp + 31]
    mov     BYTE PTR [r8], 0x0A
    dec     r8
    mov     rax, rdi
    mov     r9,  10
.convert:
    xor     rdx, rdx
    div     r9
    add     dl, 48
    mov     [r8], dl
    dec     r8
    test    rax, rax
    jnz     .convert
    inc     r8
    mov     rsi, r8
    lea     rdx, [rsp + 32]
    sub     rdx, r8
    mov     rdi, 1
    mov     rax, 1
    syscall
    add     rsp, 32
    pop     rbp
    ret

# ── _oy_alloc(rdi=size) -> rax=ptr ──────────────────────
_oy_alloc:
    push    rbp
    mov     rbp, rsp
    mov     r11, rdi
    mov     rax, 9
    xor     rdi, rdi
    mov     rsi, r11
    mov     rdx, 3
    mov     r10, 0x22
    mov     r8,  -1
    xor     r9,  r9
    syscall
    pop     rbp
    ret

# ── _oy_halt() ──────────────────────────────────────────
_oy_halt:
    mov     rax, 60
    xor     rdi, rdi
    syscall

# ── kernel_start ────────────────────────────────────────
oy_kernel_start:
    push    rbp
    mov     rbp, rsp

    # alloc memory 1024
    mov     rdi, 1024
    call    _oy_alloc

    # print "OS started"
    lea     rdi, [rip + _str_os]
    mov     rsi, 10
    call    _oy_print
    lea     rdi, [rip + _newline]
    mov     rsi, 1
    call    _oy_print

    # for i in range 3: print i
    xor     r12, r12
.loop_check:
    cmp     r12, 3
    jge     .loop_end
    mov     rdi, r12
    call    _oy_print_int
    inc     r12
    jmp     .loop_check
.loop_end:

    # print "done!"
    lea     rdi, [rip + _str_done]
    mov     rsi, 5
    call    _oy_print
    lea     rdi, [rip + _newline]
    mov     rsi, 1
    call    _oy_print

    pop     rbp
    ret

# ── _start ──────────────────────────────────────────────
_start:
    call    oy_kernel_start
    call    _oy_halt

.data
_str_os:    .ascii "OS started"
_str_done:  .ascii "done!"
_newline:   .byte  0x0A
