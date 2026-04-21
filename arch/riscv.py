"""
Osyhon RISC-V 64-bit Code Generator
Target : Linux  |  ABI: RISC-V LP64D
Assembler syntax: GNU AS (RV64I base ISA)

Register conventions (RISC-V ABI):
  zero (x0)  — hardwired zero
  ra   (x1)  — return address
  sp   (x2)  — stack pointer
  gp   (x3)  — global pointer
  tp   (x4)  — thread pointer
  t0–t2 (x5–x7)  — caller-saved temporaries
  s0/fp (x8)     — frame pointer / callee-saved
  s1   (x9)  — callee-saved
  a0–a7 (x10–x17) — function args / return / syscall args
  a7   (x17) — syscall number  ← Linux convention
  s2–s11 (x18–x27) — callee-saved
  t3–t6  (x28–x31) — caller-saved temporaries

Internal usage:
  a0  — arg1 / return value
  a1  — arg2
  a2  — arg3
  a7  — syscall number
  s1  — loop counter (callee-saved)
  s2  — scratch      (callee-saved)

Syscall numbers (Linux RV64):
  read   = 63    write  = 64    mmap   = 222
  munmap = 215   exit   = 93
"""

from arch import CodeGen


SYS_READ   = 63
SYS_WRITE  = 64
SYS_MMAP   = 222
SYS_MUNMAP = 215
SYS_EXIT   = 93


