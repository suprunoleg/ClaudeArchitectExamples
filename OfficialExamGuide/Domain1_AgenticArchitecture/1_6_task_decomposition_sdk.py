"""
Task Statement 1.6: Design task decomposition strategies for complex workflows
(SDK VERSION)

Knowledge of:
- When to use prompt chaining (fixed sequence) vs dynamic decomposition (agentic routing).
- How to partition context between decomposition steps to avoid context pollution.

Skills in:
- Implementing a fixed prompt chain for highly predictable tasks (e.g. Extract -> Translate -> Summarize).
- Implementing dynamic decomposition using structured outputs to determine the sequence of operations on the fly.
"""

import os
import asyncio
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, query, ResultMessage

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


# ==============================================================================
# APPROACH A: FIXED PROMPT CHAINING
# Best for: Highly predictable, linear tasks (e.g. ETL pipelines)
# ==============================================================================

async def run_fixed_chain_sdk(raw_document: str):
    extract_opts = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt="You are an Extractor. Extract only the action items from the text. Return bullet points."
    )
    extracted = None
    async for msg in query(prompt=raw_document, options=extract_opts):
        if isinstance(msg, ResultMessage): extracted = msg.result
            
    translate_opts = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt="You are a Translator. Translate the following action items into Spanish."
    )
    translated = None
    async for msg in query(prompt=extracted or "", options=translate_opts):
        if isinstance(msg, ResultMessage): translated = msg.result
            
    return translated


# ==============================================================================
# APPROACH B: DYNAMIC DECOMPOSITION
# Best for: Ambiguous user requests that require on-the-fly planning
# ==============================================================================

class DecompositionPlan(BaseModel):
    steps: List[str] = Field(description="The sequential steps required to solve the user's request.")
    requires_search: bool = Field(description="Whether web search is required for any step.")

async def run_dynamic_decomposition_sdk(user_request: str):
    planner_opts = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt="You are a Planner. Break the user's request into a logical sequence of steps.",
        response_schema=DecompositionPlan
    )
    
    plan: Optional[DecompositionPlan] = None
    async for msg in query(prompt=user_request, options=planner_opts):
        if isinstance(msg, ResultMessage): plan = msg.result
            
    if not plan: return "Failed to generate plan."
    
    # ANTI-TOKEN-HOG RULE: Limit dynamic loops
    safe_steps = plan.steps[:2]
    
    # Step 2: Execution Engine
    # Notice we pass the context of previous steps into the next step dynamically
    context_accumulator = ""
    for idx, step in enumerate(safe_steps):
        executor_opts = ClaudeAgentOptions(
            model=DEFAULT_MODEL,
            system_prompt="Execute the current step given the context of previous steps."
        )
        
        step_prompt = f"Previous Context:\n{context_accumulator}\n\nCurrent Step to Execute: {step}"
        
        async for msg in query(prompt=step_prompt, options=executor_opts):
            if isinstance(msg, ResultMessage):
                context_accumulator += f"\nResult of {step}:\n{msg.result}\n"
                
    return context_accumulator

# ==============================================================================

if __name__ == "__main__":
    # Run Fixed Chain
    doc = "Meeting notes: John needs to fix the server by Tuesday. Sarah will email the client."
    res_fixed = asyncio.run(run_fixed_chain_sdk(doc))
    
    # Run Dynamic
    req = "I need to know the capital of France, and then I need a poem about that city's most famous landmark."
    res_dynamic = asyncio.run(run_dynamic_decomposition_sdk(req))
