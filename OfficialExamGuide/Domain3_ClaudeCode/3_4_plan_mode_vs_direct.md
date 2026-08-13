# Task Statement 3.4: Determine when to use plan mode vs direct execution
*(Claude Code Domain)*

The Claude Code CLI provides two distinct operational modes. The exam tests your ability to choose the correct mode based on the task's complexity to optimize for token cost and architectural accuracy.

## 1. Direct Execution Mode (Default)
**Command:** `claude` or `claude -c "fix the typo"`

**How it works:**
Claude Code immediately begins reading files and executing edits using its tools. It iterates rapidly until the task is complete.

**When to use it:**
- Simple bug fixes ("Fix the NullPointerException in user_service.py")
- Localized refactors ("Extract this 50-line function into a helper file")
- Creating new, isolated components that don't impact the broader architecture.

## 2. Plan Mode (`-p`)
**Command:** `claude -p "Migrate from SQLite to PostgreSQL"`

**How it works:**
Claude Code enters a strict "read-only/thinking" mode. It is explicitly forbidden from modifying files. Instead, it researches the codebase using `Glob`, `Grep`, and `Read`, and generates a detailed Markdown implementation plan. The user reviews the plan, and only then is it passed to an execution agent.

**When to use it (EXAM SKILL):**
- **Major Architectural Changes:** Migrations, changing state management paradigms.
- **Cross-Cutting Concerns:** Adding authentication to every API endpoint.
- **High Ambiguity Tasks:** "Make the app run faster."

**Why Plan Mode is Critical for Complex Tasks:**
If you use Direct Execution for a complex migration, the LLM will begin editing file #1 before it has fully analyzed file #50. Halfway through the migration, it may realize its approach was wrong, requiring it to revert dozens of files. This leads to massive token bloat and context pollution. Plan Mode guarantees global context is established *before* the first edit is made.
