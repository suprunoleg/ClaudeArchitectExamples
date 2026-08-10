import os
import time
import json
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

# =====================================================================
# Tool Definition
# =====================================================================
perform_action_tool = {
    "name": "perform_action",
    "description": "Performs a system action. Sometimes fails.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action_type": {
                "type": "string",
                "enum": ["transient", "invalid_input", "business_rule", "permission"],
                "description": "The type of action to simulate."
            },
            "retry_count": {
                "type": "integer",
                "description": "Used internally by the LLM to track its retries. Starts at 0."
            }
        },
        "required": ["action_type"]
    }
}

# Custom Exceptions for Hard Failures
class BusinessRuleException(Exception): pass
class PermissionException(Exception): pass

# =====================================================================
# Mock Tool Execution Logic
# =====================================================================
def execute_system_action(action_type: str, retry_count: int = 0):
    """Mocks tool execution and raises distinct failure states based on action_type."""
    print(f"    [TOOL RUN] Attempting '{action_type}' (Retry: {retry_count})...")
    
    if action_type == "transient":
        # Simulate an external API timeout.
        # The python execution wrapper handles this via programmatic exponential backoff.
        raise TimeoutError("External Database timed out.")
        
    elif action_type == "invalid_input":
        # Simulate a validation failure. We return a soft error to Claude so it self-corrects.
        if retry_count < 1:
            return {"success": False, "error_message": f"Validation Error: retry_count must be at least 1, got {retry_count}."}
        return {"success": True, "message": "Action completed successfully!"}
        
    elif action_type == "business_rule":
        # Simulate a core business rule violation. We abort the loop instantly.
        raise BusinessRuleException("Business Rule Violation: Account is frozen.")
        
    elif action_type == "permission":
        # Simulate an unauthorized action. We abort the loop instantly.
        raise PermissionException("Permission Denied: You do not have admin access.")
        
    return {"success": True, "message": "Unknown action completed."}

# =====================================================================
# Agent Loop
# =====================================================================
def run_agentic_loop(scenario_name: str, initial_prompt: str, max_turns: int = 3):
    print("\n" + "=" * 80)
    print(f"🛡️ SCENARIO: {scenario_name}")
    print("=" * 80)
    print(f"Prompt: '{initial_prompt}'\n")

    messages = [{"role": "user", "content": initial_prompt}]
    turn_count = 0

    while turn_count < max_turns:
        turn_count += 1
        print(f">>> TURN {turn_count}/{max_turns}")
        
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            tools=[perform_action_tool],
            messages=messages
        )
        
        # If no tool was called, Claude is finished generating text
        if response.stop_reason != "tool_use":
            final_text = next((block.text for block in response.content if block.type == "text"), "")
            print(f"  ✅ Task Completed! Claude's Final Output: {final_text}")
            return
            
        # Claude wants to call a tool
        messages.append({"role": "assistant", "content": response.content})
        tool_use = next(block for block in response.content if block.type == "tool_use")
        
        action_type = tool_use.input.get("action_type")
        retry_count = tool_use.input.get("retry_count", 0)
        
        # We will use this flag to tell Claude if it made a mistake
        tool_is_error = False
        tool_output_string = ""
        
        try:
            # ---------------------------------------------------------
            # 1. TRANSIENT ERROR HANDLING (Exponential Backoff in Python)
            # ---------------------------------------------------------
            if action_type == "transient":
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        result = execute_system_action(action_type, retry_count)
                        break # If it succeeds, exit the retry loop
                    except TimeoutError as e:
                        if attempt == max_retries - 1:
                            print(f"  ❌ Max retries reached for transient error.")
                            # We've exhausted python retries. Tell Claude it failed permanently.
                            tool_is_error = True
                            tool_output_string = "System is down. Please tell the user we cannot complete the task."
                            break
                        backoff = 2 ** attempt
                        print(f"  ⚠️ Timeout caught! Exponential backoff... waiting {backoff}s before retry.")
                        time.sleep(backoff)
            else:
                # Normal execution
                result = execute_system_action(action_type, retry_count)
                
                # ---------------------------------------------------------
                # 2. INVALID INPUT HANDLING (Soft error -> Self-Correction)
                # ---------------------------------------------------------
                if not result.get("success"):
                    print(f"  ❌ Soft Error (Validation): {result['error_message']}")
                    tool_is_error = True
                    tool_output_string = result["error_message"]
                else:
                    print(f"  🎉 Tool Success: {result['message']}")
                    tool_output_string = json.dumps(result)
                    
        # ---------------------------------------------------------
        # 3 & 4. BUSINESS RULE / PERMISSION HANDLING (Hard Fail)
        # ---------------------------------------------------------
        except BusinessRuleException as e:
            print(f"  🚨 HARD FAIL: {str(e)}")
            print("  (Circuit Breaker Triggered: Aborting agent loop immediately without asking Claude to retry.)")
            return
        except PermissionException as e:
            print(f"  🚨 SECURITY FAIL: {str(e)}")
            print("  (Circuit Breaker Triggered: Aborting agent loop immediately without asking Claude to retry.)")
            return
            
        # Append the tool result for Claude to read on the next turn
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": tool_output_string,
                "is_error": tool_is_error
            }]
        })

    # If we exit the while loop, we hit max_turns
    print(f"\n🛑 MAX TURNS REACHED ({max_turns}). Aborting to prevent infinite loop.")

if __name__ == "__main__":
    run_agentic_loop(
        "1. TRANSIENT ERROR (Exponential Backoff)",
        "Please perform the transient action."
    )
    
    run_agentic_loop(
        "2. INVALID INPUT (Self-Correction)",
        "Please perform the invalid_input action."
    )
    
    run_agentic_loop(
        "3. BUSINESS RULE (Hard Fail)",
        "Please perform the business_rule action."
    )
    
    run_agentic_loop(
        "4. PERMISSIONS (Hard Fail)",
        "Please perform the permission action."
    )
