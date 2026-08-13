"""
Task Statement 5.2: Design effective escalation and ambiguity resolution patterns
(API VERSION)

This file demonstrates how to build the identical patterns tested in 5.2 using 
deterministic, code-first Python architecture instead of relying on the SDK.

Knowledge of:
- How to instruct the LLM to STOP and ask the user for clarification rather than hallucinating an answer.
- When an `ask_human` tool is strictly necessary.

Skills in:
- Implementing an `ask_human` tool.
- Prompting strategies to mandate ambiguity resolution.
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
# EXAM SKILL: Ambiguity Resolution Tool
# ==============================================================================

def ask_human(question: str) -> str:
    print(f"\n[AGENT PAUSED TO ASK HUMAN]: {question}")
    # Simulated human answer
    return "I meant the production database."

def delete_database(db_name: str) -> str:
    return f"Deleted database {db_name}"

TOOLS = [
    {
        "name": "ask_human",
        "description": "Ask the human user a question to clarify ambiguity.",
        "input_schema": {
            "type": "object",
            "properties": {"question": {"type": "string"}},
            "required": ["question"]
        }
    },
    {
        "name": "delete_database",
        "description": "Deletes a database.",
        "input_schema": {
            "type": "object",
            "properties": {"db_name": {"type": "string"}},
            "required": ["db_name"]
        }
    }
]

# ==============================================================================
# WORKFLOW
# ==============================================================================

async def run_ambiguity_resolution_api(user_request: str):
    print(f"\n--- Starting Deterministic API Ambiguity Resolution Workflow ---")
    
    # ✅ BEST PRACTICE: Mandating ambiguity resolution
    system_prompt = (
        "You are a database admin. "
        "CRITICAL RULE: If a user asks you to delete or modify a database but does NOT explicitly "
        "specify whether they mean 'staging' or 'production', you MUST use the ask_human tool to clarify. "
        "DO NOT GUESS."
    )
    
    messages = [{"role": "user", "content": user_request}]
    
    # ANTI-TOKEN-HOG RULE: Limit iterations
    max_iterations = 3
    
    for i in range(max_iterations):
        print(f"--- Turn {i+1} ---")
        try:
            response = await client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=1000,
                system=system_prompt,
                messages=messages,
                tools=TOOLS
            )
        except Exception as e:
            print(f"[API Error - expected if dummy key] {e}")
            return "Workflow failed."
            
        messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason == "tool_use":
            for block in response.content:
                if block.type == "tool_use":
                    print(f"[LLM called tool: {block.name}] args: {block.input}")
                    
                    if block.name == "ask_human":
                        res = ask_human(**block.input)
                    elif block.name == "delete_database":
                        res = delete_database(**block.input)
                    else:
                        res = f"Unknown tool {block.name}"
                        
                    messages.append({
                        "role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": block.id, "content": res}]
                    })
        else:
            return next((b.text for b in response.content if b.type == 'text'), "")

    return "Max iterations reached."

if __name__ == "__main__":
    try:
        req = "Please delete the database immediately!"
        res = asyncio.run(run_ambiguity_resolution_api(req))
        print(f"\n[Agent Response]: {res}")
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed: {e}")
