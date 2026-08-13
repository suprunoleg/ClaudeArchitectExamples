"""
Task Statement 2.1: Design effective tool interfaces with clear descriptions and boundaries
(SDK VERSION)

Knowledge of:
- How the LLM interprets tool descriptions and parameter descriptions as part of its system prompt.
- The impact of poorly bounded tools (e.g., overlapping functionality) on routing reliability.

Skills in:
- Writing unambiguous tool descriptions that specify exactly what the tool does, what it returns, and when NOT to use it.
- Enforcing strict typing, enums, and required parameters in JSON schema.
"""

import os
import asyncio
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, query, ResultMessage, tool

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


# ==============================================================================
# ==============================================================================

# Description is too vague. When does the model use this vs a specific search?
# Missing parameter descriptions.
@tool(
    name="get_data", 
    description="Gets data about users or orders.", 
    parameters={"query_type": str, "id": str}
)
async def bad_get_data(args):
    return {"content": [{"type": "text", "text": "Raw data."}]}


# - Specifies EXACTLY what it does and what it returns.
# - Specifies when NOT to use it (boundary definition).
# - Uses Enums to restrict string inputs to valid options.
@tool(
    name="get_user_profile", 
    description=(
        "Retrieves the complete profile for a single verified user. "
        "Returns the user's name, email, and account tier. "
        "DO NOT use this tool to search for users by name; you must have the exact User ID."
    ), 
    parameters={
        "user_id": {
            "type": "string",
            "description": "The exact alphanumeric User ID (e.g., 'U-12345')."
        },
        "detail_level": {
            "type": "string",
            "description": "How much data to return. Must be 'basic' or 'full'.",
            "enum": ["basic", "full"]
        }
    }
)
async def good_get_user_profile(args):
    return {"content": [{"type": "text", "text": "Alice, alice@example.com, Tier: Premium"}]}


# ==============================================================================
# WORKFLOW
# ==============================================================================

async def run_tool_design_sdk(user_request: str):
    
    # Notice we only supply the well-designed tool to prevent routing confusion
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        allowed_tools=["get_user_profile"],
        system_prompt="You are a helpful database assistant."
    )

    try:
        final_output = None
        # ANTI-TOKEN-HOG: Just query once
        async for msg in query(prompt=user_request, options=options):
            if isinstance(msg, ResultMessage):
                final_output = msg.result
        return final_output
    except Exception as e:
        pass

if __name__ == "__main__":
    # The LLM will easily map "U-999" to user_id and select an enum for detail_level
    req = "Can you look up the full profile for user U-999?"
    res = asyncio.run(run_tool_design_sdk(req))
