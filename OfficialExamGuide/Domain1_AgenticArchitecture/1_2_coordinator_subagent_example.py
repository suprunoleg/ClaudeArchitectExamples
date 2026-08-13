"""
Task Statement 1.2: Orchestrate multi-agent systems with coordinator-subagent patterns

Knowledge of:
- Hub-and-spoke architecture where a coordinator agent manages all inter-subagent communication
- How subagents operate with isolated context (they do not inherit history automatically)
- The role of the coordinator in task decomposition, delegation, and result aggregation
- Risks of overly narrow task decomposition

Skills in:
- Designing coordinator agents that dynamically select subagents (not just fixed pipelines)
- Partitioning research scope to minimize duplication
- Implementing iterative refinement loops (evaluating gaps and re-delegating)
- Routing all communication through the coordinator for observability
"""

import os
import asyncio

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

from claude_agent_sdk import ClaudeAgentOptions, AgentDefinition, query, ResultMessage

# ==============================================================================
# SUBAGENT DEFINITIONS
# ==============================================================================
# EXAM SKILL: Subagents operate with isolated context. 
# They do not automatically inherit the coordinator's history. They only see what 
# the coordinator explicitly passes to them via the Task tool.

searcher_agent = AgentDefinition(
    description="Call this agent to search the web for raw data and articles about a specific subtopic.",
    prompt=(
        "You are the Searcher subagent. Your job is strictly to search and return raw facts. "
        "Do not synthesize or write a final report. Just return raw findings."
    )
)

synthesizer_agent = AgentDefinition(
    description="Call this agent to evaluate and synthesize research findings into a cohesive report.",
    prompt=(
        "You are the Synthesizer subagent. Given raw facts from the coordinator, organize them into a report. "
        "CRITICAL: If you notice information is missing to fully address the original topic, "
        "you MUST explicitly list those gaps under a 'Coverage Gaps' section."
    )
)

# ==============================================================================
# COORDINATOR WORKFLOW
# ==============================================================================
async def run_hub_and_spoke_workflow(user_request: str):
    
    # EXAM SKILL: Hub-and-spoke architecture and Dynamic Selection
    # The Coordinator is the main agent. It dynamically selects subagents rather than 
    # relying on a hardcoded sequential pipeline. It also handles iterative refinement.
    coordinator_system_prompt = (
        "You are the Coordinator Agent. You manage a team of subagents: 'searcher' and 'synthesizer'.\n\n"
        "Your responsibilities:\n"
        "1. Dynamic Task Decomposition: Analyze the user's request. If it is simple, resolve it yourself without subagents. "
        "If complex, use the 'Agent' tool to invoke the 'searcher'.\n"
        "2. Partition Scope: To minimize duplication, break broad requests into distinct subtopics and invoke the 'searcher' "
        "separately for each subtopic (e.g. one task for 'visual arts', one for 'music'). Avoid overly narrow decomposition.\n"
        "3. Routing: ALL communication must route through you. Subagents cannot talk to each other directly.\n"
        "4. Iterative Refinement Loop: Once you receive search results, invoke the 'synthesizer'. Read its output. "
        "If it reports 'Coverage Gaps', you MUST re-delegate targeted queries back to the 'searcher', then re-invoke "
        "the 'synthesizer' until coverage is complete before returning the final result to the user."
    )

    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        agents={
            "searcher": searcher_agent,
            "synthesizer": synthesizer_agent
        },
        system_prompt=coordinator_system_prompt
    )

    try:
        # EXAM SKILL: Routing all communication through the coordinator for observability
        # The query() function acts as the central router. The SDK automatically logs 
        # subagent tool_calls and tool_results here, providing full observability.
        async for msg in query(prompt=user_request, options=options):
            msg_type = getattr(msg, "type", None)
            
            # The coordinator handles intermediate processing (like checking for gaps)
            if isinstance(msg, ResultMessage):
                print("\n=== FINAL SYNTHESIZED REPORT ===")
                print(msg.content)
            
    except Exception:
        # Expected exception handling when using a dummy API key
        pass

if __name__ == "__main__":
    # A broad request designed to trigger the Coordinator's partitioning and iterative refinement logic
    request = "Research the impact of AI on both visual arts and the music industry, and synthesize a comprehensive report."
    asyncio.run(run_hub_and_spoke_workflow(request))
