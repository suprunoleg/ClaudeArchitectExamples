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

3. **Execution & API Credits (CRITICAL):**
   - **DO NOT** execute Python scripts that make LLM API calls using the `run_command` tool. The user has explicitly requested this to conserve their API credits. Write the code and let the user execute it manually on their own machine.
   - **ANTI-TOKEN-HOG RULE:** When writing examples that involve multi-agent fan-outs (`asyncio.gather`) or agentic `while` loops, you MUST hardcode strict limiters (e.g., `max_iterations = 2`, or limiting array slices to `[:2]`). Do NOT write code that spawns 10+ concurrent subagents or accumulates massive context windows unchecked. Protect the user's wallet at all costs.

---

## 4. Example Generation Guidelines

The core purpose of this project is to provide complete, end-to-end working examples for the Anthropic Test Certificate. When asked to generate an example for any concept (e.g., document extraction pipeline, pre-tool hooks, etc.), agents MUST follow these rules:

1. **Complete & Runnable Flow:** Do not provide standalone snippets. Provide a fully functional, runnable script showing how all parts (API calls, tool definitions, hooks, etc.) integrate together.
2. **Single-File Preference:** Consolidate the full flow into a single, concise file whenever possible so the user can easily see the complete implementation context at a glance.
3. **Ready to Learn:** The code must serve as a comprehensive learning resource. Even if the user doesn't run the script, the entire flow (from setup to execution) must be evident.
4. **Short & Concise:** Keep the example as brief as possible while still being a complete, end-to-end integration.
5. **Use Claude 4.5 Haiku:** ALWAYS use the model string `claude-haiku-4-5` as the default model via a `DEFAULT_MODEL` constant in all API and SDK calls.
6. **Standardized Environment Loading:** All scripts MUST structure environment loading directly below the `DEFAULT_MODEL` constant as follows:
   ```python
   # Constants
   DEFAULT_MODEL = "claude-haiku-4-5"
   
   # Load environment variables
   load_dotenv()
   if "ANTHROPIC_API_KEY" not in os.environ:
       os.environ["ANTHROPIC_API_KEY"] = "dummy_key"
   ```

---

## 5. Official Exam Guide Path Rules (Dual Implementation)

For any agent generating or modifying canonical examples within the `OfficialExamGuide/` directory, you MUST implement **TWO** distinct versions of every task:

1. **The SDK Version (`*_sdk.py`)**: This version must strictly use the `claude_agent_sdk` (`ClaudeAgentOptions`, `AgentDefinition`, `query`, `Task` tool, `Hooks`). This is required because the Anthropic exam explicitly tests knowledge of these specific SDK abstractions, even if they force a prompt-driven/probabilistic architecture.
2. **The API Version (`*_api.py`)**: This version must strictly use the raw `anthropic` API to implement the same task using a **deterministic, code-first** paradigm. Use explicit Python control flow (`asyncio.gather`, `while` loops, explicit `MessageEnvelope` routing, raw `stop_reason` inspection) and structured outputs (Pydantic schemas) to prove how the architecture should be built robustly in a production environment without relying on probabilistic LLM routing.
