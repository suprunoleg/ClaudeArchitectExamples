"""
Task Statement 1.3: Configure subagent invocation, context passing, and spawning
(API VERSION)

This file demonstrates how to build the identical patterns tested in 1.3 using 
deterministic, code-first Python architecture instead of relying on the SDK's
prompt-driven Task tool.

Knowledge of:
- That subagent context must be explicitly provided in the prompt—subagents do not automatically inherit parent context
- Fork-based session management for exploring divergent approaches (simulated via parallel async calls with shared baselines)

Skills in:
- Including complete findings from prior agents directly in the subagent's prompt
- Using structured data formats to separate content from metadata when passing context
- Spawning parallel subagents deterministically using asyncio.gather rather than prompt-driven tool calls
"""

import os
import asyncio
from typing import List, Optional
from pydantic import BaseModel, Field
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
# STRUCTURED DATA FORMATS (Context Passing)
# ==============================================================================

class SearchFinding(BaseModel):
    subtopic: str = Field(description="The specific subtopic researched.")
    metadata: str = Field(description="Source information (e.g. Wikipedia).")
    content: str = Field(description="The raw factual findings.")

class SynthesisRequest(BaseModel):
    original_goal: str = Field(description="The overarching research goal.")
    findings: List[SearchFinding] = Field(description="The array of findings from parallel subagents.")

# ==============================================================================
# RAW API ORCHESTRATOR
# ==============================================================================

async def call_model(system_prompt: str, user_prompt: str) -> str:
    """Helper to simulate an isolated subagent API call."""
    # history array here. The subagent only knows exactly what is passed in `user_prompt`.
    try:
        response = await client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        return response.content[0].text
    except Exception as e:
        # Mock catch for dummy key
        return f"[Mock API Response] Data for: {user_prompt[:20]}..."

async def run_spawning_api_workflow(user_request: str):
    
    searcher_prompt = "You are the Searcher subagent. Extract raw facts only. Return your output as a short summary."
    synthesizer_prompt = "You are the Synthesizer. You will receive structured data containing findings. Synthesize them into a cohesive summary."
    
    # In a real app, this list would be generated dynamically by a routing decision (like in 1.2)
    subtopics = ["Apollo 11", "Voyager 1"]
    
    # Instead of hoping the model emits multiple "Task" tool calls simultaneously, 
    # we explicitly fan-out using Python's asyncio.gather.
    tasks = [
        call_model(searcher_prompt, f"Research this specific subtopic: {subtopic}")
        for subtopic in subtopics
    ]
    
    # Wait for all parallel agents to finish
    raw_findings = await asyncio.gather(*tasks)
    structured_findings = []
    for topic, finding in zip(subtopics, raw_findings):
        structured_findings.append(SearchFinding(
            subtopic=topic,
            metadata="Source: Simulated Search",
            content=finding
        ))
        
    synthesis_payload = SynthesisRequest(
        original_goal=user_request,
        findings=structured_findings
    )
    final_report = await call_model(
        synthesizer_prompt, 
        f"Please synthesize the following data:\n{synthesis_payload.model_dump_json(indent=2)}"
    )
    
    return final_report

if __name__ == "__main__":
    request = "Compare the Apollo 11 and Voyager 1 missions."
    result = asyncio.run(run_spawning_api_workflow(request))
