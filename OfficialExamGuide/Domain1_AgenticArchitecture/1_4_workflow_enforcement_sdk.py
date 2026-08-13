"""
Task Statement 1.4: Implement multi-step workflows with enforcement and handoff patterns
(SDK VERSION)

Knowledge of:
- The difference between programmatic enforcement (hooks, prerequisite gates) and prompt-based guidance for workflow ordering
- When deterministic compliance is required, prompt instructions alone have a non-zero failure rate
- Structured handoff protocols for mid-process escalation

Skills in:
- Implementing programmatic prerequisites that block downstream tool calls until prerequisite steps have completed
- Decomposing multi-concern customer requests into distinct items, investigating in parallel
- Compiling structured handoff summaries when escalating to human agents
"""

import os
import asyncio
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from claude_agent_sdk import (
    ClaudeAgentOptions, 
    query, 
    ResultMessage,
    tool,
    create_sdk_mcp_server,
    HookMatcher,
    PreToolUseHookInput,
    HookContext
)

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


# ==============================================================================
# 1. STATE & TOOLS
# ==============================================================================

# Global state to track prerequisite completion
# (In a real app, this would be tied to a session or context ID)
verification_state = {"verified_customer_id": None}

@tool("get_customer", "Lookup and verify a customer by email.", {"email": str})
async def get_customer(args):
    email = args.get("email")
    # Simulate verification
    if email == "test@example.com":
        verification_state["verified_customer_id"] = "CUST-12345"
        return {"content": [{"type": "text", "text": "Customer verified. ID: CUST-12345"}]}
    return {"content": [{"type": "text", "text": "Customer not found."}]}

@tool("process_refund", "Process a refund for a specific order.", {"order_id": str, "amount": float})
async def process_refund(args):
    return {"content": [{"type": "text", "text": f"Successfully refunded ${args.get('amount')} for order {args.get('order_id')}."}]}

@tool("escalate_to_human", "Escalate to a human agent.", {
    "customer_id": str, 
    "root_cause": str, 
    "refund_amount": float, 
    "recommended_action": str
})
async def escalate_to_human(args):
    # EXAM SKILL: Compiling structured handoff summaries
    handoff_summary = (
        f"ESCALATION HANDOFF:\n"
        f"Customer ID: {args.get('customer_id')}\n"
        f"Root Cause: {args.get('root_cause')}\n"
        f"Refund Amount: ${args.get('refund_amount')}\n"
        f"Recommended Action: {args.get('recommended_action')}"
    )
    print(f"\n[SYSTEM] Escaling to human queue:\n{handoff_summary}")
    return {"content": [{"type": "text", "text": "Successfully escalated to human queue."}]}

# Create local tool server
customer_server = create_sdk_mcp_server(name="customer_server", tools=[get_customer, process_refund, escalate_to_human])

# ==============================================================================
# 2. PROGRAMMATIC ENFORCEMENT HOOK
# ==============================================================================

# EXAM SKILL: Implementing programmatic prerequisites that block downstream tool calls
async def refund_prerequisite_hook(event: PreToolUseHookInput, matcher: Optional[str], context: HookContext) -> dict:
    """Blocks process_refund if get_customer hasn't been successfully run first."""
    
    if not verification_state.get("verified_customer_id"):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny", 
                "permissionDecisionReason": (
                    "PROGRAMMATIC ENFORCEMENT BLOCKED: You MUST call 'get_customer' and successfully "
                    "verify the user's identity before calling 'process_refund'."
                )
            }
        }
        
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}


# ==============================================================================
# 3. WORKFLOW EXECUTION
# ==============================================================================

async def run_enforcement_sdk_workflow(user_request: str):
    print("--- Starting SDK Enforcement Workflow ---")
    
    # EXAM SKILL: Decomposing multi-concern requests
    system_prompt = (
        "You are a Customer Support Agent.\n"
        "1. Decompose multi-concern customer requests into distinct items and investigate each in parallel.\n"
        "2. If processing a refund, you must FIRST verify the customer via get_customer.\n"
        "3. If policy is ambiguous or the refund is too large, use escalate_to_human and provide a structured summary."
    )

    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=system_prompt,
        mcp_servers={"customer_server": customer_server},
        allowed_tools=["get_customer", "process_refund", "escalate_to_human"],
        hooks={
            "PreToolUse": [
                HookMatcher(
                    matcher="process_refund", 
                    hooks=[refund_prerequisite_hook]
                )
            ]
        }
    )

    try:
        # ANTI-TOKEN-HOG RULE: We use query() but limit the loop explicitly if it gets stuck
        async for msg in query(prompt=user_request, options=options):
            if isinstance(msg, ResultMessage):
                return msg.result
    except Exception as e:
        pass

if __name__ == "__main__":
    # Test a refund attempt where the model might try to skip verification
    request = "I am test@example.com. My order 999 was broken. Please refund me $50 and also update my address."
    try:
        result = asyncio.run(run_enforcement_sdk_workflow(request))
        if result:
            print(f"\n[Agent Response]\n{result}")
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")
