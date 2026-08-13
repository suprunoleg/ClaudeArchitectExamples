"""
Task Statement 5.1: Manage conversation context to preserve critical information
(SDK VERSION)

Knowledge of:
- The "Lost in the Middle" phenomenon (LLMs pay most attention to the start and end of context).
- How to prevent context bloat by compressing long transcripts.

Skills in:
- Implementing context compaction loops (using an LLM to summarize previous turns).
"""

import os
import asyncio
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, query, ResultMessage

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


# ==============================================================================
# ==============================================================================

async def summarize_context(long_history: str) -> str:
    """Uses an LLM to compress a long chat history into a dense summary."""
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt="You are a summarizer. Extract only the permanent facts and final conclusions from the chat history. Discard all chit-chat, raw data, and failed tool attempts."
    )
    
    try:
        final_output = None
        async for msg in query(prompt=f"History:\n{long_history}", options=options):
            if isinstance(msg, ResultMessage):
                final_output = msg.result
        return final_output or "Mock Summary"
    except Exception:
        return "Mock Summary (Error)"

async def run_context_management_sdk():
    
    # Imagine a chat array that has grown to 50,000 tokens (50 turns)
    mock_long_history = (
        "User: Help me build a react app.\n"
        "Agent: [Calls terminal tool] -> Failed: npm not found.\n"
        "Agent: [Calls terminal tool] -> Failed: syntax error.\n"
        # ... 45 more turns of failing ...
        "Agent: I finally installed it correctly. The frontend is in /src/App.tsx."
    )
    compact_summary = await summarize_context(mock_long_history)
    
    # Now use the compact context for the next turn
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=f"You are a coding assistant. Previous context: {compact_summary}"
    )
    
    try:
        res = None
        async for msg in query(prompt="What file should I edit to change the UI?", options=options):
            if isinstance(msg, ResultMessage):
                res = msg.result
        return res
    except Exception as e:
        return "[Mock Response expected if dummy key]"

if __name__ == "__main__":
    res = asyncio.run(run_context_management_sdk())
