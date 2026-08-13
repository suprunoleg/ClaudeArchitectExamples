"""
Task Statement 2.3: Distribute tools appropriately across agents and configure tool choice
(SDK VERSION)

Knowledge of:
- The principle of least privilege (only giving agents the tools they need).
- How tool_choice ("auto", "any", "tool") forces or restricts LLM behavior.

Skills in:
- Configuring tool_choice to force a specific tool execution.
- Creating highly bounded subagents that only have access to 1-2 specific tools.
"""

import os
import asyncio
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, AgentDefinition, query, ResultMessage, tool

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


# ==============================================================================
# TOOLS
# ==============================================================================

@tool("web_search", "Search the web for information.", {"query": str})
async def web_search(args):
    return {"content": [{"type": "text", "text": f"Search results for {args.get('query')}"}]}

@tool("write_file", "Write content to a file.", {"filepath": str, "content": str})
async def write_file(args):
    return {"content": [{"type": "text", "text": "File written."}]}

@tool("submit_final_report", "Submit the final report to the user.", {"report_text": str})
async def submit_final_report(args):
    return {"content": [{"type": "text", "text": "Report submitted."}]}


# ==============================================================================
# ==============================================================================

# If the researcher hallucinated, it could overwrite critical files.

researcher_agent = AgentDefinition(
    description="A researcher that only searches the web.",
    prompt="You are a researcher. Use the web_search tool to find information.",
    tools=["web_search"],
    disallowedTools=["Task", "write_file", "submit_final_report"] 
)

# ==============================================================================
# WORKFLOW
# ==============================================================================

async def run_tool_distribution_sdk(user_request: str):
    
    # Coordinator has access to subagents and the final report tool
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt="You are the Coordinator. Delegate research, then submit the final report.",
        allowed_tools=["Task", "submit_final_report"],
        # If we wanted to FORCE the model to immediately use a tool without chatting,
        # we could use: tool_choice={"type": "any"} or {"type": "tool", "name": "submit_final_report"}
        # Note: claude_agent_sdk abstracts this via `response_schema` or raw tool config.
    )

    try:
        final_output = None
        async for msg in query(prompt=user_request, options=options):
            if isinstance(msg, ResultMessage):
                final_output = msg.result
        return final_output
    except Exception as e:
        pass

if __name__ == "__main__":
    req = "Research Quantum Computing and submit a report."
    res = asyncio.run(run_tool_distribution_sdk(req))
