"""
API Event Hooks

Shows how to implement pre- and post-execution hooks to intercept, log, or
modify API requests and responses. Hooks are a powerful architectural pattern
for injecting observability, auditing, and fallback logic without polluting
the core business logic.
"""

import os
import json
import asyncio
from datetime import datetime
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    HookMatcher,
    UserPromptSubmitHookInput,
    PreToolUseHookInput,
    PostToolUseHookInput,
    PreCompactHookInput,
    HookContext,
    tool,
    create_sdk_mcp_server
)

# ==============================================================================
# 1. DEFINE TOOLS
# ==============================================================================
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
            "text": '{"id": 1, "name": "Alice", "password_hash": "x8f9s2a!"}'
        }]
    }

# Create an in-process MCP server to host our custom tools
db_server = create_sdk_mcp_server(name="db_server", tools=[execute_sql, fetch_user_data])


# ==============================================================================
# 2. DEFINE HOOKS
# ==============================================================================

# A. UserPromptSubmit Hook (Context Injection)
async def user_prompt_hook(event: UserPromptSubmitHookInput, matcher: str | None, context: HookContext) -> dict:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"System Time: {current_time} | OS: {os.name}"
        }
    }

# B. PreToolUse Hook (Security Guardrail & Input Modification)
async def pre_tool_hook(event: PreToolUseHookInput, matcher: str | None, context: HookContext) -> dict:
    query = event.tool_input.get("query", "").upper()
    
    # Security rule: Deny destructive commands
    if "DROP" in query or "DELETE" in query:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny", 
                "permissionDecisionReason": "Destructive queries (DROP/DELETE) are blocked by policy."
            }
        }
        
    # Security rule: Modify input to force a LIMIT clause for safety
    if "LIMIT" not in query:
        modified_query = query + " LIMIT 10"
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedToolInput": {"query": modified_query}
            }
        }

    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}


# C. PostToolUse Hook (Sanitization, Normalization, & User Notification)
async def post_tool_hook(event: PostToolUseHookInput, matcher: str | None, context: HookContext) -> dict:
    raw_output = event.tool_output
    
    # Sanitize data
    try:
        data = json.loads(raw_output) if isinstance(raw_output, str) else raw_output
        if "password_hash" in data:
            data["password_hash"] = "[REDACTED PII]"
        clean_result = f"Cleaned Result for User {data.get('id')}: {data.get('name')} (Password: {data.get('password_hash')})"
    except Exception:
        clean_result = raw_output

    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "updatedToolOutput": clean_result, # To Claude
            "additionalContext": "Note to Claude: This user's password hash was redacted.", # To Claude
            "systemMessage": f"🔒 Security Notice: Redacted PII before sending logs to Claude." # To Human
        }
    }

# D. PreCompact Hook (State Preservation)
async def precompact_hook(event: PreCompactHookInput, matcher: str | None, context: HookContext) -> dict:
    vital_instruction = (
        "\n[SYSTEM RESTORED STATE]: Older history was truncated. "
        "Remember to format all outputs strictly as requested."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreCompact",
            "additionalContext": vital_instruction
        }
    }


# ==============================================================================
# 3. CONSOLIDATED EXECUTION LOOP
# ==============================================================================
async def run_agent_loop(user_prompt: str):
    print(f"\n{'='*60}\nRunning Agent: '{user_prompt}'\n{'='*60}")
    
    # Wire up all hooks in a single options configuration
    options = ClaudeAgentOptions(
        mcp_servers={"db_server": db_server},
        allowed_tools=["execute_sql", "fetch_user_data"],
        hooks={
            "UserPromptSubmit": [HookMatcher(hooks=[user_prompt_hook])],
            "PreCompact": [HookMatcher(hooks=[precompact_hook])],
            "PreToolUse": [
                HookMatcher(
                    matcher="execute_sql", # ONLY apply guardrail to execute_sql
                    hooks=[pre_tool_hook]
                )
            ],
            "PostToolUse": [
                HookMatcher(
                    matcher="fetch_user_data", # ONLY sanitize fetch_user_data
                    hooks=[post_tool_hook]
                )
            ]
        }
    )
    
    client = ClaudeSDKClient(options=options)
    await client.connect()
    
    try:
        await client.query(user_prompt)
        async for msg in client.receive_messages():
            if msg.type == "assistant":
                print(f"[CLAUDE MESSAGE]: {msg.content}")
            elif msg.type == "tool_use":
                print(f"[SDK RUNNING TOOL]: {msg.tool_name} with args: {msg.tool_input}")
            elif msg.type == "tool_result":
                print(f"[SDK TOOL RESULT TO CLAUDE]: {msg.content}")
            elif msg.type == "notification":
                print(f"\n🖥️  [SYSTEM UI NOTIFICATION]: {msg.message}\n")
    except Exception as e:
        print(f"[SYSTEM] Encountered expected runtime error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    if "ANTHROPIC_API_KEY" not in os.environ:
        os.environ["ANTHROPIC_API_KEY"] = "dummy_key"
        
    # Trigger PostToolUse hook on fetch_user_data
    asyncio.run(run_agent_loop("Fetch user data for user 1 and tell me their password hash."))
    
    # Trigger PreToolUse hook (Input Modification) on execute_sql
    asyncio.run(run_agent_loop("Please check the user count by running: SELECT * FROM users;"))
    
    # Trigger PreToolUse hook (Denial) on execute_sql
    asyncio.run(run_agent_loop("I need to clean the database. Drop the users table."))
