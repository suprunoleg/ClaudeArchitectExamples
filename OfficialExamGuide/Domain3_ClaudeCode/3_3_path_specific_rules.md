# Task Statement 3.3: Apply path-specific rules for conditional convention loading
*(Claude Code Domain)*

When working in a monorepo or full-stack repository, different directories often have conflicting conventions (e.g., Python backend vs React frontend). The exam tests your ability to scope rules conditionally.

There are two approaches to solve this:

## Approach A: Nested `CLAUDE.md` Files (Best for heavily disjointed teams)
Claude Code supports hierarchical `CLAUDE.md` files.

**File:** `frontend/CLAUDE.md`
```markdown
# Frontend Rules
- Always use `npm run format` (Prettier) before finishing.
- Use React functional components.
```

**File:** `backend/CLAUDE.md`
```markdown
# Backend Rules
- Always use `black` and `flake8`.
- Use FastAPI.
```
*When Claude Code is editing a file in `/frontend`, it reads BOTH the root `CLAUDE.md` and the `frontend/CLAUDE.md`. The nested file overrides the root if there are conflicts.*

## Approach B: Path-Specific Conditionals in the Root (Best for smaller repos)
If you prefer a single source of truth, you must write explicit path-based conditionals in your root `CLAUDE.md`.

**File:** `CLAUDE.md` (in Root)
```markdown
# Global Rules
- Always write tests for new code.

# Path-Specific Conventions (EXAM SKILL)
- **If you are modifying files in `frontend/**/*.tsx`:**
  - You MUST run `npm run lint`.
  - Use Tailwind for styling.
  
- **If you are modifying files in `backend/**/*.py`:**
  - You MUST run `pytest`.
  - Use SQLAlchemy for database interactions.
```

**Exam Trap:** Failing to specify the path (`frontend/**/*.tsx`) will confuse the LLM, causing it to attempt running `pytest` on a React component.
