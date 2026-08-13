"""
Task Statement 1.3: Configure subagent invocation, context passing, and spawning
(SDK VERSION)

Knowledge of:
- The Task tool as the mechanism for spawning subagents, and the requirement that allowedTools must include "Task"
- That subagent context must be explicitly provided in the prompt—subagents do not automatically inherit parent context
- The AgentDefinition configuration including descriptions, system prompts, and tool restrictions
- Fork-based session management for exploring divergent approaches

Skills in:
- Including complete findings from prior agents directly in the subagent's prompt
- Using structured data formats to separate content from metadata when passing context
- Spawning parallel subagents by emitting multiple Task tool calls in a single coordinator response
- Designing coordinator prompts that specify research goals and quality criteria rather than step-by-step instructions
"""

import os
import asyncio
from claude_agent_sdk import ClaudeAgentOptions, AgentDefinition, query, ResultMessage
from dotenv import load_dotenv

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


# ==============================================================================
# SUBAGENT DEFINITIONS
# ==============================================================================

searcher_agent = AgentDefinition(
    description="Call this agent to search the web for raw data about a specific topic.",
    prompt=(
        "You are the Searcher subagent. Your job is to return factual bullet points about the topic provided in your prompt. "
        "IMPORTANT: You operate in an isolated context and cannot see the user's original request. "
    ),
    # By omitting "Task" or explicitly disallowing it, we prevent the searcher from spawning its own subagents
    disallowedTools=["Task"] 
)

synthesizer_agent = AgentDefinition(
    description="Call this agent to synthesize multiple findings into a final report.",
    prompt=(
        "You are the Synthesizer subagent. You will receive structured data containing findings from various searchers. "
        "Synthesize them into a cohesive summary."
    ),
    disallowedTools=["Task"]
)

# ==============================================================================
# COORDINATOR WORKFLOW
# ==============================================================================

async def run_spawning_sdk_workflow(user_request: str):
    
    coordinator_system_prompt = (
        "You are the Coordinator Agent. You manage 'searcher' and 'synthesizer' subagents.\n\n"
        "GOAL: Deliver a highly accurate, synthesized research report.\n\n"
        "RULES:\n"
        "1. EXAM SKILL: Spawning parallel subagents. When delegating searches, you MUST emit multiple "
        "'Task' tool calls in a single response turn to run them in parallel.\n"
        "2. EXAM SKILL: Subagents do not inherit parent context. When you invoke the synthesizer, you MUST "
        "pass all search findings directly in the prompt.\n"
        "3. EXAM SKILL: Structured data formats. When passing findings to the synthesizer, format them as: "
        "[Source: <subtopic>] <findings>.\n"
    )

    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        agents={
            "searcher": searcher_agent,
            "synthesizer": synthesizer_agent
        },
        allowed_tools=["Agent"],
        system_prompt=coordinator_system_prompt
    )
    try:
        final_output = None
        async for msg in query(prompt=user_request, options=options):
            # Optional: Log tool usage to prove parallel execution
            m_type = getattr(msg, "type", None)
            if m_type == "tool_use" and getattr(msg, "tool_name", "") == "Task":
                pass

            if isinstance(msg, ResultMessage):
                final_output = msg.result
        return final_output
                
    except Exception as e:
        # Expected exception handling when using a dummy API key
        pass

if __name__ == "__main__":
    request = "Research the history of the Apollo 11 mission and the Voyager 1 mission."
    result = asyncio.run(run_spawning_sdk_workflow(request))
    if result:
        pass
