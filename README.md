# osyhon
إليك محتوى ملف `README.md` باللغة الإنجليزية، مصمم ليكون جاهزاً للنسخ واللصق مباشرة في مشروعك على GitHub أو أي منصة أخرى:

```markdown
# Osyhon: Systems Programming for Everyone

**Osyhon** is a systems programming language designed to empower anyone familiar with **Python** to build complete operating systems. It bridges the gap between high-level ease of use and low-level hardware control.

---

## 🚀 Core Vision
* **Zero Learning Curve**: If you know Python, you can write Osyhon without learning complex new concepts.
* **Direct Execution**: Compiles directly to machine code without any intermediate layers (No LLVM, No C).
* **Flexible Control**: Developers choose their level of control—from fully safe logic to manual hardware manipulation.
* **Minimalist Core**: A tiny core language where the community builds the surrounding ecosystem.

---

## 🛠 Syntax and Structure
Osyhon uses direct commands and indentation-based organization, mirroring Python's clean syntax.

```python
# Example Code
kernel_start:
    alloc memory 1024
    print "OS started"

def greet name:
    print "hello " + name

if x == 10:
    print "yes"

for i in range 10:
    print i
```

---

## 📂 File Types and Safety
The language separates safe logic from "dangerous" system code using different file extensions:

| Extension | Purpose | Risk Level | Handles |
| :--- | :--- | :--- | :--- |
| `.oy` | General Logic | Safe | Interfaces, Logic, Functions |
| `.osy` | System Kernel | Dangerous | Memory, Hardware, CPU |

*Separating responsibilities (e.g., `main.oy` for logic and `memory.osy` for kernel tasks) is the recommended architectural pattern.*

---

## ⚠️ The "!" Principle
The **!** symbol is the unified principle of responsibility in Osyhon. It signifies: *"I take full responsibility for this operation"*.

| Feature | Without `!` | With `!` |
| :--- | :--- | :--- |
| **Memory** | Automatic garbage collection | Manual management (`free`) |
| **Concurrency** | Osyhon decides timing | Developer decides concurrency |
| **Result** | Safe and simple | Faster and more granular control |

---

## 💎 Type System
Osyhon uses **Type Inference**. The compiler identifies the type automatically, ensuring it remains static once assigned.

* `x = 10` → Identified as `int`.
* `name = "osama"` → Identified as `str`.
* **Error Prevention**: Assigning a string to an integer variable will trigger a compile-time error.

---

## 🛡️ Error Handling
The compiler follows a strict three-stage safety process:
1.  **Inspection**: Full code scan for syntax and logic errors.
2.  **Auto-Repair**: Attempt to fix minor errors automatically.
3.  **Halt**: If unfixable, the compiler stops and highlights the exact line.

> **Philosophy**: A program either runs perfectly or doesn't run at all. There is no "crashing at runtime" due to preventable errors.

---

## 🔌 Hardware & Architecture
Basic hardware commands are built-in, while the community provides extended drivers.

* **Built-in Functions**: `memory.map`, `port.write`, `cpu.halt`.
* **Multi-Arch Support**: Define targets in `main.oy` to build for `x86_64`, `ARM64`, or `RISC-V` simultaneously.
* **Conditional Compilation**: Use `#arch:` blocks for architecture-specific code (e.g., `#x86_64:` or `#ARM64:`).

---

## 📦 Package Management
* **Official Sources**: To ensure system security, only libraries from the official `github.com/osyhon` account are supported.
* **Tree Shaking**: The compiler only includes the specific parts of the library you actually use, keeping the binary tiny.
* **Configuration**: All dependencies are managed via `packages.oy`.

---

## ⚙️ Compiler & CLI
The `osyhon` compiler is written in **Assembly** to ensure the fastest possible compilation speeds.

| Command | Function |
| :--- | :--- |
| `build main.oy` | Builds binaries for all specified architectures. |
| `run main.oy` | Executes the program directly. |
| `check main.oy` | Validates code integrity without building. |
```