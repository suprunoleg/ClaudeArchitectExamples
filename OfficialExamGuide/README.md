# CCA-Foundations Task Statement Examples Tracker

This directory contains canonical examples tailored to the **Claude Certified Architect – Foundations** exam guide. Each example is designed to demonstrate the specific skills and knowledge required for a single Task Statement.

## Design Principles for Examples

When creating new canonical examples in this directory, the following rules MUST be followed:

1. **One Comprehensive File per Task Statement**: Merge all bullet points of a Task Statement into a single, cohesive example file. Use in-code comments (e.g., `# EXAM SKILL: [Bullet Point Topic]`) to map the code back to the specific bullet points in the exam guide.
2. **Exceptions to Single-File Rule**: Only split a Task Statement into multiple files if:
   - The bullet points ask to compare mutually exclusive approaches (e.g., `1_6_prompt_chaining_example.py` vs `1_6_dynamic_decomposition_example.py`).
   - Merging everything makes the file too bloated or confusing to read at a glance.
   - You need to contrast a good example with a dedicated `anti_pattern_example.py`.
3. **High-Value Print Statements Only**: Keep terminal output minimal. Only add `print()` statements in key locations where it absolutely adds educational value (e.g., pretty-printing the final `messages` array or final `ResultMessage` to prove the state has changed).
4. **Runnable with Real APIs**: The code MUST be runnable. Do not use mock API calls to LLMs. Actual work should be done using the **Claude Agent SDK** (preferred) or direct Claude API calls.
5. **Short & Descriptive Comments Only**: Keep all comments descriptive, short, and concise. Avoid overly verbose explanations in the code; let the code structure speak for itself while clearly marking the exam skills being demonstrated.
6. **Introductory Docstring**: Every file must start with a module-level docstring. This introduction must state the Task Statement title and explicitly list the specific "Knowledge of:" and/or "Skills in:" bullet points from the exam guide that this script covers (e.g., *Knowledge of: Hub-and-spoke architecture...*).


## Domain 1: Agentic Architecture & Orchestration
- [x] **1.1** Design and implement agentic loops for autonomous task execution
- [x] **1.2** Orchestrate multi-agent systems with coordinator-subagent patterns
- [ ] **1.3** Configure subagent invocation, context passing, and spawning
- [ ] **1.4** Implement multi-step workflows with enforcement and handoff patterns
- [ ] **1.5** Apply Agent SDK hooks for tool call interception and data normalization
- [ ] **1.6** Design task decomposition strategies for complex workflows
- [ ] **1.7** Manage session state, resumption, and forking

## Domain 2: Tool Design & MCP Integration
- [ ] **2.1** Design effective tool interfaces with clear descriptions and boundaries
- [ ] **2.2** Implement structured error responses for MCP tools
- [ ] **2.3** Distribute tools appropriately across agents and configure tool choice
- [ ] **2.4** Integrate MCP servers into Claude Code and agent workflows
- [ ] **2.5** Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively

## Domain 3: Claude Code Configuration & Workflows
- [ ] **3.1** Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization
- [ ] **3.2** Create and configure custom slash commands and skills
- [ ] **3.3** Apply path-specific rules for conditional convention loading
- [ ] **3.4** Determine when to use plan mode vs direct execution
- [ ] **3.5** Apply iterative refinement techniques for progressive improvement
- [ ] **3.6** Integrate Claude Code into CI/CD pipelines

## Domain 4: Prompt Engineering & Structured Output
- [ ] **4.1** Design prompts with explicit criteria to improve precision and reduce false positives
- [ ] **4.2** Apply few-shot prompting to improve output consistency and quality
- [ ] **4.3** Enforce structured output using tool use and JSON schemas
- [ ] **4.4** Implement validation, retry, and feedback loops for extraction quality
- [ ] **4.5** Design efficient batch processing strategies
- [ ] **4.6** Design multi-instance and multi-pass review architectures

## Domain 5: Context Management & Reliability
- [ ] **5.1** Manage conversation context to preserve critical information across long interactions
- [ ] **5.2** Design effective escalation and ambiguity resolution patterns
- [ ] **5.3** Implement error propagation strategies across multi-agent systems
- [ ] **5.4** Manage context effectively in large codebase exploration
- [ ] **5.5** Design human review workflows and confidence calibration
- [ ] **5.6** Preserve information provenance and handle uncertainty in multi-source synthesis
