# Task Statement 3.5: Apply iterative refinement techniques for progressive improvement
*(Claude Code Domain)*

The exam tests your understanding of **Iterative Refinement** (or Test-Driven agent loops). Rather than asking an LLM to build a massive feature perfectly in one shot, you should instruct it to build, verify, and refine in tight, iterative loops.

## The One-Shot Anti-Pattern
**Bad Prompt:**
> "Build a full authentication system with OAuth, rate limiting, and password reset functionality. Ensure it's perfectly secure."

**Why it fails:**
The LLM will write hundreds of lines of code. If there is a bug in the database connection (the very first step), the subsequent OAuth and rate-limiting code will also be broken. The context window will fill up with broken code and stack traces.

## The Iterative Refinement Pattern (EXAM SKILL)
**Good Workflow:**
1. **Prompt 1:** "Create the basic database schema for users. Run pytest to verify the model saves correctly."
2. **Execute:** Claude Code builds the schema, writes a test, runs `Bash(pytest)`, and fixes any minor bugs.
3. **Compact:** User runs `/compact` to summarize the completed work, removing all the raw code generation and stack traces from the context window, leaving only the knowledge that "The user schema is complete and working."
4. **Prompt 2:** "Now add OAuth login for the user schema we just built. Verify it with a unit test."

## Key Concepts Tested:
1. **Micro-Verification:** Force the agent to run tests (using `Bash`) after every logical step.
2. **Context Compaction:** Know when to use `/compact`. If an agent spends 15 turns fixing a tricky syntax error, the context window is now polluted with 15 turns of failures. Once the bug is fixed, running `/compact` summarizes the success and discards the failed turns, ensuring the agent has a clean mental state for the next logical step.
