"""
Task Statement 5.1: Manage conversation context to preserve critical information
(API VERSION)

This file demonstrates how to build the identical patterns tested in 5.1 using 
deterministic, code-first Python architecture instead of relying on the SDK.

Knowledge of:
- The "Lost in the Middle" phenomenon (LLMs pay most attention to the start and end of context).
- How to prevent context bloat by compressing long transcripts.

Skills in:
- Implementing context compaction loops (using an LLM to summarize previous turns).
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
# ==============================================================================

async def summarize_context(long_history_array: list) -> str:
    """Uses the LLM to compress a raw message history array into a dense summary."""
    sys_prompt = "You are a summarizer. Extract only the permanent facts and final conclusions from the chat history. Discard all chit-chat, raw data, and failed tool attempts."
    
    # Convert array to a string transcript for summarization
    transcript = ""
    for msg in long_history_array:
        role = msg.get("role", "unknown")
        # Simplified for mock
        content = msg.get("content", "")
        transcript += f"{role}: {content}\n"
    
    try:
        response = await client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=300,
            system=sys_prompt,
            messages=[{"role": "user", "content": f"History:\n{transcript}"}]
        )
        return response.content[0].text
    except Exception:
        return "Mock Summary (Error)"

async def run_context_management_api():
    
    # Imagine a messages array that has grown to 50,000 tokens (50 turns)
    raw_messages_array = [
        {"role": "user", "content": "Help me build a react app."},
        {"role": "assistant", "content": "[Calls terminal tool] -> Failed: npm not found."},
        # ... 45 more turns of failing ...
        {"role": "assistant", "content": "I finally installed it correctly. The frontend is in /src/App.tsx."}
    ]
    compact_summary = await summarize_context(raw_messages_array)
    
    # Now use the compact context for the next turn, effectively resetting the messages array
    new_system_prompt = f"You are a coding assistant. Previous context: {compact_summary}"
    new_messages_array = [{"role": "user", "content": "What file should I edit to change the UI?"}]
    
    try:
        response = await client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=300,
            system=new_system_prompt,
            messages=new_messages_array
        )
        return response.content[0].text
    except Exception as e:
        return "[Mock Response expected if dummy key]"

if __name__ == "__main__":
    res = asyncio.run(run_context_management_api())
