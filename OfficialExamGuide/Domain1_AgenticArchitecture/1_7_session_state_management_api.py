"""
Task Statement 1.7: Manage session state, resumption, and forking
(API VERSION)

This file demonstrates how to build the identical patterns tested in 1.7 using 
deterministic, code-first Python architecture instead of relying on the SDK.

Knowledge of:
- How session state is persisted across interruptions.
- The differences between resuming a session vs forking a session for divergent exploration.

Skills in:
- Using structured summaries vs stale tool results when resuming sessions.
- Implementing named session resumption and fork_session.
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
# STATE STORAGE MOCK (Database)
# ==============================================================================
# In production, this would be a database storing a structured summary of the session.
# Storing summaries rather than the raw messages array prevents context pollution.
SESSION_DB = {}

def save_session(session_id: str, context: str):
    SESSION_DB[session_id] = context
    
def load_session(session_id: str) -> str:
    return SESSION_DB.get(session_id, "")


# ==============================================================================
# DETERMINISTIC ORCHESTRATOR
# ==============================================================================

async def run_session_api(session_id: str, user_request: str, fork_from: str = None):
    print(f"\n--- Starting API Session: {session_id} ---")
    
    # EXAM SKILL: Forking a session vs Resuming a session
    if fork_from and fork_from in SESSION_DB:
        print(f"Forking session from {fork_from}...")
        # Deep copy or explicit load of the parent state
        previous_context = load_session(fork_from)
        system_prompt = f"You are continuing a forked conversation. Previous Context:\n{previous_context}"
    else:
        # Standard resumption
        previous_context = load_session(session_id)
        if previous_context:
            print(f"Resuming existing session {session_id}...")
            # EXAM SKILL: Using structured summaries vs stale tool results
            # By passing `previous_context` inside the system prompt, we avoid passing
            # stale tool_result blocks in the Messages array which degrade LLM performance.
            system_prompt = f"You are resuming a conversation. Here is the structured summary of what happened previously:\n{previous_context}"
        else:
            print(f"Starting new session {session_id}...")
            system_prompt = "You are a helpful assistant."

    try:
        response = await client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_request}]
        )
        final_output = response.content[0].text
    except Exception as e:
        # Mocking the response for when dummy_key fails
        final_output = "[Mock Response]"
        
    # Simulate generating a structured summary of the turn to save back to DB
    new_summary = f"{previous_context}\n- User asked: {user_request}\n- Agent concluded: {final_output}"
    save_session(session_id, new_summary)
        
    return final_output

if __name__ == "__main__":
    try:
        # 1. Start a new session
        asyncio.run(run_session_api("session_A", "I am planning a trip to Japan."))
        
        # 2. Resume that session
        asyncio.run(run_session_api("session_A", "What is the best month to visit?"))
        
        # 3. Fork the session to explore a divergent path
        asyncio.run(run_session_api("session_B_fork", "Actually, what if I went to Italy instead?", fork_from="session_A"))
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed: {e}")
