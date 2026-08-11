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

---

## 5. Running the Examples

This repository is designed as a collection of **fully self-contained, end-to-end runnable examples**. You do not need to stitch snippets together—every single `.py` file is a complete program!

To run any example, simply execute it directly using python while your virtual environment is active. 

> **Important (Windows Users):** Because many of these scripts print beautiful colorful emojis to the console (like 🕵️ and ✅), you may need to force UTF-8 encoding in PowerShell before running them to avoid a `UnicodeEncodeError`:
> ```powershell
> $env:PYTHONIOENCODING="utf-8"
> ```

### Run Examples:
```bash
# Run the simple quickstart test
python quickstart_test.py

# Run a specific sub-folder example (e.g., Stratified Sampling)
python Labeling/stratified_sampling_example.py

# Run a complex Multi-Agent workflow
python MultiAgent/large_scale_workflow_orchestration_example.py
```
