"""
Task Statement 1.7: Manage session state, resumption, and forking
(SDK VERSION)

Knowledge of:
- How session state is persisted across interruptions.
- The differences between resuming a session vs forking a session for divergent exploration.

Skills in:
- Using structured summaries vs stale tool results when resuming sessions.
- Implementing session resumption and fork_session architectures.
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
# STATE STORAGE MOCK
# ==============================================================================
# In production, this would be Redis, Postgres, etc.
SESSION_DB = {}

def save_session(session_id: str, context: str):
    SESSION_DB[session_id] = context
    
def load_session(session_id: str) -> str:
    return SESSION_DB.get(session_id, "")


# ==============================================================================
# SDK IMPLEMENTATION
# ==============================================================================

async def run_session_sdk(session_id: str, user_request: str, fork_from: str = None):
    print(f"\n--- Starting SDK Session: {session_id} ---")
    
    # EXAM SKILL: Forking a session vs Resuming a session
    if fork_from and fork_from in SESSION_DB:
        print(f"Forking session from {fork_from}...")
        # Create a deep copy or explicitly load the parent state
        previous_context = load_session(fork_from)
        system_prompt = f"You are continuing a forked conversation. Previous Context:\n{previous_context}"
    else:
        # Standard resumption
        previous_context = load_session(session_id)
        if previous_context:
            print(f"Resuming existing session {session_id}...")
            # EXAM SKILL: Using structured summaries vs stale tool results
            # Instead of reloading 50 raw tool_use messages (which pollutes context),
            # we inject the structured summary of the previous state.
            system_prompt = f"You are resuming a conversation. Here is the structured summary of what happened previously:\n{previous_context}"
        else:
            print(f"Starting new session {session_id}...")
            system_prompt = "You are a helpful assistant."

    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=system_prompt
    )

    try:
        final_output = None
        async for msg in query(prompt=user_request, options=options):
            if isinstance(msg, ResultMessage):
                final_output = msg.result
                
        # Simulate generating a structured summary of the turn to save back to DB
        # In reality, you might prompt the LLM to summarize the conversation before saving.
        new_summary = f"{previous_context}\n- User asked: {user_request}\n- Agent concluded: {final_output}"
        save_session(session_id, new_summary)
        
        return final_output
    except Exception as e:
        # Catch expected dummy key errors
        save_session(session_id, f"{previous_context}\n- [MOCK SAVE DUE TO ERROR]")
        return "[Mock Response]"

if __name__ == "__main__":
    try:
        # 1. Start a new session
        asyncio.run(run_session_sdk("session_A", "I am planning a trip to Japan."))
        
        # 2. Resume that session
        asyncio.run(run_session_sdk("session_A", "What is the best month to visit?"))
        
        # 3. Fork the session to explore a divergent path
        asyncio.run(run_session_sdk("session_B_fork", "Actually, what if I went to Italy instead?", fork_from="session_A"))
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")
