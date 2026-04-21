#!/bin/bash
cd "$(dirname "$0")"

echo "=== توليد Assembly للمعماريات الثلاث ==="
python3 arch/test_codegen.py
echo ""

# ── x86_64 ──────────────────────────────────────────────
echo "=== x86_64 ==="
cd output
as -o test_x86_64.o test_x86_64.s && \
ld -o test_x86_64 test_x86_64.o && \
./test_x86_64
echo ""
cd ..

# ── ARM64 ───────────────────────────────────────────────
echo "=== ARM64 (عبر QEMU) ==="
cd output
aarch64-linux-gnu-as -o test_arm64.o output.arm64.asm && \
aarch64-linux-gnu-ld -o test_arm64 test_arm64.o && \
qemu-aarch64 ./test_arm64
echo ""
cd ..

# ── RISC-V ──────────────────────────────────────────────
echo "=== RISC-V 64 (عبر QEMU) ==="
cd output
riscv64-linux-gnu-as -march=rv64imac -o test_riscv.o output.riscv.asm && \
riscv64-linux-gnu-ld --no-relax -o test_riscv test_riscv.o && \
qemu-riscv64 ./test_riscv
echo ""
cd ..

echo "=== انتهى الاختبار ==="
