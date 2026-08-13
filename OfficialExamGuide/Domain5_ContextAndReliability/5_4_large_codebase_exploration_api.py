"""
Task Statement 5.4: Manage context effectively in large codebase exploration
(API VERSION)

This file demonstrates how to build the identical patterns tested in 5.4 using 
deterministic, code-first Python architecture instead of relying on the SDK.

Knowledge of:
- How to explore large codebases without reading entire files into context.
- Using targeted tools (`grep`, AST parsing) to pull just the relevant signatures.

Skills in:
- Implementing a tool that searches for function signatures instead of returning full file bodies.
"""

import os
import asyncio
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = AsyncAnthropic()


# ==============================================================================
# ==============================================================================

def get_function_signature(file_path: str, func_name: str) -> str:
    # Simulated AST parser behavior
    return f"Found: `def {func_name}(user_id: int, api_key: str) -> dict:` at line 452"

TOOLS = [
    {
        "name": "get_function_signature",
        "description": "Gets the exact line where a function is defined without reading the whole file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "func_name": {"type": "string"}
            },
            "required": ["file_path", "func_name"]
        }
    }
]

# ==============================================================================
# WORKFLOW
# ==============================================================================

async def run_codebase_exploration_api(user_request: str):
    
    system_prompt = (
        "You are a code explorer. You must find how to use the 'authenticate' function. "
        "DO NOT attempt to read entire files. Use the get_function_signature tool."
    )
    
    messages = [{"role": "user", "content": user_request}]
    max_iterations = 3
    
    for i in range(max_iterations):
        try:
            response = await client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=500,
                system=system_prompt,
                messages=messages,
                tools=TOOLS
            )
        except Exception as e:
            return "Workflow failed."
            
        messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason == "tool_use":
            for block in response.content:
                if block.type == "tool_use" and block.name == "get_function_signature":
                    res = get_function_signature(**block.input)
                    messages.append({
                        "role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": block.id, "content": res}]
                    })
        else:
            return next((b.text for b in response.content if b.type == 'text'), "")

    return "Max iterations reached."

if __name__ == "__main__":
    req = "How do I call the authenticate function in core.py?"
    res = asyncio.run(run_codebase_exploration_api(req))
