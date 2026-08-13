"""
Task Statement 5.4: Manage context effectively in large codebase exploration
(SDK VERSION)

Knowledge of:
- How to explore large codebases without reading entire files into context.
- Using targeted tools (`grep`, AST parsing) to pull just the relevant signatures.

Skills in:
- Implementing a tool that searches for function signatures instead of returning full file bodies.
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

# If a file is 15,000 lines, this instantly blows out the LLM's context window.

@tool("get_function_signature", "Gets the exact line where a function is defined without reading the whole file.", {"file_path": str, "func_name": str})
async def get_function_signature(args):
    # In a real system, you would use `ast` or `ripgrep` here.
    # For this mock, we simulate returning just the signature line.
    func_name = args.get("func_name")
    return {"content": [{"type": "text", "text": f"Found: `def {func_name}(user_id: int, api_key: str) -> dict:` at line 452"}]}


# ==============================================================================
# WORKFLOW
# ==============================================================================

async def run_codebase_exploration_sdk(user_request: str):
    
    system_prompt = (
        "You are a code explorer. You must find how to use the 'authenticate' function. "
        "DO NOT attempt to read entire files. Use the get_function_signature tool."
    )
    
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=system_prompt,
        allowed_tools=["get_function_signature"]
    )

    try:
        final_output = None
        async for msg in query(prompt=user_request, options=options):
            if isinstance(msg, ResultMessage):
                final_output = msg.result
        return final_output
    except Exception as e:
        return "[Mock Response expected if dummy key]"

if __name__ == "__main__":
    req = "How do I call the authenticate function in core.py?"
    res = asyncio.run(run_codebase_exploration_sdk(req))
