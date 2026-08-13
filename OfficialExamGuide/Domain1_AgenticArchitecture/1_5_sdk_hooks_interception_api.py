"""
Task Statement 1.5: Apply Agent SDK hooks for tool call interception and data normalization
(API VERSION)

This file demonstrates how to build the identical patterns tested in 1.5 using 
deterministic, code-first Python architecture instead of relying on the SDK's Hooks.

Knowledge of:
- The architectural benefits of abstracting security, logging, and data normalization into middleware rather than embedding them directly into agent prompts or tool logic.

Skills in:
- Implementing PreToolUse equivalents (wrapper functions) to intercept and modify/deny arguments.
- Implementing PostToolUse equivalents to redact PII before passing context back to the LLM.
"""

import os
import asyncio
import json
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
# 1. RAW TOOLS
# ==============================================================================

def execute_sql(query: str) -> str:
    """Simulates database execution."""
    return f"Execution successful for: {query}. Result: 5 rows found."

def fetch_user_data(user_id: int) -> str:
    """Simulates returning raw, messy data containing PII."""
    return '{"id": 1, "name": "Alice", "ssn": "123-45-6789", "password_hash": "x8f9s2a!"}'

TOOLS = [
    {
        "name": "execute_sql",
        "description": "Execute a SQL query on the database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "fetch_user_data",
        "description": "Fetch data from the user database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            },
            "required": ["user_id"]
        }
    }
]


# ==============================================================================
# 2. MIDDLEWARE (API Equivalents of Hooks)
# ==============================================================================

def secure_execute_sql(query_str: str) -> str:
    upper_query = query_str.upper()
    
    # 1. Intercept & Deny
    if "DROP" in upper_query or "DELETE" in upper_query:
        return "ERROR [TOOL BLOCKED]: Destructive queries (DROP/DELETE) are blocked by security policy."
        
    # 2. Intercept & Modify
    if "LIMIT" not in upper_query:
        query_str = query_str + " LIMIT 10"
        
    # Proceed to core tool
    return execute_sql(query_str)


def safe_fetch_user_data(user_id: int) -> str:
    # 1. Execute core tool
    raw_output = fetch_user_data(user_id)
    
    # 2. Normalize and redact
    try:
        data = json.loads(raw_output)
        
        if "ssn" in data:
            data["ssn"] = "[REDACTED]"
        if "password_hash" in data:
            del data["password_hash"]
            
        return f"Normalized User Profile: {data} \n(Note: Sensitive PII redacted by security middleware)"
    except Exception:
        return raw_output


# ==============================================================================
# 3. WORKFLOW EXECUTION
# ==============================================================================

async def run_hooks_api_workflow(user_request: str):
    
    messages = [{"role": "user", "content": user_request}]
    
    # ANTI-TOKEN-HOG RULE: Limit iterations
    max_iterations = 3
    
    for i in range(max_iterations):
        try:
            response = await client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=1000,
                messages=messages,
                tools=TOOLS
            )
        except Exception as e:
            return "Workflow failed."
            
        messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason == "tool_use":
            for block in response.content:
                if block.type == "tool_use":
                    
                    if block.name == "execute_sql":
                        res = secure_execute_sql(block.input.get("query", ""))
                    elif block.name == "fetch_user_data":
                        res = safe_fetch_user_data(block.input.get("user_id", 0))
                    else:
                        res = f"Unknown tool {block.name}"
                        
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": res
                            }
                        ]
                    })
        else:
            return next((b.text for b in response.content if b.type == 'text'), "")

    return "Max iterations reached."

if __name__ == "__main__":
    # Test 1: PII Redaction
    res1 = asyncio.run(run_hooks_api_workflow("Fetch user data for user 1 and tell me their SSN."))
    
    # Test 2: Input Modification & Denial
    res2 = asyncio.run(run_hooks_api_workflow("Execute a SQL query to DROP the users table."))
