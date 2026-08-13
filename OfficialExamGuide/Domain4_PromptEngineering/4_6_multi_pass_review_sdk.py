"""
Task Statement 4.6: Design multi-instance and multi-pass review architectures
(SDK VERSION)

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
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, query, ResultMessage

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


# ==============================================================================
# APPROACH A: MULTI-INSTANCE (PARALLEL ENSEMBLE)
# Best for: Reducing variance, brainstorming, finding consensus.
# ==============================================================================

async def run_parallel_ensemble_sdk(prompt: str):
    print("\n--- Starting SDK Parallel Ensemble ---")
    
    options = ClaudeAgentOptions(model=DEFAULT_MODEL, system_prompt="You are a creative brainstorming agent.")
    
    async def fetch_idea():
        try:
            async for msg in query(prompt=prompt, options=options):
                if isinstance(msg, ResultMessage): return msg.result
        except Exception:
            return "Mock Idea"
            
    # EXAM SKILL: Using asyncio.gather for parallel multi-instance execution
    # ANTI-TOKEN-HOG: Limit to 2 parallel tasks
    print("Spawning 2 parallel instances...")
    results = await asyncio.gather(*[fetch_idea() for _ in range(2)])
    
    # In a real architecture, you would pass these results to a final "Aggregator" agent.
    print("\nAggregated Results:")
    for idx, res in enumerate(results):
        print(f"Instance {idx+1}: {res[:50]}...")
        
    return results


# ==============================================================================
# APPROACH B: MULTI-PASS REVIEW (SEQUENTIAL)
# Best for: High-stakes translation, complex code generation, critique.
# ==============================================================================

async def run_sequential_review_sdk(draft_text: str):
    print("\n--- Starting SDK Sequential Multi-Pass Review ---")
    
    # Pass 1: The Drafter
    print("Pass 1: Drafting...")
    drafter_opts = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt="You are a translator. Translate the text to French."
    )
    draft = None
    try:
        async for msg in query(prompt=draft_text, options=drafter_opts):
            if isinstance(msg, ResultMessage): draft = msg.result
    except Exception:
        draft = "Mock French Draft"
            
    # Pass 2: The Reviewer (Critiques the draft)
    print("Pass 2: Reviewing...")
    reviewer_opts = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt="You are a native French speaker. Critique this translation and provide a corrected version."
    )
    final_version = None
    try:
        async for msg in query(prompt=draft, options=reviewer_opts):
            if isinstance(msg, ResultMessage): final_version = msg.result
    except Exception:
        final_version = "Mock Corrected Translation"
            
    return final_version

# ==============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(run_parallel_ensemble_sdk("Give me a name for a new pet dog."))
        asyncio.run(run_sequential_review_sdk("The quick brown fox jumps over the lazy dog."))
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")
