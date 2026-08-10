import os
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
update_facts_tool = {
    "name": "update_persistent_facts",
    "description": "Updates the persistent case-facts block with critical numeric or identifying details.",
    "input_schema": {
        "type": "object",
        "properties": {
            "order_number": {"type": "string"},
            "refund_amount": {"type": "number"},
            "deadline": {"type": "string"}
        },
        "required": []
    }
}

# =====================================================================
# Memory Architecture Simulation
# =====================================================================
def run_memory_example():
    print("=" * 80)
    print("🧠 RUNNING PERSISTENT CASE-FACTS MEMORY EXAMPLE")
    print("=" * 80)

    # State Definition
    persistent_facts = {}
    
    # ---------------------------------------------------------
    # TURN 1: Extraction Phase
    # ---------------------------------------------------------
    print("\n--- TURN 1: EXTRACTION ---")
    user_message_1 = "Hi, my order number is ORD-998877. I need a refund of $214.88 by the 15th."
    print(f"User: '{user_message_1}'")
    
    # We instruct the model to use the tool if it sees critical billing data
    system_prompt = "You are a billing support agent. If the user provides an order number, refund amount, or deadline, YOU MUST use the update_persistent_facts tool to save it."
    
    response_1 = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        system=system_prompt,
        tools=[update_facts_tool],
        messages=[{"role": "user", "content": user_message_1}]
    )

    if response_1.stop_reason == "tool_use":
        tool_use = next(block for block in response_1.content if block.type == "tool_use")
        persistent_facts.update(tool_use.input)
        print(f"✅ Claude extracted facts: {json.dumps(persistent_facts, indent=2)}")
        
    # ---------------------------------------------------------
    # TURN 2: The "Compression/Summarization" Phase
    # ---------------------------------------------------------
    print("\n--- TURN 2: CHAT LOG COMPRESSION ---")
    print("Simulating a long chat history being summarized to save context window...")
    
    # We deliberately create a summary that LOSES the exact numeric data.
    # This is the exact failure mode described in the certification question.
    summarized_chat_log = "The customer wants a refund soon and mentioned an order from last month."
    
    print(f"❌ Summarized Chat Log (Narrative Data Lost):\n   '{summarized_chat_log}'")

    # ---------------------------------------------------------
    # TURN 3: Retrieval Phase (Injecting Persistent Facts)
    # ---------------------------------------------------------
    print("\n--- TURN 3: RESOLUTION ---")
    user_message_3 = "Can you confirm the exact amount of the refund and the order number we are processing?"
    print(f"User: '{user_message_3}'")

    # ARCHITECTURAL PATTERN: We inject the persistent_facts block directly into the system prompt!
    robust_system_prompt = f"""You are a billing support agent.
    
<case_facts>
{json.dumps(persistent_facts, indent=2)}
</case_facts>

Base your response on the case facts provided above.
"""

    messages = [
        {"role": "user", "content": "Here is the summary of our previous chat: " + summarized_chat_log},
        {"role": "assistant", "content": "Got it. How can I help you now?"},
        {"role": "user", "content": user_message_3}
    ]

    response_3 = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        system=robust_system_prompt,
        messages=messages
    )

    print("\n✅ Claude's Final Response:")
    print("-" * 40)
    print(response_3.content[0].text)
    print("-" * 40)
    print("\nCONCLUSION: Even though the chat narrative was summarized and lost the numbers, the persistent block saved the context!")

if __name__ == "__main__":
    run_memory_example()
