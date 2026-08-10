# Project Agent Rules

- Use `.venv` virtual environment for all Python operations in this workspace.
- Run `.\.venv\Scripts\Activate.ps1` (PowerShell) or `source .venv/bin/activate` (Bash) when executing Python tasks.
- Keep dependencies updated in `requirements.txt`.

## Example Generation Rules

- **End-to-End Examples:** When answering questions or demonstrating concepts (like "document extraction pipeline", "pre-tool hook", etc.) for the Anthropic test certificate, **always provide complete, fully runnable, end-to-end code implementations**.
- **No Standalone Snippets:** Do not just output fragments of code. You must show how everything integrates together (tool definitions, hooks, API calling, execution).
- **Single File Preference:** Put the entire working example into a single, concise file whenever possible.
- **Ready to Learn:** Even if the user does not intend to run the code, the example must be written as a "ready to learn" script so the user can trace the complete execution flow from start to finish.
