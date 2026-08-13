"""
Task Statement 4.1: Design prompts with explicit criteria to improve precision
(API VERSION)

This file demonstrates how to build the identical patterns tested in 4.1 using 
deterministic, code-first Python architecture instead of relying on the SDK.

Knowledge of:
- The difference between vague criteria and explicit criteria.
- How explicit criteria reduce false positives in classification/extraction tasks.

Skills in:
- Writing a deterministic system prompt that bounds the LLM's classification logic.
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
# EXAM SKILL: Explicit vs Vague Criteria
# ==============================================================================

GOOD_PROMPT = """
You are a classifier. Read the following review and determine if it contains a CRITICAL ISSUE.

A CRITICAL ISSUE is defined STRICTLY as:
1. The user states they requested a refund.
2. The user states the product arrived completely broken or unusable.
3. The user threatens legal action or regulatory reporting.

If the review contains ANY of these three criteria, reply with YES.
If the review complains about shipping speed, minor dents, or is generally annoyed BUT 
does not meet the above three criteria, reply with NO.

ONLY output YES or NO. Do not explain your reasoning.
"""

async def run_explicit_criteria_api(review_text: str):
    print(f"\n--- Starting Deterministic API Explicit Criteria Workflow ---")
    
    try:
        response = await client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=10,
            system=GOOD_PROMPT,
            messages=[{"role": "user", "content": review_text}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return "[Mock Response expected if dummy key]"

if __name__ == "__main__":
    try:
        review_1 = "The box was a bit dented when it arrived, which was annoying, but I love the product!"
        print(f"Review 1: {review_1}")
        res_1 = asyncio.run(run_explicit_criteria_api(review_1))
        print(f"[Agent Response -> should be NO]: {res_1}")
        
        review_2 = "This is garbage. It arrived shattered into 50 pieces. I already emailed support for a refund."
        print(f"\nReview 2: {review_2}")
        res_2 = asyncio.run(run_explicit_criteria_api(review_2))
        print(f"[Agent Response -> should be YES]: {res_2}")
        
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed: {e}")
