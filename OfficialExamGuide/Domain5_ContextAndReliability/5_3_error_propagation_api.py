"""
Task Statement 5.3: Implement error propagation strategies across multi-agent systems
(API VERSION)

Knowledge of:
- How errors from a subagent bubble up to a coordinator agent.
- How the coordinator can catch the error and decide whether to retry or fail.

Skills in:
- Using `try/except` around subagent invocations.
- Exposing subagent failure reasons to the coordinator using `is_error`.
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

async def failing_subagent_logic(query: str):
    raise ConnectionError("Database timed out while searching.")

TOOLS = [
    {
        "name": "search_db",
        "description": "Searches the database. Might fail.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    }
]

# ==============================================================================
# WORKFLOW
# ==============================================================================

async def run_error_propagation_api(user_request: str):
    
    system_prompt = (
        "You are the coordinator. You must search the database to answer the user's question. "
        "If the search tool returns an error, tell the user the system is temporarily down, "
        "but do NOT try to guess the answer."
    )
    
    messages = [{"role": "user", "content": user_request}]
    max_iterations = 2
    
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
                if block.type == "tool_use" and block.name == "search_db":
                    
                    try:
                        res = await failing_subagent_logic(**block.input)
                        is_error = False
                    except Exception as e:
                        res = f"SYSTEM ERROR IN SUBAGENT: {str(e)}"
                        is_error = True
                        
                    messages.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result", 
                            "tool_use_id": block.id, 
                            "content": res,
                            "is_error": is_error
                        }]
                    })
        else:
            return next((b.text for b in response.content if b.type == 'text'), "")

    return "Max iterations reached."

if __name__ == "__main__":
    req = "What is John's phone number?"
    res = asyncio.run(run_error_propagation_api(req))
