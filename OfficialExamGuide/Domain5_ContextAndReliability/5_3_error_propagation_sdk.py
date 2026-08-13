"""
Task Statement 5.3: Implement error propagation strategies across multi-agent systems
(SDK VERSION)

Knowledge of:
- How errors from a subagent bubble up to a coordinator agent.
- How the coordinator can catch the error and decide whether to retry or fail.

Skills in:
- Using `try/except` around subagent invocations.
- Exposing subagent failure reasons to the coordinator.
"""

import os
import asyncio
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, AgentDefinition, Task, query, ResultMessage

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


# ==============================================================================
# ==============================================================================

async def failing_subagent_logic(args):
    raise ConnectionError("Database timed out while searching.")

failing_subagent = AgentDefinition(
    description="Searches the database. Might fail.",
    instructions="Search the DB.",
    tools=[]
)

async def run_error_propagation_sdk(user_request: str):
    
    # the entire coordinator crashes and the user sees a raw Python stack trace.
    
    async def safe_subagent_wrapper(args):
        try:
            return await failing_subagent_logic(args)
        except Exception as e:
            # allowing the Coordinator LLM to read it and decide what to do next.
            return f"SYSTEM ERROR IN SUBAGENT: {str(e)}"
    
    subagent_tool = Task(
        name="search_db",
        description="Searches the database.",
        agent=failing_subagent,
        execute=safe_subagent_wrapper # Use the safe wrapper
    )
    
    system_prompt = (
        "You are the coordinator. You must search the database to answer the user's question. "
        "If the search tool returns a SYSTEM ERROR, tell the user the system is temporarily down, "
        "but do NOT try to guess the answer."
    )
    
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=system_prompt,
        allowed_tools=[subagent_tool]
    )

    try:
        final_output = None
        async for msg in query(prompt=user_request, options=options):
            if isinstance(msg, ResultMessage):
                final_output = msg.result
        return final_output
    except Exception as e:
        return "[Mock Response expected if dummy key]"

if __name__ == "__main__":
    req = "What is John's phone number?"
    res = asyncio.run(run_error_propagation_sdk(req))
