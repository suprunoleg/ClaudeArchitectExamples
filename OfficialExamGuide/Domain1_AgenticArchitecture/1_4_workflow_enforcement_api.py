"""
Task Statement 1.4: Implement multi-step workflows with enforcement and handoff patterns
(API VERSION)

This file demonstrates how to build the identical patterns tested in 1.4 using 
deterministic, code-first Python architecture instead of relying on the SDK's Hooks.

Knowledge of:
- The difference between programmatic enforcement (hooks, prerequisite gates) and prompt-based guidance for workflow ordering
- When deterministic compliance is required, prompt instructions alone have a non-zero failure rate
- Structured handoff protocols for mid-process escalation

Skills in:
- Implementing programmatic prerequisites that block downstream tool calls until prerequisite steps have completed
- Compiling structured handoff summaries when escalating to human agents
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
# STATE & ROUTING
# ==============================================================================

# Global state to track prerequisite completion
session_state = {"verified_customer_id": None}

def run_process_refund(order_id: str, amount: float) -> str:
    # EXAM SKILL: Implementing programmatic prerequisites that block downstream tool calls
    # In pure Python, we simply check our deterministic state before executing the logic.
    if not session_state.get("verified_customer_id"):
        return (
            "ERROR [PROGRAMMATIC ENFORCEMENT BLOCKED]: You MUST call 'get_customer' and successfully "
            "verify the user's identity before calling 'process_refund'."
        )
    return f"Successfully refunded ${amount} for order {order_id}."

def run_get_customer(email: str) -> str:
    if email == "test@example.com":
        session_state["verified_customer_id"] = "CUST-12345"
        return "Customer verified. ID: CUST-12345"
    return "Customer not found."

def run_escalate_to_human(customer_id: str, root_cause: str, refund_amount: float, recommended_action: str) -> str:
    # EXAM SKILL: Compiling structured handoff summaries
    handoff_summary = (
        f"ESCALATION HANDOFF:\n"
        f"Customer ID: {customer_id}\n"
        f"Root Cause: {root_cause}\n"
        f"Refund Amount: ${refund_amount}\n"
        f"Recommended Action: {recommended_action}"
    )
    print(f"\n[SYSTEM] Escaling to human queue:\n{handoff_summary}")
    return "Successfully escalated to human queue."

TOOLS = [
    {
        "name": "process_refund",
        "description": "Process a refund for a specific order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number"}
            },
            "required": ["order_id", "amount"]
        }
    },
    {
        "name": "get_customer",
        "description": "Lookup and verify a customer by email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string"}
            },
            "required": ["email"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate to a human agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "root_cause": {"type": "string"},
                "refund_amount": {"type": "number"},
                "recommended_action": {"type": "string"}
            },
            "required": ["customer_id", "root_cause", "refund_amount", "recommended_action"]
        }
    }
]

# ==============================================================================
# DETERMINISTIC ORCHESTRATOR
# ==============================================================================

async def run_enforcement_api_workflow(user_request: str):
    print("--- Starting Deterministic API Enforcement Workflow ---")
    
    system_prompt = (
        "You are a Customer Support Agent.\n"
        "1. Decompose multi-concern customer requests into distinct items and investigate each in parallel.\n"
        "2. If processing a refund, you must FIRST verify the customer via get_customer.\n"
        "3. If policy is ambiguous or the refund is too large, use escalate_to_human and provide a structured summary."
    )
    
    messages = [{"role": "user", "content": user_request}]
    
    # ANTI-TOKEN-HOG RULE: Limit iterations
    max_iterations = 4
    
    for i in range(max_iterations):
        print(f"\n--- Turn {i+1} ---")
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
                    
                    if block.name == "process_refund":
                        res = run_process_refund(**block.input)
                    elif block.name == "get_customer":
                        res = run_get_customer(**block.input)
                    elif block.name == "escalate_to_human":
                        res = run_escalate_to_human(**block.input)
                    else:
                        res = f"Unknown tool {block.name}"
                        
                    print(f"[Tool Result] {res}")
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
    request = "I am test@example.com. My order 999 was broken. Please refund me $50 and also update my address."
    try:
        result = asyncio.run(run_enforcement_api_workflow(request))
        print(f"\n[Agent Response]\n{result}")
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed: {e}")
