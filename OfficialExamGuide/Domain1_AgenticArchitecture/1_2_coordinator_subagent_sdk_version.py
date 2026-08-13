"""
Task Statement 1.2: Orchestrate multi-agent systems with coordinator-subagent patterns
(SDK VERSION FOR COMPARISON)

This version uses the `claude_agent_sdk` which abstracts the orchestration loop.
Notice how the routing and refinement logic relies heavily on a natural language 
system prompt (probabilistic) rather than strict Python code (deterministic).
"""

import os
import asyncio
import logging

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from claude_agent_sdk import ClaudeAgentOptions, AgentDefinition, query, ResultMessage

# ==============================================================================
# SUBAGENT DEFINITIONS
# ==============================================================================

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
# COORDINATOR WORKFLOW (Prompt-Driven Orchestration via SDK)
# ==============================================================================

async def run_hub_and_spoke_sdk_workflow(user_request: str):
    
    # Notice: Instead of strict Python code (like RoutingDecision or a while loop), 
    # we have to write a complex natural language prompt to convince Claude 
    # to route to subagents and loop iteratively. 
    coordinator_system_prompt = (
        "You are the Coordinator Agent. You manage a team of subagents: 'searcher' and 'synthesizer'.\n\n"
        "Your responsibilities:\n"
        "1. Dynamic Task Decomposition: Analyze the user's request. If it is simple, resolve it yourself without subagents. "
        "If complex, use the 'Agent' tool to invoke the 'searcher'.\n"
        "2. Partition Scope: To minimize duplication, break broad requests into distinct subtopics and invoke the 'searcher' "
        "separately for each subtopic (e.g. one task for 'visual arts', one for 'music'). Avoid overly narrow decomposition.\n"
        "3. Iterative Refinement Loop: Once you receive search results, invoke the 'synthesizer'. Read its output. "
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

    logging.info("--- Starting Prompt-Driven SDK Workflow ---")
    try:
        # The query() function abstracts away the routing and loop iteration.
        # It handles tool calls automatically, but we lose granular programmatic control 
        # (like asyncio.gather for parallel subagents, or explicit try/except Envelopes).
        async for msg in query(prompt=user_request, options=options):
            if isinstance(msg, ResultMessage):
                logging.info("--- Workflow Complete ---")
                return msg.content
            
    except Exception:
        # Expected exception handling when using a dummy API key
        pass

if __name__ == "__main__":
    request = "Research the impact of AI on both visual arts and the music industry, and synthesize a comprehensive report."
    result = asyncio.run(run_hub_and_spoke_sdk_workflow(request))
    print("\n=== FINAL SYNTHESIZED REPORT ===")
    print(result)
