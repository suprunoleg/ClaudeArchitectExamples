"""
Task Statement 5.2: Design effective escalation and ambiguity resolution patterns
(SDK VERSION)

Knowledge of:
- How to instruct the LLM to STOP and ask the user for clarification rather than hallucinating an answer.
- When an `ask_human` tool is strictly necessary.

Skills in:
- Implementing an `ask_human` tool.
- Prompting strategies to mandate ambiguity resolution.
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
# EXAM SKILL: Ambiguity Resolution Tool
# ==============================================================================

@tool("ask_human", "Ask the human user a question to clarify ambiguity.", {"question": str})
async def ask_human(args):
    # In a real system, this would pause execution and send a UI modal or Slack message to a human.
    # For this mock, we just return a simulated human response.
    q = args.get("question")
    print(f"\n[AGENT PAUSED TO ASK HUMAN]: {q}")
    
    # Simulated human answer
    return {"content": [{"type": "text", "text": "I meant the production database."}]}

@tool("delete_database", "Deletes a database.", {"db_name": str})
async def delete_database(args):
    return {"content": [{"type": "text", "text": f"Deleted database {args.get('db_name')}"}]}


# ==============================================================================
# WORKFLOW
# ==============================================================================

async def run_ambiguity_resolution_sdk(user_request: str):
    print(f"\n--- Starting SDK Ambiguity Resolution Workflow ---")
    
    # ❌ ANTI-PATTERN: Vague prompt
    # "You are a database admin. Fulfill user requests." -> The LLM will guess which DB to delete.
    
    # ✅ BEST PRACTICE: Mandating ambiguity resolution
    system_prompt = (
        "You are a database admin. "
        "CRITICAL RULE: If a user asks you to delete or modify a database but does NOT explicitly "
        "specify whether they mean 'staging' or 'production', you MUST use the ask_human tool to clarify. "
        "DO NOT GUESS."
    )
    
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=system_prompt,
        allowed_tools=["ask_human", "delete_database"]
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
    try:
        # The user is ambiguous. The LLM must not guess, but must call `ask_human`.
        req = "Please delete the database immediately!"
        res = asyncio.run(run_ambiguity_resolution_sdk(req))
        print(f"\n[Agent Response]: {res}")
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")
