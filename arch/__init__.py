"""
Osyhon Architecture Backends
Each backend receives an IR (list of nodes) and emits Assembly.

IR Node Types:
  program       : { stmts: [node] }
  kernel_start  : { body: [node] }
  func_def      : { name: str, args: [str], body: [node] }
  assign        : { var: str, value: expr }
  print_stmt    : { value: expr }
  alloc         : { var: str, size: expr }        # alloc memory N
  free          : { var: str }                    # free var  (requires ! in .osy)
  if_stmt       : { cond: expr, body: [node], else_body: [node] }
  for_stmt      : { var: str, end: expr, body: [node] }
  call          : { name: str, args: [expr] }
  return_stmt   : { value: expr }
  memory_map    : { addr: expr, size: expr }
  port_write    : { port: expr, value: expr }
  cpu_halt      : {}
  query         : { target: str }               # battery?, wifi?, storage?, time?

Expr Types:
  int_lit   : { value: int }
  str_lit   : { value: str }
  var_ref   : { name: str }
  binop     : { op: str, left: expr, right: expr }
  compare   : { op: str, left: expr, right: expr }
"""

from abc import ABC, abstractmethod


SUPPORTED_ARCHS = ["x86_64", "arm64", "riscv"]


class OsyhonCodeGenError(Exception):
    pass


class CodeGen(ABC):
    """Base code generator — subclassed by each architecture backend."""

    def __init__(self):
        self._label_counter = 0
        self._strings: dict[str, str] = {}   # label -> value
        self._vars: dict[str, str] = {}       # varname -> register/stack slot
        self._output: list[str] = []

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def generate(self, program: dict) -> str:
        """Entry point: takes a 'program' node, returns full assembly text."""
        self._reset()
        self._emit_header()

        for node in program.get("stmts", []):
            self._gen_node(node)

        self._emit_footer()
        self._emit_data_section()
        return "\n".join(self._output)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _reset(self):
        self._label_counter = 0
        self._strings = {}
        self._vars = {}
        self._output = []

    def _new_label(self, prefix: str = ".L") -> str:
        self._label_counter += 1
        return f"{prefix}{self._label_counter}"

    def _intern_string(self, value: str) -> str:
        """Store a string literal, return its label."""
        for label, v in self._strings.items():
            if v == value:
                return label
        label = f"_str{len(self._strings)}"
        self._strings[label] = value
        return label

    def _emit(self, line: str = ""):
        self._output.append(line)

    def _emit_comment(self, text: str):
        self._emit(f"{self._comment_char()} {text}")

    # ------------------------------------------------------------------ #
    # Abstract interface — must be implemented per architecture
    # ------------------------------------------------------------------ #

    @abstractmethod
    def _comment_char(self) -> str: ...

    @abstractmethod
    def _emit_header(self): ...

    @abstractmethod
    def _emit_footer(self): ...

    @abstractmethod
    def _emit_data_section(self): ...

    @abstractmethod
    def _gen_node(self, node: dict): ...

    @abstractmethod
    def _gen_expr(self, expr: dict, dest_reg: str): ...


def get_backend(arch: str) -> "CodeGen":
    """Factory — returns the right backend for the given arch string."""
    arch = arch.lower().replace("-", "_")
    if arch == "x86_64":
        from arch.x86_64 import X86_64CodeGen
        return X86_64CodeGen()
    elif arch in ("arm64", "aarch64"):
        from arch.arm64 import ARM64CodeGen
        return ARM64CodeGen()
    elif arch in ("riscv", "riscv64", "risc_v"):
        from arch.riscv import RISCVCodeGen
        return RISCVCodeGen()
    else:
        raise OsyhonCodeGenError(f"Unknown architecture: '{arch}'")
