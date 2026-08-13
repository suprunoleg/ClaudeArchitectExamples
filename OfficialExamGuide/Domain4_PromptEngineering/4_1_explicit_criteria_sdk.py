"""
Task Statement 4.1: Design prompts with explicit criteria to improve precision
(SDK VERSION)

Knowledge of:
- The difference between vague criteria ("extract negative reviews") and explicit criteria 
  ("extract reviews where the user states they will return the product or requested a refund").
- How explicit criteria reduce false positives in classification/extraction tasks.

Skills in:
- Writing a deterministic system prompt that bounds the LLM's classification logic.
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
# EXAM SKILL: Explicit vs Vague Criteria
# ==============================================================================

# ❌ ANTI-PATTERN: Vague Prompt
# This leads to false positives. A review saying "The packaging was slightly dented, 
# but the product is amazing" might get flagged as a "negative review".
BAD_PROMPT = """
You are a classifier. Read the following review and determine if it is a negative review. 
Reply with YES or NO.
"""

# ✅ BEST PRACTICE: Explicit Criteria
# This eliminates ambiguity and reduces false positives by defining EXACTLY what 
# constitutes a "critical issue".
GOOD_PROMPT = """
You are a classifier. Read the following review and determine if it contains a CRITICAL ISSUE.

A CRITICAL ISSUE is defined STRICTLY as:
1. The user states they requested a refund.
2. The user states the product arrived completely broken or unusable.
3. The user threatens legal action or regulatory reporting.

If the review contains ANY of these three criteria, reply with YES.
If the review complains about shipping speed, minor dents, or is generally annoyed BUT 
does not meet the above three criteria, reply with NO.
"""

async def run_explicit_criteria_sdk(review_text: str):
    print(f"\n--- Starting SDK Explicit Criteria Workflow ---")
    
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=GOOD_PROMPT
    )

    try:
        final_output = None
        async for msg in query(prompt=review_text, options=options):
            if isinstance(msg, ResultMessage):
                final_output = msg.result
        return final_output
    except Exception as e:
        return "[Mock Response expected if dummy key]"

if __name__ == "__main__":
    try:
        review_1 = "The box was a bit dented when it arrived, which was annoying, but I love the product!"
        print(f"Review 1: {review_1}")
        res_1 = asyncio.run(run_explicit_criteria_sdk(review_1))
        print(f"[Agent Response -> should be NO]: {res_1}")
        
        review_2 = "This is garbage. It arrived shattered into 50 pieces. I already emailed support for a refund."
        print(f"\nReview 2: {review_2}")
        res_2 = asyncio.run(run_explicit_criteria_sdk(review_2))
        print(f"[Agent Response -> should be YES]: {res_2}")
        
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")
