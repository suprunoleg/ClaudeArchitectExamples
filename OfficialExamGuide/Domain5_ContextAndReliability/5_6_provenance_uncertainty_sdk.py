"""
Task Statement 5.6: Preserve information provenance and handle uncertainty
(SDK VERSION)

Knowledge of:
- How to instruct an LLM to cite its sources when generating an answer (provenance).
- Handling contradictions across sources by acknowledging the uncertainty.

Skills in:
- Prompting strategies that enforce strict source citation.
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
# EXAM SKILL: Provenance & Uncertainty
# ==============================================================================

# ❌ ANTI-PATTERN: Vague instructions
# "Answer the user's question based on these docs." -> The LLM will blend the docs, 
# and if they contradict, it will likely hallucinate a compromise or pick one arbitrarily.

# ✅ BEST PRACTICE: Enforce Citations and Explicit Uncertainty
SYSTEM_PROMPT = """
You are a research analyst. Answer the user's question based ONLY on the provided documents.

RULES:
1. PROVENANCE: Every claim you make MUST be followed by a citation in brackets referencing the document ID (e.g. [Doc A]).
2. UNCERTAINTY: If the documents contradict each other, DO NOT guess which one is correct. You must explicitly state that the sources conflict and cite both.
"""

async def run_provenance_sdk():
    print(f"\n--- Starting SDK Provenance Workflow ---")
    
    mock_documents = (
        "[Doc A] The 2023 Q4 revenue was $45 Million.\n"
        "[Doc B] According to the audited logs, 2023 Q4 revenue was $42 Million due to refunds."
    )
    
    user_request = f"What was the Q4 revenue?\n\n<docs>\n{mock_documents}\n</docs>"
    
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=SYSTEM_PROMPT
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
    try:
        res = asyncio.run(run_provenance_sdk())
        print(f"\n[Agent Response (Should highlight contradiction & cite docs)]:\n{res}")
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")
