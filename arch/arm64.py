"""
Osyhon ARM64 / AArch64 Code Generator
Target : Linux  |  ABI: AAPCS64
Assembler syntax: GNU AS

Register conventions (AAPCS64):
  x0–x7   — function arguments / return values
  x8      — indirect result / syscall number
  x9–x15  — caller-saved temporaries
  x19–x28 — callee-saved
  x29     — frame pointer (fp)
  x30     — link register  (lr)
  sp      — stack pointer

Internal usage:
  x0  — arg1 / return value
  x1  — arg2
  x2  — arg3
  x8  — syscall number
  x19 — loop counter (callee-saved)
  x20 — scratch      (callee-saved)

Syscall numbers (Linux AArch64):
  read   = 63    write  = 64    mmap   = 222
  munmap = 215   exit   = 93
"""

from arch import CodeGen


SYS_READ   = 63
SYS_WRITE  = 64
SYS_MMAP   = 222
SYS_MUNMAP = 215
SYS_EXIT   = 93


class ARM64CodeGen(CodeGen):

    def _comment_char(self) -> str:
        return "//"

    # ------------------------------------------------------------------ #
    # Header / Footer / Data
    # ------------------------------------------------------------------ #

    def _emit_header(self):
        self._emit("// ============================================================")
        self._emit("//  Osyhon — ARM64 / AArch64 (Linux / GNU AS)")
        self._emit("// ============================================================")
        self._emit(".arch armv8-a")
        self._emit(".text")
        self._emit(".global _start")
        self._emit()
        self._emit_runtime()

    def _emit_footer(self):
        self._emit()
        self._emit("// ── entry point ───────────────────────────────────────────")
        self._emit("_start:")
        self._emit("    stp     x29, x30, [sp, #-16]!")
        self._emit("    mov     x29, sp")
        self._emit("    bl      oy_kernel_start")
        self._emit(f"    mov     x8,  #{SYS_EXIT}")
        self._emit("    mov     x0,  #0")
        self._emit("    svc     #0")

    def _emit_data_section(self):
        if not self._strings:
            return
        self._emit()
        self._emit(".data")
        for label, value in self._strings.items():
            escaped = value.replace("\\n", "\\n")
            self._emit(f'{label}:')
            self._emit(f'    .asciz "{escaped}"')
            self._emit(f'{label}_len = . - {label} - 1')
        self._emit()
        self._emit("_newline:")
        self._emit("    .byte 0x0A")
        self._emit("_newline_len = 1")
        self._emit("")

    # ------------------------------------------------------------------ #
    # Built-in runtime
    # ------------------------------------------------------------------ #

    def _emit_runtime(self):
        self._emit("// ── _oy_print(x0=ptr, x1=len) ─────────────────────────────")
        self._emit("_oy_print:")
        self._emit("    stp     x29, x30, [sp, #-16]!")
        self._emit("    mov     x29, sp")
        self._emit("    mov     x2,  x1             // len")
        self._emit("    mov     x1,  x0             // ptr")
        self._emit("    mov     x0,  #1             // stdout")
        self._emit(f"    mov     x8,  #{SYS_WRITE}")
        self._emit("    svc     #0")
        self._emit("    ldp     x29, x30, [sp], #16")
        self._emit("    ret")
        self._emit()

        self._emit("// ── _oy_print_int(x0=number) ──────────────────────────────")
        self._emit("_oy_print_int:")
        self._emit("    stp     x29, x30, [sp, #-64]!")
        self._emit("    mov     x29, sp")
        self._emit("    mov     x9,  sp")
        self._emit("    add     x9,  x9, #63")
        self._emit("    mov     x10, #0x0A")
        self._emit("    strb    w10, [x9]")
        self._emit("    sub     x9,  x9, #1")
        self._emit("    mov     x1,  x0             // number")
        self._emit("    mov     x11, #10")
        self._emit(".Lprint_int_loop:")
        self._emit("    udiv    x12, x1, x11")
        self._emit("    msub    x13, x12, x11, x1   // remainder")
        self._emit("    add     w13, w13, #'0'")
        self._emit("    strb    w13, [x9]")
        self._emit("    sub     x9,  x9, #1")
        self._emit("    mov     x1,  x12")
        self._emit("    cbnz    x1,  .Lprint_int_loop")
        self._emit("    add     x1,  x9, #1         // start of number")
        self._emit("    add     x2,  sp,  #64")
        self._emit("    sub     x2,  x2,  x1        // length")
        self._emit("    mov     x0,  #1             // stdout")
        self._emit(f"    mov     x8,  #{SYS_WRITE}")
        self._emit("    svc     #0")
        self._emit("    ldp     x29, x30, [sp], #64")
        self._emit("    ret")
        self._emit()

        self._emit("// ── _oy_alloc(x0=size) -> x0=ptr ──────────────────────────")
        self._emit("_oy_alloc:")
        self._emit("    stp     x29, x30, [sp, #-16]!")
        self._emit("    mov     x29, sp")
        self._emit("    mov     x1,  x0             // length")
        self._emit("    mov     x0,  #0             // addr = NULL")
        self._emit("    mov     x2,  #3             // PROT_READ | PROT_WRITE")
        self._emit("    mov     x3,  #0x22          // MAP_PRIVATE | MAP_ANONYMOUS")
        self._emit("    mov     x4,  #-1            // fd = -1")
        self._emit("    mov     x5,  #0             // offset = 0")
        self._emit(f"    mov     x8,  #{SYS_MMAP}")
        self._emit("    svc     #0                  // x0 = ptr or -errno")
        self._emit("    ldp     x29, x30, [sp], #16")
        self._emit("    ret")
        self._emit()

        self._emit("// ── _oy_free(x0=ptr, x1=size) ─────────────────────────────")
        self._emit("_oy_free:")
        self._emit("    stp     x29, x30, [sp, #-16]!")
        self._emit("    mov     x29, sp")
        self._emit(f"    mov     x8,  #{SYS_MUNMAP}")
        self._emit("    svc     #0")
        self._emit("    ldp     x29, x30, [sp], #16")
        self._emit("    ret")
        self._emit()

        self._emit("// ── _oy_halt() ─────────────────────────────────────────────")
        self._emit("_oy_halt:")
        self._emit(f"    mov     x8,  #{SYS_EXIT}")
        self._emit("    mov     x0,  #0")
        self._emit("    svc     #0")
        self._emit()

        self._emit("// ── _oy_port_write(x0=port, x1=value) ─────────────────────")
        self._emit("// ── NOTE: ARM64 has no IN/OUT — use MMIO instead ───────────")
        self._emit("_oy_port_write:")
        self._emit("    str     w1, [x0]            // MMIO: write value to port address")
        self._emit("    ret")
        self._emit()

        self._emit("// ── _oy_memory_map(x0=addr, x1=size) -> x0=ptr ────────────")
        self._emit("_oy_memory_map:")
        self._emit("    stp     x29, x30, [sp, #-16]!")
        self._emit("    mov     x29, sp")
        self._emit("    mov     x2,  #3             // PROT_READ | PROT_WRITE")
        self._emit("    mov     x3,  #0x32          // MAP_FIXED | MAP_PRIVATE | MAP_ANONYMOUS")
        self._emit("    mov     x4,  #-1")
        self._emit("    mov     x5,  #0")
        self._emit(f"    mov     x8,  #{SYS_MMAP}")
        self._emit("    svc     #0")
        self._emit("    ldp     x29, x30, [sp], #16")
        self._emit("    ret")
        self._emit()

    # ------------------------------------------------------------------ #
    # Node generation
    # ------------------------------------------------------------------ #

    def _gen_node(self, node: dict):
        kind = node["type"]

        if kind == "kernel_start":
            self._emit()
            self._emit("// ── kernel_start ───────────────────────────────────────")
            self._emit("oy_kernel_start:")
            self._emit("    stp     x29, x30, [sp, #-16]!")
            self._emit("    mov     x29, sp")
            for child in node["body"]:
                self._gen_node(child)
            self._emit("    ldp     x29, x30, [sp], #16")
            self._emit("    ret")

        elif kind == "func_def":
            self._emit()
            self._emit(f"// ── def {node['name']} ──────────────────────────────")
            self._emit(f"oy_{node['name']}:")
            self._emit("    stp     x29, x30, [sp, #-16]!")
            self._emit("    mov     x29, sp")
            arg_regs = ["x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7"]
            for i, arg in enumerate(node.get("args", [])):
                if i < len(arg_regs):
                    self._vars[arg] = arg_regs[i]
            for child in node["body"]:
                self._gen_node(child)
            self._emit("    ldp     x29, x30, [sp], #16")
            self._emit("    ret")

        elif kind == "print_stmt":
            self._gen_print(node["value"])

        elif kind == "alloc":
            self._gen_expr(node["size"], "x0")
            self._emit("    bl      _oy_alloc")
            self._vars[node["var"]] = "x0"

        elif kind == "free":
            reg = self._vars.get(node["var"], "x0")
            if reg != "x0":
                self._emit(f"    mov     x0, {reg}")
            self._emit("    mov     x1, #0          // caller must set correct size")
            self._emit("    bl      _oy_free")

        elif kind == "assign":
            self._gen_expr(node["value"], "x0")
            self._vars[node["var"]] = "x0"

        elif kind == "if_stmt":
            lbl_else = self._new_label(".Lelse")
            lbl_end  = self._new_label(".Lend")
            self._gen_condition(node["cond"], lbl_else)
            for child in node["body"]:
                self._gen_node(child)
            self._emit(f"    b       {lbl_end}")
            self._emit(f"{lbl_else}:")
            for child in node.get("else_body", []):
                self._gen_node(child)
            self._emit(f"{lbl_end}:")

        elif kind == "for_stmt":
            lbl_loop  = self._new_label(".Lloop")
            lbl_check = self._new_label(".Lcheck")
            self._emit("    mov     x19, #0         // loop counter = 0")
            self._vars[node["var"]] = "x19"
            self._emit(f"    b       {lbl_check}")
            self._emit(f"{lbl_loop}:")
            for child in node["body"]:
                self._gen_node(child)
            self._emit("    add     x19, x19, #1")
            self._emit(f"{lbl_check}:")
            self._gen_expr(node["end"], "x20")
            self._emit("    cmp     x19, x20")
            self._emit(f"    b.lt    {lbl_loop}")

        elif kind == "call":
            arg_regs = ["x0", "x1", "x2", "x3", "x4", "x5", "x6", "x7"]
            for i, arg in enumerate(node.get("args", [])):
                if i < len(arg_regs):
                    self._gen_expr(arg, arg_regs[i])
            self._emit(f"    bl      oy_{node['name']}")

        elif kind == "return_stmt":
            self._gen_expr(node["value"], "x0")
            self._emit("    ldp     x29, x30, [sp], #16")
            self._emit("    ret")

        elif kind == "memory_map":
            self._gen_expr(node["addr"], "x0")
            self._gen_expr(node["size"], "x1")
            self._emit("    bl      _oy_memory_map")

        elif kind == "port_write":
            self._gen_expr(node["port"],  "x0")
            self._gen_expr(node["value"], "x1")
            self._emit("    bl      _oy_port_write")

        elif kind == "cpu_halt":
            self._emit("    bl      _oy_halt")

        elif kind == "query":
            self._emit(f"    // query: {node['target']}?  (resolved at runtime by driver)")

        else:
            self._emit(f"    // [arm64] unknown node: {kind}")

    # ------------------------------------------------------------------ #
    # Expression → dest_reg
    # ------------------------------------------------------------------ #

    def _gen_expr(self, expr: dict, dest_reg: str):
        kind = expr["type"]

        if kind == "int_lit":
            self._emit(f"    mov     {dest_reg}, #{expr['value']}")

        elif kind == "str_lit":
            label = self._intern_string(expr["value"])
            self._emit(f"    adr     {dest_reg}, {label}")

        elif kind == "var_ref":
            src = self._vars.get(expr["name"], "x0")
            if src != dest_reg:
                self._emit(f"    mov     {dest_reg}, {src}")

        elif kind == "binop":
            self._gen_expr(expr["left"],  dest_reg)
            self._emit("    str     x0, [sp, #-16]!")
            self._gen_expr(expr["right"], "x1")
            self._emit("    ldr     x0, [sp], #16")
            op = expr["op"]
            if op == "+":
                self._emit(f"    add     {dest_reg}, x0, x1")
            elif op == "-":
                self._emit(f"    sub     {dest_reg}, x0, x1")
            elif op == "*":
                self._emit(f"    mul     {dest_reg}, x0, x1")
            elif op == "/":
                self._emit(f"    sdiv    {dest_reg}, x0, x1")

        elif kind == "compare":
            self._gen_expr(expr["left"],  "x0")
            self._gen_expr(expr["right"], "x1")
            self._emit("    cmp     x0, x1")

    # ------------------------------------------------------------------ #
    # Condition → branch to lbl_false if false
    # ------------------------------------------------------------------ #

    def _gen_condition(self, cond: dict, lbl_false: str):
        self._gen_expr(cond, "x0")
        op = cond.get("op", "==")
        branch_map = {
            "==": "b.ne", "!=": "b.eq",
            "<":  "b.ge", ">":  "b.le",
            "<=": "b.gt", ">=": "b.lt",
        }
        br = branch_map.get(op, "b.ne")
        self._emit(f"    {br}     {lbl_false}")

    # ------------------------------------------------------------------ #
    # Print helper
    # ------------------------------------------------------------------ #

    def _gen_print(self, expr: dict):
        kind = expr["type"]
        if kind == "str_lit":
            label = self._intern_string(expr["value"])
            self._emit(f"    adr     x0, {label}")
            self._emit(f"    mov     x1, #{label}_len")
            self._emit("    bl      _oy_print")
            self._emit("    adr     x0, _newline")
            self._emit("    mov     x1, #1")
            self._emit("    bl      _oy_print")
        elif kind == "int_lit":
            self._emit(f"    mov     x0, #{expr['value']}")
            self._emit("    bl      _oy_print_int")
        elif kind == "var_ref":
            src = self._vars.get(expr["name"], "x0")
            if src != "x0":
                self._emit(f"    mov     x0, {src}")
            self._emit("    bl      _oy_print_int")
        else:
            self._gen_expr(expr, "x0")
            self._emit("    bl      _oy_print_int")
