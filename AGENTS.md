# Agent Guidelines (AGENTS.md)

This document provides guidelines, environment specifications, and setup instructions for AI coding agents (such as Antigravity / Gemini / Claude) interacting with this codebase.

---

## 1. Project Overview & Tech Stack

- **Language:** Python 3.x
- **Core Dependencies:** 
  - `anthropic`
  - `claude-agent-sdk`
- **Environment Management:** Virtual environment at `.venv`

---

## 2. Virtual Environment & Commands

Always ensure commands run within the dedicated Python virtual environment `.venv`.

### Setup & Activation
- **Create environment:**
  ```powershell
  python -m venv .venv
  ```
- **Activate environment (Windows PowerShell):**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
- **Activate environment (Windows CMD):**
  ```cmd
  .\.venv\Scripts\activate.bat
  ```
- **Activate environment (macOS / Linux):**
  ```bash
  source .venv/bin/activate
  ```

### Package Management
- **Install dependencies:**
  ```bash
  pip install -r requirements.txt
  ```

---

## 3. Development Guidelines for AI Agents

1. **Environment Awareness:**
   - Always check if `.venv` exists before running Python commands or installing packages.
   - Execute commands in the workspace root directory (`d:\Source\Learning\ClaudeArchitectExamples`).

2. **Code Style & Practices:**
   - Follow standard Python PEP 8 style guidelines.
   - Maintain type annotations and docstrings for functions and classes.
   - Do not remove or mutate unrelated comments or docstrings.
   - **File Introductions:** Each script file (especially complicated ones) must begin with a concise, descriptive introductory comment describing the pattern and purpose of the script. If needed, you can add 1-2 more sentences (ONLY IF IT ADDS VALUE).

3. **Verification:**
   - After creating or modifying Python scripts, test execution using the `.venv` interpreter.

---

## 4. Example Generation Guidelines

The core purpose of this project is to provide complete, end-to-end working examples for the Anthropic Test Certificate. When asked to generate an example for any concept (e.g., document extraction pipeline, pre-tool hooks, etc.), agents MUST follow these rules:

1. **Complete & Runnable Flow:** Do not provide standalone snippets. Provide a fully functional, runnable script showing how all parts (API calls, tool definitions, hooks, etc.) integrate together.
2. **Single-File Preference:** Consolidate the full flow into a single, concise file whenever possible so the user can easily see the complete implementation context at a glance.
3. **Ready to Learn:** The code must serve as a comprehensive learning resource. Even if the user doesn't run the script, the entire flow (from setup to execution) must be evident.
4. **Short & Concise:** Keep the example as brief as possible while still being a complete, end-to-end integration.
5. **Use Claude 4.5 Haiku:** ALWAYS use the model string `claude-haiku-4-5` as the default model via a `DEFAULT_MODEL` constant in all API and SDK calls.
