"""
Task Statement 4.6: Design multi-instance and multi-pass review architectures
(API VERSION)

This file demonstrates how to build the identical patterns tested in 4.6 using 
deterministic, code-first Python architecture instead of relying on the SDK.

Knowledge of:
- When to use multiple instances of a model (parallel ensemble) vs multi-pass review (sequential).
- Multi-instance reduces variance by aggregating multiple parallel responses.
- Multi-pass review allows a model to critique and refine output in sequence.

Skills in:
- Implementing an ensemble pattern using asyncio.gather.
- Implementing a sequential review pattern.
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

async def call_model(system_prompt: str, user_prompt: str) -> str:
    try:
        response = await client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return response.content[0].text
    except Exception:
        return "[Mock API Response - expected if dummy key]"

# ==============================================================================
# APPROACH A: MULTI-INSTANCE (PARALLEL ENSEMBLE)
# ==============================================================================

async def run_parallel_ensemble_api(prompt: str):
    
    sys_prompt = "You are a creative brainstorming agent."
    results = await asyncio.gather(*[call_model(sys_prompt, prompt) for _ in range(2)])
    for idx, res in enumerate(results):
        pass
        
    return results


# ==============================================================================
# APPROACH B: MULTI-PASS REVIEW (SEQUENTIAL)
# ==============================================================================

async def run_sequential_review_api(draft_text: str):
    draft = await call_model(
        system_prompt="You are a translator. Translate the text to French.", 
        user_prompt=draft_text
    )
    final_version = await call_model(
        system_prompt="You are a native French speaker. Critique this translation and provide a corrected version.",
        user_prompt=draft
    )
            
    return final_version

# ==============================================================================

if __name__ == "__main__":
    asyncio.run(run_parallel_ensemble_api("Give me a name for a new pet dog."))
    asyncio.run(run_sequential_review_api("The quick brown fox jumps over the lazy dog."))
