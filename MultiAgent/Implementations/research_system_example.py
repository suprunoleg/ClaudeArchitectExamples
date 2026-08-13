"""
Research Agent System

Implements a specialized multi-agent workflow designed for deep research,
involving searching, reading, and synthesizing information. It typically
involves a planner agent, researcher agents, and a writer agent working in
tandem.
"""

import os
import asyncio
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables

load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AgentDefinition,
    ResultMessage,
    tool
)

# ==============================================================================
# 1. ENFORCING STRUCTURE VIA SDK TOOLS
# ==============================================================================
# Since AgentDefinition doesn't natively accept 'output_format', the standard
# SDK pattern to force a subagent to return structured data is to give it a 
# required tool that matches your desired schema.

@tool(
    name="submit_research_findings",
    description="Use this tool to submit your final structured research findings.",
    input_schema={
        "type": "object",
        "properties": {
            "research_topic": {"type": "string"},
            "facts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {"type": "string"},
                        "citation": {"type": "string"}
                    }
                }
            }
        },
        "required": ["research_topic", "facts"]
    }
)
def submit_research_findings(research_topic: str, facts: list[dict]) -> str:
    return "Findings submitted successfully! You may now stop."

# ==============================================================================
# 2. DEFINE NATIVE SDK SUBAGENTS
# ==============================================================================
# Instead of writing custom loops or wrappers, we declare our subagents
# using the SDK's built-in AgentDefinition configuration.

researcher_agent = AgentDefinition(
    description="Call this agent to gather deep, factual, and comprehensive information on a topic.",
    prompt=(
        "You are an expert Researcher Agent. Your only job is to gather deep, factual, "
        "and comprehensive information on the requested topic. "
        "CRITICAL REQUIREMENT: For every fact, statistic, or claim you provide, you MUST "
        "include a verifiable citation (e.g., [Source: Name of Paper/Website, Year]).\n\n"
        "When you are finished researching, you MUST call the `submit_research_findings` tool "
        "to output your data in strict structured format."
    ),
    tools=["submit_research_findings"]
)

synthesizer_agent = AgentDefinition(
    description="Call this agent to format and structure raw research notes into a final deliverable.",
    prompt=(
        "You are an expert Synthesizer Agent. You will receive raw research notes. "
        "Your job is to structure and format this data strictly as requested. "
        "Do not invent new facts. Just organize the provided notes beautifully."
    )
)

# ==============================================================================
# 3. DEFINE PYDANTIC SCHEMA FOR FINAL OUTPUT
# ==============================================================================
class FinalRecommendation(BaseModel):
    final_recommendation: str = Field(description="The executive summary")
    key_differences: list[str] = Field(description="List of core architectural differences")

# ==============================================================================
# 4. RUN THE COORDINATOR AGENT
# ==============================================================================
async def run_coordinator(user_request: str):
    print(f"\n{'='*70}\n[COORDINATOR] Received Request: '{user_request}'\n{'='*70}")
    
    # We configure the main Coordinator agent by passing the subagents into its options.
    # We also use the native 'output_format' property with our Pydantic schema to guarantee 
    # the Coordinator's final response is a strictly structured JSON object!
    # We override the main system prompt for this specific query so the Coordinator knows its role.
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        agents={
            "Researcher": researcher_agent,
            "Synthesizer": synthesizer_agent
        },
        output_format={
            "type": "json_schema",
            "schema": FinalRecommendation.model_json_schema()
        },
        system_prompt=(
            "You are the Coordinator Agent. You manage a team of specialists. "
            "To satisfy the user's request, first use the `Agent` tool to invoke the 'Researcher' to gather facts. "
            "Once you have the facts, you MUST use the `Agent` tool again to invoke the 'Synthesizer' to format them. "
            "Finally, present the synthesized data to the user."
        )
    )
    
    try:
        # We use the SDK's `query` helper to automatically manage the loop and yield the ResultMessage
        async for msg in query(
            prompt=user_request, 
            options=options
        ):
            if isinstance(msg, ResultMessage):
                print(f"\n[COORDINATOR FINAL RESULT] Extracting Pydantic Object...")
                if msg.structured_output:
                    # Parse the raw dictionary back into a fully-typed Pydantic object
                    result = FinalRecommendation.model_validate(msg.structured_output)
                    print(f"\n Final Recommendation:\n{result.final_recommendation}")
                    print(f"\n Key Differences:")
                    for diff in result.key_differences:
                        print(f"  - {diff}")
            else:
                m_type = getattr(msg, "type", None)
                if m_type == "assistant":
                    pass
                elif m_type == "tool_use":
                    print(f"[SDK ROUTING] Delegating via Tool: {getattr(msg, 'tool_name', 'tool')} with args: {getattr(msg, 'tool_input', {})}")
                elif m_type == "tool_result":
                    print(f"[SDK RESULT] Subagent completed task. Sending data back to Coordinator.")
                elif m_type == "notification":
                    print(f"  {getattr(msg, 'message', '')}")
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")

if __name__ == "__main__":
        
    request = "Research the architectural differences between React and Vue, then synthesize a final recommendation for a small startup as an executive summary."
    asyncio.run(run_coordinator(request))
