"""
Task Statement 2.3: Distribute tools appropriately across agents and configure tool choice
(API VERSION)

This file demonstrates how to build the identical patterns tested in 2.3 using 
deterministic, code-first Python architecture instead of relying on the SDK.

Knowledge of:
- The principle of least privilege (only giving agents the tools they need).
- How tool_choice ("auto", "any", "tool") forces or restricts LLM behavior.

Skills in:
- Configuring tool_choice to force a specific tool execution.
- Creating highly bounded subagents that only have access to 1-2 specific tools.
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
# TOOLS
# ==============================================================================

TOOL_WEB_SEARCH = {
    "name": "web_search",
    "description": "Search the web for information.",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"]
    }
}

TOOL_WRITE_FILE = {
    "name": "write_file",
    "description": "Write content to a file.",
    "input_schema": {
        "type": "object",
        "properties": {"filepath": {"type": "string"}, "content": {"type": "string"}},
        "required": ["filepath", "content"]
    }
}

TOOL_SUBMIT_REPORT = {
    "name": "submit_final_report",
    "description": "Submit the final report to the user.",
    "input_schema": {
        "type": "object",
        "properties": {"report_text": {"type": "string"}},
        "required": ["report_text"]
    }
}

# ==============================================================================
# WORKFLOW
# ==============================================================================

async def run_tool_distribution_api(user_request: str):
    print("\n--- Starting Deterministic API Tool Distribution Workflow ---")
    
    # --------------------------------------------------------------------------
    # SUBAGENT (Researcher)
    # EXAM SKILL: Principle of Least Privilege
    # --------------------------------------------------------------------------
    print("\n[Phase 1] Calling Researcher Subagent...")
    try:
        research_response = await client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1000,
            system="You are a researcher. Use the web_search tool to find information.",
            messages=[{"role": "user", "content": user_request}],
            # We ONLY provide web_search. If we provided write_file, a hallucination 
            # could overwrite critical system files.
            tools=[TOOL_WEB_SEARCH],
            # Default is "auto", letting Claude decide if it needs to search
            tool_choice={"type": "auto"} 
        )
        print("Researcher successfully bounded to only web_search.")
    except Exception as e:
        print(f"[API Error - expected if dummy key] {e}")
        research_response = None
        
    # --------------------------------------------------------------------------
    # COORDINATOR (Forcing a Tool)
    # EXAM SKILL: Configuring tool_choice to force specific tool execution
    # --------------------------------------------------------------------------
    print("\n[Phase 2] Forcing Coordinator to submit report...")
    try:
        report_response = await client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1000,
            system="You are the Coordinator. You MUST submit the report using the tool.",
            messages=[{"role": "user", "content": f"Compile this into a report: 'Quantum computing is fast.'"}],
            tools=[TOOL_SUBMIT_REPORT, TOOL_WRITE_FILE],
            # EXAM SKILL: Forcing a specific tool
            # {"type": "any"} forces the model to use ANY tool before responding.
            # {"type": "tool", "name": "..."} forces the model to use THAT EXACT tool.
            tool_choice={"type": "tool", "name": "submit_final_report"}
        )
        
        # Verify it worked
        if report_response.stop_reason == "tool_use":
            tool_block = next((b for b in report_response.content if b.type == 'tool_use'), None)
            if tool_block:
                print(f"Coordinator successfully forced to use: {tool_block.name}")
                return "Workflow Complete."
    except Exception as e:
        print(f"[API Error - expected if dummy key] {e}")
        
    return "Workflow complete (simulated)."

if __name__ == "__main__":
    req = "Research Quantum Computing and submit a report."
    asyncio.run(run_tool_distribution_api(req))
