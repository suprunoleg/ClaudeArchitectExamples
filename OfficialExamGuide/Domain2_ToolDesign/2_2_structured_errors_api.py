"""
Task Statement 2.2: Implement structured error responses for MCP tools
(API VERSION)

This file demonstrates how to build the identical patterns tested in 2.2 using 
deterministic, code-first Python architecture instead of relying on the SDK.

Knowledge of:
- The `is_error` API protocol flag and how it influences LLM behavior.
- The difference between a system crash vs a graceful tool error.

Skills in:
- Returning `is_error=True` so the LLM knows it made a mistake and can retry.
- Providing actionable feedback in the error text.
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

def good_read_file(filepath: str) -> dict:
    if not os.path.exists(filepath):
        # In the raw Anthropic API, this translates to setting is_error=True in the tool_result block
        return {
            "is_error": True,
            "text": f"Error: File '{filepath}' not found. Did you mean to use an absolute path, or is it in a different directory?"
        }
        
    try:
        with open(filepath, "r") as f:
            return {"is_error": False, "text": f.read()}
    except PermissionError:
        return {
            "is_error": True,
            "text": f"Error: Permission denied reading '{filepath}'."
        }

TOOL_SCHEMA = {
    "name": "good_read_file",
    "description": "Reads a file from the workspace.",
    "input_schema": {
        "type": "object",
        "properties": {
            "filepath": {"type": "string"}
        },
        "required": ["filepath"]
    }
}

# ==============================================================================
# WORKFLOW
# ==============================================================================

async def run_structured_error_api(user_request: str):
    
    system_prompt = "You are an assistant that reads files. If a tool returns an error, try to fix the argument and retry once."
    messages = [{"role": "user", "content": user_request}]
    
    # ANTI-TOKEN-HOG RULE: Limit iterations
    max_iterations = 3
    
    for i in range(max_iterations):
        try:
            response = await client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=1000,
                system=system_prompt,
                messages=messages,
                tools=[TOOL_SCHEMA]
            )
        except Exception as e:
            return "Workflow failed."
            
        messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason == "tool_use":
            for block in response.content:
                if block.type == "tool_use":
                    
                    if block.name == "good_read_file":
                        result_dict = good_read_file(**block.input)
                        
                        # Pack the result into the Anthropic tool_result format
                        tool_result_block = {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "is_error": result_dict["is_error"],
                            "content": result_dict["text"]
                        }
                    else:
                        tool_result_block = {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "is_error": True,
                            "content": f"Unknown tool {block.name}"
                        }
                        
                    messages.append({"role": "user", "content": [tool_result_block]})
        else:
            return next((b.text for b in response.content if b.type == 'text'), "")

    return "Max iterations reached."

if __name__ == "__main__":
    req = "Read the contents of 'missing_config.json'."
    res = asyncio.run(run_structured_error_api(req))
