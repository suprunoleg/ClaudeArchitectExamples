# Python Virtual Environment Setup

This guide provides instructions on how to create, activate, and manage a Python virtual environment (`venv`) for this project.

---

## 1. Create Virtual Environment

Run the following command in the project root directory:

**Windows / macOS / Linux:**
```bash
python -m venv .venv
```
*(On macOS/Linux, you may need to use `python3 -m venv .venv` depending on your Python installation.)*

---

## 2. Activate Virtual Environment

Choose the command corresponding to your operating system and shell:

### Windows (PowerShell)
```powershell
.\.venv\Scripts\Activate.ps1
```
> **Note:** If you encounter an execution policy error in PowerShell, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
> ```

### Windows (Command Prompt)
```cmd
.\.venv\Scripts\activate.bat
```

### macOS / Linux (Bash or Zsh)
```bash
source .venv/bin/activate
```

---

## 3. Install Dependencies

Once the virtual environment is activated, install the required packages using:

```bash
pip install -r requirements.txt
```

---

## 4. Deactivate Virtual Environment

When you are done working, deactivate the environment by running:

```bash
deactivate
```
