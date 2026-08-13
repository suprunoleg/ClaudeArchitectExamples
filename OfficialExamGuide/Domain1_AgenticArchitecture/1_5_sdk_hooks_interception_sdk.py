"""
Task Statement 1.5: Apply Agent SDK hooks for tool call interception and data normalization
(SDK VERSION)

Knowledge of:
- The architectural benefits of abstracting security, logging, and data normalization into middleware (hooks) rather than embedding them directly into agent prompts or tool logic.
- Which hook lifecycle events correspond to specific architectural needs (e.g., PreToolUse for interception, PostToolUse for data redaction).

Skills in:
- Implementing PreToolUse hooks to intercept and dynamically modify out-of-policy tool arguments (or outright deny execution).
- Implementing PostToolUse hooks to redact PII or normalize inconsistent data shapes before returning the context back to the model.
"""

import os
import asyncio
import json
from typing import Optional
from dotenv import load_dotenv

from claude_agent_sdk import (
    ClaudeAgentOptions, 
    query, 
    ResultMessage,
    tool,
    create_sdk_mcp_server,
    HookMatcher,
    PreToolUseHookInput,
    PostToolUseHookInput,
    HookContext
)

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


# ==============================================================================
# 1. RAW TOOLS
# ==============================================================================
# Notice how the tools contain NO security or redaction logic.
# They are purely functional.

@tool("execute_sql", "Execute a SQL query on the database.", {"query": str})
async def execute_sql(args):
    """Simulates database execution."""
    return {"content": [{"type": "text", "text": f"Execution successful for: {args['query']}. Result: 5 rows found."}]}

@tool("fetch_user_data", "Fetch data from the user database.", {"user_id": int})
async def fetch_user_data(args):
    """Simulates returning raw, messy data containing PII."""
    return {
        "content": [{
            "type": "text", 
            "text": '{"id": 1, "name": "Alice", "ssn": "123-45-6789", "password_hash": "x8f9s2a!"}'
        }]
    }

db_server = create_sdk_mcp_server(name="db_server", tools=[execute_sql, fetch_user_data])


# ==============================================================================
# 2. SDK HOOKS (Middleware)
# ==============================================================================

# EXAM SKILL: Implementing PreToolUse hooks to intercept and modify/deny arguments
async def pre_sql_hook(event: PreToolUseHookInput, matcher: Optional[str], context: HookContext) -> dict:
    query_str = event.tool_input.get("query", "").upper()
    
    # 1. Intercept & Deny
    if "DROP" in query_str or "DELETE" in query_str:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny", 
                "permissionDecisionReason": "Destructive queries (DROP/DELETE) are blocked by security policy."
            }
        }
        
    # 2. Intercept & Modify
    if "LIMIT" not in query_str:
        modified_query = event.tool_input.get("query", "") + " LIMIT 10"
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedToolInput": {"query": modified_query}
            }
        }

    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}


# EXAM SKILL: Implementing PostToolUse hooks to redact PII and normalize data
async def post_fetch_hook(event: PostToolUseHookInput, matcher: Optional[str], context: HookContext) -> dict:
    raw_output = event.tool_output
    
    try:
        # Extract the text string from the ToolResult structure
        if isinstance(raw_output, dict) and "content" in raw_output:
            text_val = raw_output["content"][0]["text"]
            data = json.loads(text_val)
            
            # Redact PII
            if "ssn" in data:
                data["ssn"] = "[REDACTED]"
            if "password_hash" in data:
                del data["password_hash"]
                
            clean_result = f"Normalized User Profile: {data}"
        else:
            clean_result = str(raw_output)
    except Exception:
        clean_result = str(raw_output)

    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "updatedToolOutput": clean_result, 
            "additionalContext": "Note to Claude: Sensitive PII was redacted by the security middleware."
        }
    }


# ==============================================================================
# 3. WORKFLOW EXECUTION
# ==============================================================================

async def run_hooks_sdk_workflow(user_request: str):
    print(f"\n--- Starting SDK Hooks Workflow: '{user_request}' ---")
    
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        mcp_servers={"db_server": db_server},
        allowed_tools=["execute_sql", "fetch_user_data"],
        hooks={
            "PreToolUse": [
                HookMatcher(matcher="execute_sql", hooks=[pre_sql_hook])
            ],
            "PostToolUse": [
                HookMatcher(matcher="fetch_user_data", hooks=[post_fetch_hook])
            ]
        }
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
    try:
        # Test 1: PII Redaction
        res1 = asyncio.run(run_hooks_sdk_workflow("Fetch user data for user 1 and tell me their SSN."))
        print(f"[Agent Response] {res1}")
        
        # Test 2: Input Modification & Denial
        res2 = asyncio.run(run_hooks_sdk_workflow("Execute a SQL query to DROP the users table."))
        print(f"[Agent Response] {res2}")
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")
