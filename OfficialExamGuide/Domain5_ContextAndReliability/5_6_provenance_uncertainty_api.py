"""
Task Statement 5.6: Preserve information provenance and handle uncertainty
(API VERSION)

This file demonstrates how to build the identical patterns tested in 5.6 using 
deterministic, code-first Python architecture instead of relying on the SDK.

Knowledge of:
- How to instruct an LLM to cite its sources when generating an answer (provenance).
- Handling contradictions across sources by acknowledging the uncertainty.

Skills in:
- Prompting strategies that enforce strict source citation.
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
# EXAM SKILL: Provenance & Uncertainty
# ==============================================================================

SYSTEM_PROMPT = """
You are a research analyst. Answer the user's question based ONLY on the provided documents.

RULES:
1. PROVENANCE: Every claim you make MUST be followed by a citation in brackets referencing the document ID (e.g. [Doc A]).
2. UNCERTAINTY: If the documents contradict each other, DO NOT guess which one is correct. You must explicitly state that the sources conflict and cite both.
"""

async def run_provenance_api():
    print(f"\n--- Starting Deterministic API Provenance Workflow ---")
    
    # ✅ BEST PRACTICE: Use native `document` blocks with citations enabled
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "text",
                        "media_type": "text/plain",
                        "data": "The 2023 Q4 revenue was $45 Million."
                    },
                    "title": "Doc A",
                    "citations": {"enabled": True}
                },
                {
                    "type": "document",
                    "source": {
                        "type": "text",
                        "media_type": "text/plain",
                        "data": "According to the audited logs, 2023 Q4 revenue was $42 Million due to refunds."
                    },
                    "title": "Doc B",
                    "citations": {"enabled": True}
                },
                {
                    "type": "text",
                    "text": "What was the Q4 revenue?"
                }
            ]
        }
    ]
    
    try:
        response = await client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        return "[Mock Response expected if dummy key]"

if __name__ == "__main__":
    try:
        res = asyncio.run(run_provenance_api())
        print(f"\n[Agent Response (Should highlight contradiction & cite docs)]:\n{res}")
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed: {e}")
