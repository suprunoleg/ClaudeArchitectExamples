"""
Task Statement 1.6: Design task decomposition strategies for complex workflows
(API VERSION)

This file demonstrates how to build the identical patterns tested in 1.6 using 
deterministic, code-first Python architecture instead of relying on the SDK.

Knowledge of:
- When to use prompt chaining (fixed sequence) vs dynamic decomposition (agentic routing).
- How to partition context between decomposition steps to avoid context pollution.

Skills in:
- Implementing a fixed prompt chain for highly predictable tasks (e.g. Extract -> Translate -> Summarize).
- Implementing dynamic decomposition using structured outputs to determine the sequence of operations on the fly.
"""

import os
import asyncio
import json
from typing import List, Optional
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = AsyncAnthropic()

async def call_model(system_prompt: str, user_prompt: str, tools=None) -> tuple[str, list]:
    """Helper to simulate an isolated subagent API call. Returns (text, tool_calls)."""
    try:
        kwargs = {
            "model": DEFAULT_MODEL,
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        if tools:
            kwargs["tools"] = tools
            
        response = await client.messages.create(**kwargs)
        
        text_blocks = [b.text for b in response.content if b.type == 'text']
        tool_blocks = [b for b in response.content if b.type == 'tool_use']
        
        return "\n".join(text_blocks), tool_blocks
    except Exception as e:
        print(f"[Mock API Response - expected if dummy key] {e}")
        return "", []

# ==============================================================================
# APPROACH A: FIXED PROMPT CHAINING
# ==============================================================================

async def run_fixed_chain_api(raw_document: str):
    print("\n--- Starting Deterministic API Fixed Prompt Chain ---")
    
    # EXAM SKILL: Partitioning context explicitly in Python code.
    
    # Step 1: Extract
    print("Step 1: Extracting...")
    sys_ext = "You are an Extractor. Extract only the action items from the text. Return bullet points."
    extracted, _ = await call_model(sys_ext, raw_document)
            
    # Step 2: Translate (Only receives the output of Step 1)
    print("Step 2: Translating...")
    sys_trans = "You are a Translator. Translate the following action items into Spanish."
    translated, _ = await call_model(sys_trans, extracted)
            
    return translated


# ==============================================================================
# APPROACH B: DYNAMIC DECOMPOSITION
# ==============================================================================

# EXAM SKILL: Using structured outputs to determine the sequence of operations on the fly
# Instead of Pydantic + SDK, we use the raw ToolUse API.
PLANNER_TOOL = {
    "name": "generate_plan",
    "description": "Output the sequence of steps required to solve the user's request.",
    "input_schema": {
        "type": "object",
        "properties": {
            "steps": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The sequential steps required to solve the user's request."
            }
        },
        "required": ["steps"]
    }
}

async def run_dynamic_decomposition_api(user_request: str):
    print("\n--- Starting Deterministic API Dynamic Decomposition ---")
    
    print("Step 1: Dynamically planning the workflow...")
    
    sys_plan = "You are a Planner. Break the user's request into a logical sequence of steps. You MUST use the generate_plan tool."
    
    # We call the model and force it to use our structured output tool
    _, tools_used = await call_model(sys_plan, user_request, tools=[PLANNER_TOOL])
    
    if not tools_used or tools_used[0].name != "generate_plan":
        return "Failed to generate plan."
        
    generated_steps = tools_used[0].input.get("steps", [])
    print(f"Generated Plan: {generated_steps}")
    
    # ANTI-TOKEN-HOG RULE: Limit dynamic loops
    safe_steps = generated_steps[:2]
    print(f"Executing first {len(safe_steps)} steps to conserve tokens...")
    
    context_accumulator = ""
    for idx, step in enumerate(safe_steps):
        print(f"Executing Step {idx+1}: {step}")
        sys_exec = "Execute the current step given the context of previous steps."
        step_prompt = f"Previous Context:\n{context_accumulator}\n\nCurrent Step to Execute: {step}"
        
        step_result, _ = await call_model(sys_exec, step_prompt)
        context_accumulator += f"\nResult of {step}:\n{step_result}\n"
                
    return context_accumulator

# ==============================================================================

if __name__ == "__main__":
    try:
        doc = "Meeting notes: John needs to fix the server by Tuesday. Sarah will email the client."
        res_fixed = asyncio.run(run_fixed_chain_api(doc))
        print(f"\n[Fixed Chain Result]\n{res_fixed}")
        
        req = "I need to know the capital of France, and then I need a poem about that city's most famous landmark."
        res_dynamic = asyncio.run(run_dynamic_decomposition_api(req))
        print(f"\n[Dynamic Result]\n{res_dynamic}")
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed: {e}")
