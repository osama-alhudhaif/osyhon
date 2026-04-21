; ============================================================
;  Osyhon — x86_64 Runtime Library
;  Target : Linux  |  Syntax: NASM Intel
;
;  Syscalls used:
;    SYS_READ   = 0     SYS_WRITE  = 1
;    SYS_MMAP   = 9     SYS_MUNMAP = 11
;    SYS_EXIT   = 60
;
;  ABI: System V AMD64
;    args  : rdi  rsi  rdx  rcx  r8  r9
;    return: rax
;    syscall args: rdi rsi rdx r10 r8 r9  (number in rax)
; ============================================================

bits 64
default rel

section .text

; ── _oy_print(rdi=ptr, rsi=len) ─────────────────────────────
; Writes 'len' bytes from 'ptr' to stdout.
global _oy_print
_oy_print:
    push    rbp
    mov     rbp, rsp
    mov     rdx, rsi        ; length
    mov     rsi, rdi        ; buffer
    mov     rdi, 1          ; fd = stdout
    mov     rax, 1          ; SYS_write
    syscall
    pop     rbp
    ret

; ── _oy_print_int(rdi=signed 64-bit int) ────────────────────
; Converts integer to decimal string and prints it + newline.
global _oy_print_int
_oy_print_int:
    push    rbp
    mov     rbp, rsp
    sub     rsp, 32
    lea     r8,  [rsp + 31]
    mov     byte [r8], 0x0A     ; trailing newline
    dec     r8
    mov     rax, rdi
    mov     r9,  10
    xor     r10, r10            ; negative flag
    test    rax, rax
    jns     .convert
    neg     rax
    mov     r10, 1
.convert:
    xor     rdx, rdx
    div     r9
    add     dl, '0'
    mov     [r8], dl
    dec     r8
    test    rax, rax
    jnz     .convert
    test    r10, r10
    jz      .no_neg
    mov     byte [r8], '-'
    dec     r8
.no_neg:
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

; ── _oy_alloc(rdi=size) -> rax=ptr ──────────────────────────
; Allocates 'size' bytes via mmap(MAP_PRIVATE|MAP_ANONYMOUS).
; Returns pointer in rax; negative value = -errno on error.
global _oy_alloc
_oy_alloc:
    push    rbp
    mov     rbp, rsp
    mov     r11, rdi            ; save requested size
    mov     rax, 9              ; SYS_mmap
    xor     rdi, rdi            ; addr   = NULL  (kernel picks)
    mov     rsi, r11            ; length = requested size
    mov     rdx, 3              ; prot   = PROT_READ | PROT_WRITE
    mov     r10, 0x22           ; flags  = MAP_PRIVATE | MAP_ANONYMOUS
    mov     r8,  -1             ; fd     = -1
    xor     r9,  r9             ; offset = 0
    syscall
    pop     rbp
    ret

; ── _oy_free(rdi=ptr, rsi=size) ─────────────────────────────
; Releases a block previously returned by _oy_alloc.
global _oy_free
_oy_free:
    push    rbp
    mov     rbp, rsp
    mov     rax, 11             ; SYS_munmap
    syscall
    pop     rbp
    ret

; ── _oy_halt() ──────────────────────────────────────────────
; Terminates the process with exit code 0.
global _oy_halt
_oy_halt:
    mov     rax, 60             ; SYS_exit
    xor     rdi, rdi            ; status = 0
    syscall

; ── _oy_port_write(rdi=port, rsi=value) ─────────────────────
; Writes one byte 'value' to I/O port 'port'.
; Requires IOPL ≥ 1  (i.e., kernel / ring-0 context).
global _oy_port_write
_oy_port_write:
    mov     dx,  di             ; port  (16-bit)
    mov     al,  sil            ; value (8-bit)
    out     dx,  al
    ret

; ── _oy_port_read(rdi=port) -> rax=value ────────────────────
; Reads one byte from I/O port 'port'.
global _oy_port_read
_oy_port_read:
    mov     dx,  di
    in      al,  dx
    movzx   rax, al
    ret

; ── _oy_memory_map(rdi=addr, rsi=size) -> rax=ptr ───────────
; Maps a fixed physical address range into virtual memory.
; Used for MMIO / hardware register access.
global _oy_memory_map
_oy_memory_map:
    push    rbp
    mov     rbp, rsp
    mov     r11, rdi            ; save fixed addr
    mov     r12, rsi            ; save size
    mov     rax, 9              ; SYS_mmap
    mov     rdi, r11            ; addr   = fixed physical address
    mov     rsi, r12            ; length
    mov     rdx, 3              ; prot   = PROT_READ | PROT_WRITE
    mov     r10, 0x32           ; flags  = MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS
    mov     r8,  -1             ; fd     = -1
    xor     r9,  r9             ; offset = 0
    syscall
    pop     rbp
    ret

; ── _oy_cpu_cpuid(rdi=leaf) -> stores in [rax,rbx,rcx,rdx] ─
; Executes CPUID with the given leaf. Useful for arch detection.
global _oy_cpu_cpuid
_oy_cpu_cpuid:
    push    rbx
    mov     eax, edi
    xor     ecx, ecx
    cpuid
    pop     rbx
    ret
