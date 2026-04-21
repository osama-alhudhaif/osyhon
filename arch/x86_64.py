"""
Osyhon x86_64 Code Generator
Target : Linux  |  ABI: System V AMD64
Assembler syntax: NASM (Intel)

Registers used internally:
  rax  — return value / syscall number
  rbx  — scratch (callee-saved, used for temp storage)
  rdi  — arg 1 / syscall arg 1
  rsi  — arg 2 / syscall arg 2
  rdx  — arg 3 / syscall arg 3
  r10  — syscall arg 4  (mmap flags)
  r8   — syscall arg 5  (mmap fd)
  r9   — syscall arg 6  (mmap offset)
  r12  — loop counter   (callee-saved)

Syscall numbers (Linux x86_64):
  read   = 0    write  = 1    mmap   = 9
  munmap = 11   exit   = 60   iopl   = 172
"""

from arch import CodeGen


# ── Linux syscall numbers ──────────────────────────────────────────────
SYS_READ   = 0
SYS_WRITE  = 1
SYS_MMAP   = 9
SYS_MUNMAP = 11
SYS_EXIT   = 60


class X86_64CodeGen(CodeGen):

    def _comment_char(self) -> str:
        return ";"

    # ------------------------------------------------------------------ #
    # Header / Footer / Data
    # ------------------------------------------------------------------ #

    def _emit_header(self):
        self._emit("; ============================================================")
        self._emit(";  Osyhon — x86_64 (Linux / NASM Intel syntax)")
        self._emit("; ============================================================")
        self._emit("bits 64")
        self._emit("default rel")
        self._emit()
        self._emit("section .text")
        self._emit("    global _start")
        self._emit()
        self._emit_runtime()

    def _emit_footer(self):
        self._emit()
        self._emit("; ── entry point ──────────────────────────────────────────")
        self._emit("_start:")
        self._emit("    call    oy_kernel_start")
        self._emit("    mov     rax, {SYS_EXIT}".replace("{SYS_EXIT}", str(SYS_EXIT)))
        self._emit("    xor     rdi, rdi")
        self._emit("    syscall")

    def _emit_data_section(self):
        if not self._strings:
            return
        self._emit()
        self._emit("section .data")
        for label, value in self._strings.items():
            escaped = value.replace("\\n", '", 0x0A, "')
            self._emit(f'    {label}     db "{escaped}", 0')
            self._emit(f'    {label}_len equ $ - {label} - 1')
        self._emit()
        self._emit("    _newline    db 0x0A")
        self._emit("    _newline_len equ 1")

    # ------------------------------------------------------------------ #
    # Built-in runtime functions (always emitted)
    # ------------------------------------------------------------------ #

    def _emit_runtime(self):
        self._emit("; ── _oy_print(rdi=ptr, rsi=len) ───────────────────────────")
        self._emit("_oy_print:")
        self._emit("    push    rbp")
        self._emit("    mov     rbp, rsp")
        self._emit(f"    mov     rax, {SYS_WRITE}")
        self._emit("    mov     rdx, rsi            ; len")
        self._emit("    mov     rsi, rdi            ; ptr")
        self._emit("    mov     rdi, 1              ; stdout")
        self._emit("    syscall")
        self._emit("    pop     rbp")
        self._emit("    ret")
        self._emit()

        self._emit("; ── _oy_print_int(rdi=number) ─────────────────────────────")
        self._emit("_oy_print_int:")
        self._emit("    push    rbp")
        self._emit("    mov     rbp, rsp")
        self._emit("    sub     rsp, 32")
        self._emit("    lea     rsi, [rsp+31]")
        self._emit("    mov     byte [rsi], 0x0A    ; trailing newline")
        self._emit("    dec     rsi")
        self._emit("    mov     rax, rdi")
        self._emit("    mov     r9,  10")
        self._emit("    test    rax, rax")
        self._emit("    jns     .convert")
        self._emit("    neg     rax")
        self._emit(".convert:")
        self._emit("    xor     rdx, rdx")
        self._emit("    div     r9")
        self._emit("    add     dl, '0'")
        self._emit("    mov     [rsi], dl")
        self._emit("    dec     rsi")
        self._emit("    test    rax, rax")
        self._emit("    jnz     .convert")
        self._emit("    test    rdi, rdi")
        self._emit("    jns     .no_neg")
        self._emit("    mov     byte [rsi], '-'")
        self._emit("    dec     rsi")
        self._emit(".no_neg:")
        self._emit("    inc     rsi")
        self._emit(f"    mov     rax, {SYS_WRITE}")
        self._emit("    mov     rdi, 1")
        self._emit("    lea     rdx, [rsp+32]")
        self._emit("    sub     rdx, rsi            ; len")
        self._emit("    syscall")
        self._emit("    add     rsp, 32")
        self._emit("    pop     rbp")
        self._emit("    ret")
        self._emit()

        self._emit("; ── _oy_alloc(rdi=size) -> rax=ptr ───────────────────────")
        self._emit("_oy_alloc:")
        self._emit("    push    rbp")
        self._emit("    mov     rbp, rsp")
        self._emit("    mov     r10, rdi            ; save size")
        self._emit(f"    mov     rax, {SYS_MMAP}")
        self._emit("    xor     rdi, rdi            ; addr = NULL (kernel chooses)")
        self._emit("    mov     rsi, r10            ; length")
        self._emit("    mov     rdx, 3              ; PROT_READ | PROT_WRITE")
        self._emit("    mov     r10, 0x22           ; MAP_PRIVATE | MAP_ANONYMOUS")
        self._emit("    mov     r8,  -1             ; fd = -1")
        self._emit("    xor     r9,  r9             ; offset = 0")
        self._emit("    syscall                     ; rax = ptr or -errno")
        self._emit("    pop     rbp")
        self._emit("    ret")
        self._emit()

        self._emit("; ── _oy_free(rdi=ptr, rsi=size) ──────────────────────────")
        self._emit("_oy_free:")
        self._emit("    push    rbp")
        self._emit("    mov     rbp, rsp")
        self._emit(f"    mov     rax, {SYS_MUNMAP}")
        self._emit("    syscall")
        self._emit("    pop     rbp")
        self._emit("    ret")
        self._emit()

        self._emit("; ── _oy_halt() ────────────────────────────────────────────")
        self._emit("_oy_halt:")
        self._emit(f"    mov     rax, {SYS_EXIT}")
        self._emit("    xor     rdi, rdi")
        self._emit("    syscall")
        self._emit()

        self._emit("; ── _oy_port_write(rdi=port, rsi=value) ──────────────────")
        self._emit("; ── NOTE: requires IOPL=3 (kernel mode / privileged) ─────")
        self._emit("_oy_port_write:")
        self._emit("    mov     dx, di              ; port number (16-bit)")
        self._emit("    mov     al, sil             ; byte value")
        self._emit("    out     dx, al")
        self._emit("    ret")
        self._emit()

        self._emit("; ── _oy_memory_map(rdi=addr, rsi=size) -> rax=ptr ────────")
        self._emit("_oy_memory_map:")
        self._emit("    push    rbp")
        self._emit("    mov     rbp, rsp")
        self._emit("    mov     r10, rdi")
        self._emit("    mov     r11, rsi")
        self._emit(f"    mov     rax, {SYS_MMAP}")
        self._emit("    mov     rdi, r10            ; fixed address")
        self._emit("    mov     rsi, r11            ; size")
        self._emit("    mov     rdx, 3              ; PROT_READ | PROT_WRITE")
        self._emit("    mov     r10, 0x32           ; MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS")
        self._emit("    mov     r8,  -1")
        self._emit("    xor     r9,  r9")
        self._emit("    syscall")
        self._emit("    pop     rbp")
        self._emit("    ret")
        self._emit()

    # ------------------------------------------------------------------ #
    # Node generation
    # ------------------------------------------------------------------ #

    def _gen_node(self, node: dict):
        kind = node["type"]

        if kind == "kernel_start":
            self._emit()
            self._emit("; ── kernel_start ──────────────────────────────────────")
            self._emit("oy_kernel_start:")
            self._emit("    push    rbp")
            self._emit("    mov     rbp, rsp")
            for child in node["body"]:
                self._gen_node(child)
            self._emit("    pop     rbp")
            self._emit("    ret")

        elif kind == "func_def":
            self._emit()
            self._emit(f"; ── def {node['name']} ──────────────────────────────")
            self._emit(f"oy_{node['name']}:")
            self._emit("    push    rbp")
            self._emit("    mov     rbp, rsp")
            arg_regs = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]
            for i, arg in enumerate(node.get("args", [])):
                if i < len(arg_regs):
                    self._emit(f"    ; arg '{arg}' is in {arg_regs[i]}")
                    self._vars[arg] = arg_regs[i]
            for child in node["body"]:
                self._gen_node(child)
            self._emit("    pop     rbp")
            self._emit("    ret")

        elif kind == "print_stmt":
            self._gen_print(node["value"])

        elif kind == "alloc":
            size_expr = node["size"]
            self._gen_expr(size_expr, "rdi")
            self._emit("    call    _oy_alloc")
            self._vars[node["var"]] = "rax"
            self._emit(f"    ; '{node['var']}' points to allocated block (rax)")

        elif kind == "free":
            var = node["var"]
            reg = self._vars.get(var, "rdi")
            if reg != "rdi":
                self._emit(f"    mov     rdi, {reg}")
            self._emit(f"    mov     rsi, 0          ; caller must set correct size")
            self._emit("    call    _oy_free")

        elif kind == "assign":
            self._gen_expr(node["value"], "rax")
            self._vars[node["var"]] = "rax"
            self._emit(f"    ; '{node['var']}' = rax")

        elif kind == "if_stmt":
            lbl_else = self._new_label(".Lelse")
            lbl_end  = self._new_label(".Lend")
            self._gen_condition(node["cond"], lbl_else)
            for child in node["body"]:
                self._gen_node(child)
            self._emit(f"    jmp     {lbl_end}")
            self._emit(f"{lbl_else}:")
            for child in node.get("else_body", []):
                self._gen_node(child)
            self._emit(f"{lbl_end}:")

        elif kind == "for_stmt":
            lbl_loop  = self._new_label(".Lloop")
            lbl_check = self._new_label(".Lcheck")
            self._emit("    xor     r12, r12        ; loop counter = 0")
            self._vars[node["var"]] = "r12"
            self._emit(f"    jmp     {lbl_check}")
            self._emit(f"{lbl_loop}:")
            for child in node["body"]:
                self._gen_node(child)
            self._emit("    inc     r12")
            self._emit(f"{lbl_check}:")
            self._gen_expr(node["end"], "rbx")
            self._emit("    cmp     r12, rbx")
            self._emit(f"    jl      {lbl_loop}")

        elif kind == "call":
            arg_regs = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]
            for i, arg in enumerate(node.get("args", [])):
                if i < len(arg_regs):
                    self._gen_expr(arg, arg_regs[i])
            self._emit(f"    call    oy_{node['name']}")

        elif kind == "return_stmt":
            self._gen_expr(node["value"], "rax")
            self._emit("    pop     rbp")
            self._emit("    ret")

        elif kind == "memory_map":
            self._gen_expr(node["addr"], "rdi")
            self._gen_expr(node["size"], "rsi")
            self._emit("    call    _oy_memory_map")

        elif kind == "port_write":
            self._gen_expr(node["port"],  "rdi")
            self._gen_expr(node["value"], "rsi")
            self._emit("    call    _oy_port_write")

        elif kind == "cpu_halt":
            self._emit("    call    _oy_halt")

        elif kind == "query":
            target = node["target"]
            self._emit(f"    ; query: {target}?  (resolved at runtime by driver)")

        else:
            self._emit(f"    ; [x86_64] unknown node: {kind}")

    # ------------------------------------------------------------------ #
    # Expression generation  → result in dest_reg
    # ------------------------------------------------------------------ #

    def _gen_expr(self, expr: dict, dest_reg: str):
        kind = expr["type"]

        if kind == "int_lit":
            self._emit(f"    mov     {dest_reg}, {expr['value']}")

        elif kind == "str_lit":
            label = self._intern_string(expr["value"])
            self._emit(f"    lea     {dest_reg}, [{label}]")

        elif kind == "var_ref":
            src = self._vars.get(expr["name"], "0")
            if src != dest_reg:
                self._emit(f"    mov     {dest_reg}, {src}")

        elif kind == "binop":
            self._gen_expr(expr["left"],  dest_reg)
            self._emit("    push    rax")
            self._gen_expr(expr["right"], "rbx")
            self._emit("    pop     rax")
            op = expr["op"]
            if op == "+":
                self._emit(f"    add     {dest_reg}, rbx")
            elif op == "-":
                self._emit(f"    sub     {dest_reg}, rbx")
            elif op == "*":
                self._emit(f"    imul    {dest_reg}, rbx")
            elif op == "/":
                self._emit("    xor     rdx, rdx")
                self._emit("    idiv    rbx")

        elif kind == "compare":
            self._gen_expr(expr["left"],  "rax")
            self._gen_expr(expr["right"], "rbx")
            self._emit("    cmp     rax, rbx")

    # ------------------------------------------------------------------ #
    # Condition → jump to lbl_false if condition is false
    # ------------------------------------------------------------------ #

    def _gen_condition(self, cond: dict, lbl_false: str):
        self._gen_expr(cond, "rax")
        op = cond.get("op", "==")
        jump_map = {
            "==": "jne", "!=": "je",
            "<":  "jge", ">":  "jle",
            "<=": "jg",  ">=": "jl",
        }
        jmp = jump_map.get(op, "jne")
        self._emit(f"    {jmp}     {lbl_false}")

    # ------------------------------------------------------------------ #
    # Print helper
    # ------------------------------------------------------------------ #

    def _gen_print(self, expr: dict):
        kind = expr["type"]
        if kind == "str_lit":
            label = self._intern_string(expr["value"])
            self._emit(f"    lea     rdi, [{label}]")
            self._emit(f"    mov     rsi, {label}_len")
            self._emit("    call    _oy_print")
            self._emit("    ; print newline")
            self._emit("    lea     rdi, [_newline]")
            self._emit("    mov     rsi, 1")
            self._emit("    call    _oy_print")
        elif kind == "int_lit":
            self._emit(f"    mov     rdi, {expr['value']}")
            self._emit("    call    _oy_print_int")
        elif kind == "var_ref":
            src = self._vars.get(expr["name"], "0")
            if src != "rdi":
                self._emit(f"    mov     rdi, {src}")
            self._emit("    call    _oy_print_int")
        else:
            self._gen_expr(expr, "rdi")
            self._emit("    call    _oy_print_int")
