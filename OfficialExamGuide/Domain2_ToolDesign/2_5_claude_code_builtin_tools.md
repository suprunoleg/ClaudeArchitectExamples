# Task Statement 2.5: Select and apply built-in tools effectively
*(Claude Code Domain)*

The Claude Code CLI provides several highly optimized built-in tools. The exam tests your knowledge of **when** and **how** to use these built-in tools vs custom tools.

## 1. File Exploration (`Glob`, `Grep`, `LS`)
**Knowledge of:**
- `Glob` is best for finding files by naming pattern (e.g., `*.py` or `**/*.test.js`) across large codebases without loading content.
- `Grep` (or Ripgrep) is best for finding specific text or regex patterns *within* files, returning snippets and line numbers without loading the whole file into context.
- `LS` is best for shallow directory listing to understand project structure.

**Exam Trap:** Using `Read` to open 50 files just to search for a function name will blow out the context window. You must use `Grep`.

## 2. File Modification (`Edit` vs `Write`)
**Knowledge of:**
- `Write` should ONLY be used to create brand new files or overwrite a file completely.
- `Edit` (or `Replace`) MUST be used for modifying existing files. It uses search-and-replace blocks to patch specific lines, which saves massive amounts of output tokens compared to rewriting the entire file with `Write`.

## 3. Execution (`Bash`)
**Knowledge of:**
- The `Bash` tool allows Claude Code to execute shell commands, run tests, install dependencies, and build projects.
- **Safety Boundary:** Destructive commands (like `rm -rf`) or running unfamiliar scripts should be bounded by permissions or require explicit user confirmation.

## Example Claude Code Workflow:
*If a user asks Claude Code: "Fix the deprecation warning in the database connection"*

1. **Glob**: `Glob(pattern="**/db*.py")` -> Locates the database file.
2. **Grep**: `Grep(pattern="connect\\(", path="src/db.py")` -> Finds the exact line of the warning without reading the whole file.
3. **Read**: `Read(path="src/db.py")` -> Reads the file to understand the surrounding context.
4. **Edit**: `Edit(path="src/db.py", old_string="...", new_string="...")` -> Patches the specific line without rewriting the file.
5. **Bash**: `Bash(command="pytest tests/db_tests.py")` -> Verifies the fix didn't break anything.
