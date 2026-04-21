"""
Quick smoke-test for all three Osyhon architecture backends.
Run:  python3 arch/test_codegen.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from arch import get_backend

# ── Sample Osyhon IR ──────────────────────────────────────────────────
# Equivalent Osyhon source:
#
#   kernel_start:
#       alloc memory 1024
#       print "OS started"
#       for i in range 3:
#           print i
#       if x == 10:
#           print "yes"
#       memory.map 0xFEE00000 4096
#       cpu.halt

SAMPLE_PROGRAM = {
    "type": "program",
    "stmts": [
        {
            "type": "func_def",
            "name": "greet",
            "args": ["name"],
            "body": [
                {"type": "print_stmt", "value": {"type": "str_lit", "value": "hello "}},
                {"type": "print_stmt", "value": {"type": "var_ref",  "name": "name"}},
            ],
        },
        {
            "type": "kernel_start",
            "body": [
                {
                    "type": "alloc",
                    "var":  "buf",
                    "size": {"type": "int_lit", "value": 1024},
                },
                {
                    "type": "print_stmt",
                    "value": {"type": "str_lit", "value": "OS started"},
                },
                {
                    "type": "for_stmt",
                    "var": "i",
                    "end": {"type": "int_lit", "value": 3},
                    "body": [
                        {"type": "print_stmt", "value": {"type": "var_ref", "name": "i"}},
                    ],
                },
                {
                    "type": "if_stmt",
                    "cond": {
                        "type": "compare",
                        "op":   "==",
                        "left":  {"type": "var_ref",  "name": "x"},
                        "right": {"type": "int_lit",  "value": 10},
                    },
                    "body": [
                        {"type": "print_stmt", "value": {"type": "str_lit", "value": "yes"}},
                    ],
                    "else_body": [],
                },
                {
                    "type": "memory_map",
                    "addr": {"type": "int_lit", "value": 0xFEE00000},
                    "size": {"type": "int_lit", "value": 4096},
                },
                {"type": "cpu_halt"},
            ],
        },
    ],
}


def run_test(arch_name: str, out_path: str):
    backend = get_backend(arch_name)
    asm = backend.generate(SAMPLE_PROGRAM)
    with open(out_path, "w") as f:
        f.write(asm)
    lines = asm.count("\n")
    print(f"  [{arch_name:8s}]  {lines:4d} lines  →  {out_path}")
    return asm


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)

    print("Osyhon Code Generator — Architecture Test")
    print("=" * 50)

    run_test("x86_64", os.path.join(output_dir, "output.x86_64.asm"))
    run_test("arm64",  os.path.join(output_dir, "output.arm64.asm"))
    run_test("riscv",  os.path.join(output_dir, "output.riscv.asm"))

    print("=" * 50)
    print("Done. Check output/ for generated assembly files.")