class RISCVCodeGen(CodeGen):

    def _comment_char(self) -> str:
        return "#"

    # ------------------------------------------------------------------ #
    # Header / Footer / Data
    # ------------------------------------------------------------------ #

    def _emit_header(self):
        self._emit("# ============================================================")
        self._emit("#  Osyhon — RISC-V 64-bit (Linux / GNU AS RV64I)")
        self._emit("# ============================================================")
        self._emit(".option nopic")
        self._emit(".attribute arch, \"rv64i2p0_m2p0\"")  # M extension: mul/div/rem
        self._emit(".text")
        self._emit(".global _start")
        self._emit()
        self._emit_runtime()

    def _emit_footer(self):
        self._emit()
        self._emit("# ── entry point ───────────────────────────────────────────")
        self._emit("_start:")
        self._emit("    addi    sp, sp, -16")
        self._emit("    sd      ra, 8(sp)")
        self._emit("    sd      s0, 0(sp)")
        self._emit("    addi    s0, sp, 16")
        self._emit("    call    oy_kernel_start")
        self._emit(f"    li      a7, {SYS_EXIT}")
        self._emit("    li      a0, 0")
        self._emit("    ecall")

    def _emit_data_section(self):
        if not self._strings:
            return
        self._emit()
        self._emit(".data")
        for label, value in self._strings.items():
            escaped = value.replace("\\n", "\\n")
            self._emit(f"{label}:")
            self._emit(f'    .string "{escaped}"')
            self._emit(f".set {label}_len, . - {label} - 1")
        self._emit()
        self._emit("_newline:")
        self._emit("    .byte 0x0A")
        self._emit(".set _newline_len, 1")
        self._emit("")

    # ------------------------------------------------------------------ #
    # Built-in runtime
    # ------------------------------------------------------------------ #

    def _emit_runtime(self):
        self._emit("# ── _oy_print(a0=ptr, a1=len) ─────────────────────────────")
        self._emit("_oy_print:")
        self._emit("    addi    sp, sp, -16")
        self._emit("    sd      ra, 8(sp)")
        self._emit("    mv      a2, a1              # len")
        self._emit("    mv      a1, a0              # ptr")
        self._emit("    li      a0, 1               # stdout (fd=1)")
        self._emit(f"    li      a7, {SYS_WRITE}")
        self._emit("    ecall")
        self._emit("    ld      ra, 8(sp)")
        self._emit("    addi    sp, sp, 16")
        self._emit("    ret")
        self._emit()

        self._emit("# ── _oy_print_int(a0=number) ──────────────────────────────")
        self._emit("# Frame layout (80 bytes):")
        self._emit("#   sp+0..sp+7  : saved ra  (bottom, safe from buffer)")
        self._emit("#   sp+8..sp+79 : digit buffer (top-down, max 20 digits + newline)")
        self._emit("_oy_print_int:")
        self._emit("    addi    sp, sp, -80")
        self._emit("    sd      ra, 0(sp)            # save ra at bottom of frame")
        self._emit("    addi    t0, sp, 79           # t0 = top of buffer")
        self._emit("    li      t1, 0x0A")
        self._emit("    sb      t1, 0(t0)            # trailing newline at sp+79")
        self._emit("    addi    t0, t0, -1           # t0 = sp+78 (first digit slot)")
        self._emit("    mv      t2, a0              # number")
        self._emit("    li      t3, 10")
        self._emit(".Lprint_int_loop:")
        self._emit("    remu    t4, t2, t3          # remainder")
        self._emit("    addi    t4, t4, 48          # '0' = 48")
        self._emit("    sb      t4, 0(t0)")
        self._emit("    addi    t0, t0, -1")
        self._emit("    divu    t2, t2, t3")
        self._emit("    bnez    t2, .Lprint_int_loop")
        self._emit("    addi    a1, t0, 1           # start of number string")
        self._emit("    addi    a2, sp, 80          # one past end (sp+80 = caller sp)")
        self._emit("    sub     a2, a2, a1          # length = (sp+79 - t0)")
        self._emit("    li      a0, 1               # stdout")
        self._emit(f"    li      a7, {SYS_WRITE}")
        self._emit("    ecall")
        self._emit("    ld      ra, 0(sp)           # restore ra from bottom of frame")
        self._emit("    addi    sp, sp, 80")
        self._emit("    ret")
        self._emit()

        self._emit("# ── _oy_alloc(a0=size) -> a0=ptr ──────────────────────────")
        self._emit("_oy_alloc:")
        self._emit("    addi    sp, sp, -16")
        self._emit("    sd      ra, 8(sp)")
        self._emit("    mv      a1, a0              # length")
        self._emit("    li      a0, 0               # addr = NULL")
        self._emit("    li      a2, 3               # PROT_READ | PROT_WRITE")
        self._emit("    li      a3, 0x22            # MAP_PRIVATE | MAP_ANONYMOUS")
        self._emit("    li      a4, -1              # fd = -1")
        self._emit("    li      a5, 0               # offset = 0")
        self._emit(f"    li      a7, {SYS_MMAP}")
        self._emit("    ecall                       # a0 = ptr or -errno")
        self._emit("    ld      ra, 8(sp)")
        self._emit("    addi    sp, sp, 16")
        self._emit("    ret")
        self._emit()

        self._emit("# ── _oy_free(a0=ptr, a1=size) ─────────────────────────────")
        self._emit("_oy_free:")
        self._emit("    addi    sp, sp, -16")
        self._emit("    sd      ra, 8(sp)")
        self._emit(f"    li      a7, {SYS_MUNMAP}")
        self._emit("    ecall")
        self._emit("    ld      ra, 8(sp)")
        self._emit("    addi    sp, sp, 16")
        self._emit("    ret")
        self._emit()

        self._emit("# ── _oy_halt() ─────────────────────────────────────────────")
        self._emit("_oy_halt:")
        self._emit(f"    li      a7, {SYS_EXIT}")
        self._emit("    li      a0, 0")
        self._emit("    ecall")
        self._emit()

        self._emit("# ── _oy_port_write(a0=mmio_addr, a1=value) ────────────────")
        self._emit("# ── NOTE: RISC-V uses MMIO — no IN/OUT instructions ────────")
        self._emit("_oy_port_write:")
        self._emit("    sw      a1, 0(a0)           # MMIO write: store value at address")
        self._emit("    fence   ow, ow              # memory ordering fence")
        self._emit("    ret")
        self._emit()

        self._emit("# ── _oy_memory_map(a0=addr, a1=size) -> a0=ptr ────────────")
        self._emit("_oy_memory_map:")
        self._emit("    addi    sp, sp, -16")
        self._emit("    sd      ra, 8(sp)")
        self._emit("    li      a2, 3               # PROT_READ | PROT_WRITE")
        self._emit("    li      a3, 0x32            # MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS")
        self._emit("    li      a4, -1              # fd = -1")
        self._emit("    li      a5, 0               # offset = 0")
        self._emit(f"    li      a7, {SYS_MMAP}")
        self._emit("    ecall")
        self._emit("    ld      ra, 8(sp)")
        self._emit("    addi    sp, sp, 16")
        self._emit("    ret")
        self._emit()

    # ------------------------------------------------------------------ #
    # Node generation
    # ------------------------------------------------------------------ #

    def _gen_node(self, node: dict):
        kind = node["type"]

        if kind == "kernel_start":
            self._emit()
            self._emit("# ── kernel_start ───────────────────────────────────────")
            self._emit("oy_kernel_start:")
            self._emit("    addi    sp, sp, -16")
            self._emit("    sd      ra, 8(sp)")
            self._emit("    sd      s0, 0(sp)")
            self._emit("    addi    s0, sp, 16")
            for child in node["body"]:
                self._gen_node(child)
            self._emit("    ld      ra, 8(sp)")
            self._emit("    ld      s0, 0(sp)")
            self._emit("    addi    sp, sp, 16")
            self._emit("    ret")

        elif kind == "func_def":
            self._emit()
            self._emit(f"# ── def {node['name']} ──────────────────────────────")
            self._emit(f"oy_{node['name']}:")
            self._emit("    addi    sp, sp, -16")
            self._emit("    sd      ra, 8(sp)")
            self._emit("    sd      s0, 0(sp)")
            self._emit("    addi    s0, sp, 16")
            arg_regs = ["a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"]
            for i, arg in enumerate(node.get("args", [])):
                if i < len(arg_regs):
                    self._vars[arg] = arg_regs[i]
            for child in node["body"]:
                self._gen_node(child)
            self._emit("    ld      ra, 8(sp)")
            self._emit("    ld      s0, 0(sp)")
            self._emit("    addi    sp, sp, 16")
            self._emit("    ret")

        elif kind == "print_stmt":
            self._gen_print(node["value"])

        elif kind == "alloc":
            self._gen_expr(node["size"], "a0")
            self._emit("    call    _oy_alloc")
            self._vars[node["var"]] = "a0"

        elif kind == "free":
            reg = self._vars.get(node["var"], "a0")
            if reg != "a0":
                self._emit(f"    mv      a0, {reg}")
            self._emit("    li      a1, 0           # caller must set correct size")
            self._emit("    call    _oy_free")

        elif kind == "assign":
            self._gen_expr(node["value"], "a0")
            self._vars[node["var"]] = "a0"

        elif kind == "if_stmt":
            lbl_else = self._new_label(".Lelse")
            lbl_end  = self._new_label(".Lend")
            self._gen_condition(node["cond"], lbl_else)
            for child in node["body"]:
                self._gen_node(child)
            self._emit(f"    j       {lbl_end}")
            self._emit(f"{lbl_else}:")
            for child in node.get("else_body", []):
                self._gen_node(child)
            self._emit(f"{lbl_end}:")

        elif kind == "for_stmt":
            lbl_loop  = self._new_label(".Lloop")
            lbl_check = self._new_label(".Lcheck")
            self._emit("    li      s1, 0           # loop counter = 0")
            self._vars[node["var"]] = "s1"
            self._emit(f"    j       {lbl_check}")
            self._emit(f"{lbl_loop}:")
            for child in node["body"]:
                self._gen_node(child)
            self._emit("    addi    s1, s1, 1")
            self._emit(f"{lbl_check}:")
            self._gen_expr(node["end"], "s2")
            self._emit("    blt     s1, s2, " + lbl_loop)

        elif kind == "call":
            arg_regs = ["a0", "a1", "a2", "a3", "a4", "a5", "a6"]
            for i, arg in enumerate(node.get("args", [])):
                if i < len(arg_regs):
                    self._gen_expr(arg, arg_regs[i])
            self._emit(f"    call    oy_{node['name']}")

        elif kind == "return_stmt":
            self._gen_expr(node["value"], "a0")
            self._emit("    ld      ra, 8(sp)")
            self._emit("    ld      s0, 0(sp)")
            self._emit("    addi    sp, sp, 16")
            self._emit("    ret")

        elif kind == "memory_map":
            self._gen_expr(node["addr"], "a0")
            self._gen_expr(node["size"], "a1")
            self._emit("    call    _oy_memory_map")

        elif kind == "port_write":
            self._gen_expr(node["port"],  "a0")
            self._gen_expr(node["value"], "a1")
            self._emit("    call    _oy_port_write")

        elif kind == "cpu_halt":
            self._emit("    call    _oy_halt")

        elif kind == "query":
            self._emit(f"    # query: {node['target']}?  (resolved at runtime by driver)")

        else:
            self._emit(f"    # [riscv] unknown node: {kind}")

    # ------------------------------------------------------------------ #
    # Expression → dest_reg
    # ------------------------------------------------------------------ #

    def _gen_expr(self, expr: dict, dest_reg: str):
        kind = expr["type"]

        if kind == "int_lit":
            self._emit(f"    li      {dest_reg}, {expr['value']}")

        elif kind == "str_lit":
            label = self._intern_string(expr["value"])
            self._emit(f"    la      {dest_reg}, {label}")

        elif kind == "var_ref":
            src = self._vars.get(expr["name"], "a0")
            if src != dest_reg:
                self._emit(f"    mv      {dest_reg}, {src}")

        elif kind == "binop":
            self._gen_expr(expr["left"], dest_reg)
            self._emit("    addi    sp, sp, -8")
            self._emit(f"    sd      {dest_reg}, 0(sp)")
            self._gen_expr(expr["right"], "t0")
            self._emit(f"    ld      {dest_reg}, 0(sp)")
            self._emit("    addi    sp, sp, 8")
            op = expr["op"]
            if op == "+":
                self._emit(f"    add     {dest_reg}, {dest_reg}, t0")
            elif op == "-":
                self._emit(f"    sub     {dest_reg}, {dest_reg}, t0")
            elif op == "*":
                self._emit(f"    mul     {dest_reg}, {dest_reg}, t0")
            elif op == "/":
                self._emit(f"    div     {dest_reg}, {dest_reg}, t0")

        elif kind == "compare":
            self._gen_expr(expr["left"],  "a0")
            self._gen_expr(expr["right"], "t0")

    # ------------------------------------------------------------------ #
    # Condition → branch to lbl_false if false
    # ------------------------------------------------------------------ #

    def _gen_condition(self, cond: dict, lbl_false: str):
        self._gen_expr(cond, "a0")
        op = cond.get("op", "==")
        branch_map = {
            "==": "bne",  "!=": "beq",
            "<":  "bge",  ">":  "ble",
            "<=": "bgt",  ">=": "blt",
        }
        br = branch_map.get(op, "bne")
        self._emit(f"    {br}     a0, t0, {lbl_false}")

    # ------------------------------------------------------------------ #
    # Print helper
    # ------------------------------------------------------------------ #

    def _gen_print(self, expr: dict):
        kind = expr["type"]
        if kind == "str_lit":
            label = self._intern_string(expr["value"])
            length = len(expr["value"])
            self._emit(f"    la      a0, {label}")
            self._emit(f"    li      a1, {length}")
            self._emit("    call    _oy_print")
            self._emit("    la      a0, _newline")
            self._emit("    li      a1, 1")
            self._emit("    call    _oy_print")
        elif kind == "int_lit":
            self._emit(f"    li      a0, {expr['value']}")
            self._emit("    call    _oy_print_int")
        elif kind == "var_ref":
            src = self._vars.get(expr["name"], "a0")
            if src != "a0":
                self._emit(f"    mv      a0, {src}")
            self._emit("    call    _oy_print_int")
        else:
            self._gen_expr(expr, "a0")
            self._emit("    call    _oy_print_int")
