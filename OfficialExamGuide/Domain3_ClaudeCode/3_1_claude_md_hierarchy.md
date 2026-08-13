# Task Statement 3.1: Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization
*(Claude Code Domain)*

This document demonstrates how to properly design `CLAUDE.md` files for Claude Code.

## 1. Hierarchy & Scoping
**Knowledge of:**
Claude Code reads instructions from multiple locations, merging them in a specific priority order (most specific to least specific):

1. **Local/Directory Scoped**: `sub_folder/CLAUDE.md` (Overrides everything else for tasks within this folder).
2. **Workspace/Project Scoped**: `./CLAUDE.md` (Applies to the entire repository).
3. **Global Scoped**: `~/.claude.md` (Applies to every project on your machine, e.g., "Always use `claude-3-5-sonnet`" or "Always format with Prettier").

## 2. Modular Organization & The 500-Line Limit
**Knowledge of:**
- `CLAUDE.md` files should be concise. If they grow beyond ~500 lines, they consume too many input tokens for every single interaction, wasting credits and degrading LLM focus.
- **EXAM SKILL:** Avoid token bloat by keeping `CLAUDE.md` as an "index" or "router" that points to specialized markdown files when needed.

## Example: A Well-Structured `CLAUDE.md`
Here is an example of an optimized, modular `CLAUDE.md`:

```markdown
# Project Context
This is the backend repository for the Acme E-Commerce platform.

# Tech Stack
- Python 3.11, FastAPI, SQLAlchemy
- Testing: Pytest

# Rules
- ALL Python files must pass `black` and `flake8` formatting.
- ALWAYS use the `.venv` virtual environment for Python commands.
- DO NOT generate test files without also running them immediately to verify.

# Modular Architecture References
*Note: Do not memorize the following rules unless working on these specific systems.*
- When modifying the database schemas, you MUST follow the rules in `docs/DB_MIGRATION_GUIDE.md`.
- When writing new frontend API endpoints, you MUST follow the schema in `docs/API_STANDARDS.md`.
```

**Why this is effective:**
Instead of pasting the entire database migration guide into the root `CLAUDE.md` (which would force Claude Code to read it on *every* single prompt), the agent reads the pointer and uses its `Glob`/`Read` tools to fetch `docs/DB_MIGRATION_GUIDE.md` ONLY if the user's prompt involves the database.
