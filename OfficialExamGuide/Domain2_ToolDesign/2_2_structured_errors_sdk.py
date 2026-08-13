"""
Task Statement 2.2: Implement structured error responses for MCP tools
(SDK VERSION)

Knowledge of:
- The `isError` MCP protocol flag and how it influences LLM behavior.
- The difference between a system crash vs a graceful tool error.

Skills in:
- Returning `{ isError: true, content: [...] }` so the LLM knows it made a mistake and can retry.
- Providing actionable feedback in the error text (e.g., "File not found. Did you mean X?").
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

@tool("bad_read_file", "Reads a file.", {"filepath": str})
async def bad_read_file(args):
    filepath = args.get("filepath")
    # If file doesn't exist, this throws a raw Exception.
    # The LLM doesn't get a helpful error message, and the agentic loop might crash.
    with open(filepath, "r") as f:
        return {"content": [{"type": "text", "text": f.read()}]}


@tool("good_read_file", "Reads a file from the workspace.", {"filepath": str})
async def good_read_file(args):
    filepath = args.get("filepath")
    
    if not os.path.exists(filepath):
        return {
            "isError": True, 
            "content": [{
                "type": "text", 
                "text": f"Error: File '{filepath}' not found. Did you mean to use an absolute path, or is it in a different directory?"
            }]
        }
        
    try:
        with open(filepath, "r") as f:
            return {"content": [{"type": "text", "text": f.read()}]}
    except PermissionError:
        return {
            "isError": True,
            "content": [{"type": "text", "text": f"Error: Permission denied reading '{filepath}'."}]
        }


# ==============================================================================
# WORKFLOW
# ==============================================================================

async def run_structured_error_sdk(user_request: str):
    
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        allowed_tools=["good_read_file"],
        system_prompt="You are an assistant that reads files. If a tool returns an error, try to fix the argument and retry once."
    )

    try:
        final_output = None
        # ANTI-TOKEN-HOG: Limit the loop automatically through query config if possible, 
        # but the LLM will see isError=True and either fix it or stop.
        async for msg in query(prompt=user_request, options=options):
            if isinstance(msg, ResultMessage):
                final_output = msg.result
        return final_output
    except Exception as e:
        pass

if __name__ == "__main__":
    req = "Read the contents of 'missing_config.json'."
    res = asyncio.run(run_structured_error_sdk(req))
