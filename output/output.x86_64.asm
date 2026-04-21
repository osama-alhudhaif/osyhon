; ============================================================
;  Osyhon — x86_64 (Linux / NASM Intel syntax)
; ============================================================
bits 64
default rel

section .text
    global _start

; ── _oy_print(rdi=ptr, rsi=len) ───────────────────────────
_oy_print:
    push    rbp
    mov     rbp, rsp
    mov     rax, 1
    mov     rdx, rsi            ; len
    mov     rsi, rdi            ; ptr
    mov     rdi, 1              ; stdout
    syscall
    pop     rbp
    ret

; ── _oy_print_int(rdi=number) ─────────────────────────────
_oy_print_int:
    push    rbp
    mov     rbp, rsp
    sub     rsp, 32
    lea     rsi, [rsp+31]
    mov     byte [rsi], 0x0A    ; trailing newline
    dec     rsi
    mov     rax, rdi
    mov     r9,  10
    test    rax, rax
    jns     .convert
    neg     rax
.convert:
    xor     rdx, rdx
    div     r9
    add     dl, '0'
    mov     [rsi], dl
    dec     rsi
    test    rax, rax
    jnz     .convert
    test    rdi, rdi
    jns     .no_neg
    mov     byte [rsi], '-'
    dec     rsi
.no_neg:
    inc     rsi
    mov     rax, 1
    mov     rdi, 1
    lea     rdx, [rsp+32]
    sub     rdx, rsi            ; len
    syscall
    add     rsp, 32
    pop     rbp
    ret

; ── _oy_alloc(rdi=size) -> rax=ptr ───────────────────────
_oy_alloc:
    push    rbp
    mov     rbp, rsp
    mov     r10, rdi            ; save size
    mov     rax, 9
    xor     rdi, rdi            ; addr = NULL (kernel chooses)
    mov     rsi, r10            ; length
    mov     rdx, 3              ; PROT_READ | PROT_WRITE
    mov     r10, 0x22           ; MAP_PRIVATE | MAP_ANONYMOUS
    mov     r8,  -1             ; fd = -1
    xor     r9,  r9             ; offset = 0
    syscall                     ; rax = ptr or -errno
    pop     rbp
    ret

; ── _oy_free(rdi=ptr, rsi=size) ──────────────────────────
_oy_free:
    push    rbp
    mov     rbp, rsp
    mov     rax, 11
    syscall
    pop     rbp
    ret

; ── _oy_halt() ────────────────────────────────────────────
_oy_halt:
    mov     rax, 60
    xor     rdi, rdi
    syscall

; ── _oy_port_write(rdi=port, rsi=value) ──────────────────
; ── NOTE: requires IOPL=3 (kernel mode / privileged) ─────
_oy_port_write:
    mov     dx, di              ; port number (16-bit)
    mov     al, sil             ; byte value
    out     dx, al
    ret

; ── _oy_memory_map(rdi=addr, rsi=size) -> rax=ptr ────────
_oy_memory_map:
    push    rbp
    mov     rbp, rsp
    mov     r10, rdi
    mov     r11, rsi
    mov     rax, 9
    mov     rdi, r10            ; fixed address
    mov     rsi, r11            ; size
    mov     rdx, 3              ; PROT_READ | PROT_WRITE
    mov     r10, 0x32           ; MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS
    mov     r8,  -1
    xor     r9,  r9
    syscall
    pop     rbp
    ret


; ── def greet ──────────────────────────────
oy_greet:
    push    rbp
    mov     rbp, rsp
    ; arg 'name' is in rdi
    lea     rdi, [_str0]
    mov     rsi, _str0_len
    call    _oy_print
    ; print newline
    lea     rdi, [_newline]
    mov     rsi, 1
    call    _oy_print
    call    _oy_print_int
    pop     rbp
    ret

; ── kernel_start ──────────────────────────────────────
oy_kernel_start:
    push    rbp
    mov     rbp, rsp
    mov     rdi, 1024
    call    _oy_alloc
    ; 'buf' points to allocated block (rax)
    lea     rdi, [_str1]
    mov     rsi, _str1_len
    call    _oy_print
    ; print newline
    lea     rdi, [_newline]
    mov     rsi, 1
    call    _oy_print
    xor     r12, r12        ; loop counter = 0
    jmp     .Lcheck2
.Lloop1:
    mov     rdi, r12
    call    _oy_print_int
    inc     r12
.Lcheck2:
    mov     rbx, 3
    cmp     r12, rbx
    jl      .Lloop1
    mov     rax, 0
    mov     rbx, 10
    cmp     rax, rbx
    jne     .Lelse3
    lea     rdi, [_str2]
    mov     rsi, _str2_len
    call    _oy_print
    ; print newline
    lea     rdi, [_newline]
    mov     rsi, 1
    call    _oy_print
    jmp     .Lend4
.Lelse3:
.Lend4:
    mov     rdi, 4276092928
    mov     rsi, 4096
    call    _oy_memory_map
    call    _oy_halt
    pop     rbp
    ret

; ── entry point ──────────────────────────────────────────
_start:
    call    oy_kernel_start
    mov     rax, 60
    xor     rdi, rdi
    syscall

section .data
    _str0     db "hello ", 0
    _str0_len equ $ - _str0 - 1
    _str1     db "OS started", 0
    _str1_len equ $ - _str1 - 1
    _str2     db "yes", 0
    _str2_len equ $ - _str2 - 1

    _newline    db 0x0A
    _newline_len equ 1