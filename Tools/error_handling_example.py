"""
Tool Error Handling

Shows basic patterns for handling errors when a model attempts to call a tool
incorrectly or the tool fails. It introduces the concept of feeding the
exception string back to the model as a `tool_result`.
"""

import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"


# Load environment variables (API Key)
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

# =====================================================================
# 1. API Level (Transient) Errors & Exponential Backoff
# =====================================================================
# The Anthropic SDK automatically handles transient errors like 
# RateLimitError and APIConnectionError using exponential backoff.
# We can configure this via the `max_retries` argument (default is 2).
client = Anthropic(max_retries=5)


# =====================================================================
# Tool Definition
# =====================================================================
transfer_funds_tool = {
    "name": "transfer_funds",
    "description": "Transfers funds. If it fails with a business rule violation, YOU MUST try again with the maximum allowed amount.",
    "input_schema": {
        "type": "object",
        "properties": {
            "amount": {
                "type": "integer",
                "description": "The amount in USD to transfer."
            }
        },
        "required": ["amount"]
    }
}

def mock_transfer_funds(amount: int):
    """A mock local function that enforces a business rule."""
    print(f"  [LOCAL EXECUTION] 💸 Attempting to transfer ${amount}...")
    
    # Simulate a business rule violation
    if amount > 100:
        return {"success": False, "error_message": "Business Rule Violation: Maximum transfer amount is $100."}
    
    return {"success": True, "message": f"Successfully transferred ${amount}."}

# =====================================================================
# 2. Tool Level Errors & Self-Correction Demonstration
# =====================================================================
def run_error_handling_example():
    print("=" * 80)
    print("🛡️ RUNNING ERROR HANDLING & SELF-CORRECTION EXAMPLE")
    print("=" * 80)

    # 1. Initial Prompt (Asking for $500 transfer)
    messages = [{"role": "user", "content": "Please transfer $500 for me to my savings account immediately. I authorize this transaction."}]
    print("User: 'Please transfer $500 for me to my savings account immediately. I authorize this transaction.'\n")

    # 2. First API Call
    print(">>> 1. Sending first API call (Claude attempts to transfer $500)...")
    response_1 = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=1024,
        tools=[transfer_funds_tool],
        messages=messages
    )

    if response_1.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": response_1.content})
        tool_use_block = next(block for block in response_1.content if block.type == "tool_use")
        amount = tool_use_block.input["amount"]
        
        # 3. Execute tool and hit business rule failure
        tool_output = mock_transfer_funds(amount)
        
        if not tool_output["success"]:
            print(f"  ❌ Tool Failed! Error: {tool_output['error_message']}")
            
            # =====================================================================
            # CRITICAL ARCHITECT PATTERN: Return is_error=True
            # =====================================================================
            # We don't crash our app. We package the error and return it to Claude.
            print("\n>>> 2. Packaging the error with `is_error=True` and returning to Claude...")
            
            tool_result_message = {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": tool_output["error_message"],
                        "is_error": True # <--- THIS IS THE MAGIC FLAG
                    }
                ]
            }
            messages.append(tool_result_message)

            # 4. Second API Call (Claude self-corrects)
            print(">>> 3. Sending second API call (Claude reads the error and tries to fix it)...")
            response_2 = client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=1024,
                tools=[transfer_funds_tool],
                messages=messages
            )
            
            # Check if Claude tried to call the tool again with a fixed amount
            if response_2.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response_2.content})
                new_tool_use_block = next(block for block in response_2.content if block.type == "tool_use")
                new_amount = new_tool_use_block.input["amount"]
                
                print(f"  ✅ Claude Self-Corrected! New requested amount: ${new_amount}")
                
                # Execute tool successfully
                final_output = mock_transfer_funds(new_amount)
                if final_output["success"]:
                    print(f"  🎉 {final_output['message']}")

if __name__ == "__main__":
    run_error_handling_example()
