# LLVM-Based Python Compiler

This project is a lightweight Python-to-LLVM compiler that translates a subset of Python code into LLVM IR and compiles it into an executable. It supports basic arithmetic, conditionals, function calls, and print statements using the `llvmlite` library.

## Features

- Converts Python functions to LLVM IR
- Supports arithmetic operations (`+`, `-`, `*`, `/`)
- Handles conditionals (`if`, `else`) and comparisons
- Supports function calls and local variable storage
- Generates standalone executables

---

## Installation

### Step 1: Install Required Dependencies

Ensure you have Python 3.x installed. Then install the required Python package by running:

```bash
pip install -r requirements.txt
```

This will install:

- `llvmlite` → Used for generating LLVM IR

---

### Step 2: Install LLVM Toolchain

This compiler requires the LLVM toolchain (`llc` and `clang`) for compiling LLVM IR into machine code.

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install llvm clang
```

#### MacOS (using Homebrew)

```bash
brew install llvm
```

#### Windows

1. Download the LLVM toolchain from:  
   [https://github.com/llvm/llvm-project/releases](https://github.com/llvm/llvm-project/releases)
2. Install it and add `llvm/bin` to your PATH.
3. Verify installation by running:
   ```bash
   llc --version
   clang --version
   ```

---

## Usage

### Step 1: Write a Python Script

Create a simple Python script (e.g., `example.py`):

```python
def main():
    print("Hello, LLVM!")
```

---

### Step 2: Compile with LLVM Compiler

Run the compiler on your script or you can use our script for demo (`test.py`):

```bash
python compiler.py example.py
```

### Step 3: Execute the Compiled File

After compilation, an executable file named `output` is generated. Run it with:

```bash
./output
```

If you see "Hello, LLVM!" printed, your program has compiled successfully!

---

## How It Works

1. **Parses Python code** using the `ast` (Abstract Syntax Tree) module.
2. **Generates LLVM IR** using `llvmlite`.
3. **Saves LLVM IR** to a file (`output.ll`).
4. **Compiles IR to an object file** using `llc`.
5. **Links the object file with Clang** to produce the final executable.

---

## Supported Features

| Feature                         | Supported?   |
| ------------------------------- | ------------ |
| Arithmetic (`+`, `-`, `*`, `/`) | Yes          |
| Conditionals (`if`, `else`)     | Yes          |
| Function Calls                  | Yes          |
| Variable Assignments            | Yes          |
| Print Statements                | Yes          |
| Loops (`for`, `while`)          | No (not yet) |
| Lists & Dictionaries            | No (not yet) |

---

## Troubleshooting

- **llc command not found:**  
  Ensure LLVM is installed and the `llc` binary is added to your system's PATH.
- **Compilation issues on Windows:**  
  Try running `clang` from the LLVM installation directory if you encounter linking problems.
- **Runtime errors (e.g., NameError):**  
  Verify that all variables are properly assigned and referenced in your source code.

---

## Future Improvements

- Add support for loops (`for`, `while`)
- Improve error handling and diagnostics
- Extend to more Python constructs

---

## Contributing

If you'd like to contribute, please fork the repository and submit a pull request with your improvements!

```

```
