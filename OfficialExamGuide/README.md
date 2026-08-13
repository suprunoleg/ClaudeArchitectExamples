# CCA-Foundations Task Statement Examples Tracker

This directory contains canonical examples tailored to the **Claude Certified Architect – Foundations** exam guide. Each example is designed to demonstrate the specific skills and knowledge required for a single Task Statement.

## Design Principles for Examples

When creating new canonical examples in this directory, the following rules MUST be followed:

1. **Two Comprehensive Files per Task Statement**: For every Task Statement, create **two** versions of the code (`_sdk.py` and `_api.py`). Merge all bullet points of a Task Statement into these cohesive examples. Use in-code comments (e.g., `# EXAM SKILL: [Bullet Point Topic]`) to map the code back to the specific bullet points in the exam guide.
2. **Exceptions to Two-File Rule**: Only split a Task Statement into more than two files if:
   - The bullet points ask to compare mutually exclusive approaches (e.g., `1_6_prompt_chaining_example.py` vs `1_6_dynamic_decomposition_example.py`).
   - Merging everything makes the file too bloated or confusing to read at a glance.
   - You need to contrast a good example with a dedicated `anti_pattern_example.py`.
3. **High-Value Print Statements Only**: Keep terminal output minimal. Only add `print()` statements in key locations where it absolutely adds educational value (e.g., pretty-printing the final `messages` array or final `ResultMessage` to prove the state has changed).
4. **Dual Implementation (SDK vs API)**: For every task statement, provide both paradigms:
   - `[task_number]_[name]_sdk.py`: Uses the `claude_agent_sdk` to demonstrate the exact syntax and abstractions tested on the exam (e.g., `Task` tool, `query()`).
   - `[task_number]_[name]_api.py`: Uses the raw `anthropic` API to demonstrate how to build the same pattern deterministically using pure Python code (`asyncio.gather`, explicit state routing, raw `stop_reason` parsing).
5. **Short & Descriptive Comments Only**: Keep all comments descriptive, short, and concise. Avoid overly verbose explanations in the code; let the code structure speak for itself while clearly marking the exam skills being demonstrated.
6. **Introductory Docstring**: Every file must start with a module-level docstring. This introduction must state the Task Statement title and explicitly list the specific "Knowledge of:" and/or "Skills in:" bullet points from the exam guide that this script covers (e.g., *Knowledge of: Hub-and-spoke architecture...*).


## Domain 1: Agentic Architecture & Orchestration
- [x] **1.1** Design and implement agentic loops for autonomous task execution
- [x] **1.2** Orchestrate multi-agent systems with coordinator-subagent patterns
- [x] **1.3** Configure subagent invocation, context passing, and spawning
- [x] **1.4** Implement multi-step workflows with enforcement and handoff patterns
- [x] **1.5** Apply Agent SDK hooks for tool call interception and data normalization
- [x] **1.6** Design task decomposition strategies for complex workflows
- [x] **1.7** Manage session state, resumption, and forking

## Domain 2: Tool Design & MCP Integration
- [x] **2.1** Design effective tool interfaces with clear descriptions and boundaries
- [x] **2.2** Implement structured error responses for MCP tools
- [x] **2.3** Distribute tools appropriately across agents and configure tool choice
- [x] **2.4** Integrate MCP servers into Claude Code and agent workflows
- [x] **2.5** Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively

## Domain 3: Claude Code Configuration & Workflows
- [x] **3.1** Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization
- [x] **3.2** Create and configure custom slash commands and skills
- [x] **3.3** Apply path-specific rules for conditional convention loading
- [x] **3.4** Determine when to use plan mode vs direct execution
- [x] **3.5** Apply iterative refinement techniques for progressive improvement
- [x] **3.6** Integrate Claude Code into CI/CD pipelines

## Domain 4: Prompt Engineering & Structured Output
- [x] **4.1** Design prompts with explicit criteria to improve precision and reduce false positives
- [x] **4.2** Apply few-shot prompting to improve output consistency and quality
- [x] **4.3** Enforce structured output using tool use and JSON schemas
- [x] **4.4** Implement validation, retry, and feedback loops for extraction quality
- [x] **4.5** Design efficient batch processing strategies
- [x] **4.6** Design multi-instance and multi-pass review architectures

## Domain 5: Context Management & Reliability
- [x] **5.1** Manage conversation context to preserve critical information across long interactions
- [x] **5.2** Design effective escalation and ambiguity resolution patterns
- [x] **5.3** Implement error propagation strategies across multi-agent systems
- [x] **5.4** Manage context effectively in large codebase exploration
- [x] **5.5** Design human review workflows and confidence calibration
- [x] **5.6** Preserve information provenance and handle uncertainty in multi-source synthesis
