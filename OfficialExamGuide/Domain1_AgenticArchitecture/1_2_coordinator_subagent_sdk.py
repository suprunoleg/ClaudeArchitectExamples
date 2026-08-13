"""
Task Statement 1.2: Orchestrate multi-agent systems with coordinator-subagent patterns
(SDK VERSION)

Knowledge of:
- Hub-and-spoke architecture where a coordinator agent manages all inter-subagent communication
- How subagents operate with isolated context
- The role of the coordinator in task decomposition, delegation, and result aggregation
- Risks of overly narrow task decomposition

Skills in:
- Designing coordinator agents that dynamically select subagents
- Partitioning research scope across subagents to minimize duplication
- Implementing iterative refinement loops where the coordinator evaluates synthesis output for gaps

This example demonstrates the "Hybrid SDK" approach: Using the `claude_agent_sdk` to power
the actual LLM calls (proving knowledge of SDK primitives), but wrapping the Coordinator
routing in strict Python code and Pydantic models for deterministic control flow.
"""

import os
import asyncio
from typing import List, Optional
from pydantic import BaseModel, Field
from claude_agent_sdk import ClaudeAgentOptions, query, ResultMessage

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

# ==============================================================================
# STRUCTURED OUTPUTS (Deterministic Control Flow)
# ==============================================================================

class RoutingDecision(BaseModel):
    reasoning: str = Field(description="Explanation of why specific subagents are needed.")
    selected_subtopics: List[str] = Field(description="List of distinct subtopics to search. Do not be overly narrow.")

class SynthesisAssessment(BaseModel):
    is_complete: bool = Field(description="True if the topic is fully covered without gaps.")
    final_report: str = Field(description="The synthesized report text.")
    coverage_gaps: List[str] = Field(description="Specific missing topics or weak points requiring further research.")

# ==============================================================================
# DETERMINISTIC ORCHESTRATOR 
# ==============================================================================

async def execute_task(prompt: str, system_prompt: str, response_schema: Optional[type[BaseModel]] = None) -> any:
    """Helper function to run a single, bounded subagent task using the SDK."""
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt=system_prompt
    )
    
    # Force structured output if a Pydantic schema is provided
    if response_schema:
        options.output_format = {
            "type": "json_schema",
            "schema": response_schema.model_json_schema()
        }

    final_result = None
    error_msg = None
    async for msg in query(prompt=prompt, options=options):
        if isinstance(msg, ResultMessage):
            if response_schema:
                if msg.structured_output:
                    final_result = response_schema.model_validate(msg.structured_output)
                else:
                    error_msg = f"Expected structured output but got none. Raw result: {msg.result}"
            else:
                final_result = msg.result
                
    if error_msg:
        raise ValueError(error_msg)
        
    return final_result

async def run_deterministic_sdk_workflow(user_request: str):
    # Subagent Prompts
    router_prompt = "You are the Router. Break the user's request into comprehensive subtopics."
    searcher_prompt = "You are the Searcher. Your job is strictly to search and return raw facts. Do not synthesize."
    synthesizer_prompt = "You are the Synthesizer. Evaluate findings for gaps. Output strict JSON."
    
    # 1. EXAM SKILL: Task Decomposition (Partitioning scope to minimize duplication)
    print("1. Decomposing request...")
    routing: RoutingDecision = await execute_task(
        prompt=f"Decompose this request into distinct research subtopics: {user_request}",
        system_prompt=router_prompt,
        response_schema=RoutingDecision
    )
    
    context_bank = []
    
    # 2. EXAM SKILL: Hub-and-spoke execution with isolated context
    # ANTI-TOKEN-HOG RULE: Limit to 2 parallel subagents maximum
    safe_subtopics = routing.selected_subtopics[:2]
    print(f"2. Dispatching {len(safe_subtopics)} parallel searches (limited from {len(routing.selected_subtopics)})...")
    tasks = [
        execute_task(f"Find information about: {subtopic}", searcher_prompt) 
        for subtopic in safe_subtopics
    ]
    initial_findings = await asyncio.gather(*tasks)
    context_bank.extend(initial_findings)
    
    # 3. EXAM SKILL: Iterative refinement loops (evaluating synthesis output for gaps)
    # ANTI-TOKEN-HOG RULE: Strictly limit agentic loops
    max_iterations = 2
    for iteration in range(1, max_iterations + 1):
        print(f"3. Refinement Iteration {iteration}/{max_iterations}: Synthesizing...")
        context_str = "\n".join(str(f) for f in context_bank)
        synth_input = f"Topic: {user_request}\n\nGathered Context:\n{context_str}"
        
        synthesis: SynthesisAssessment = await execute_task(
            synth_input, 
            synthesizer_prompt,
            response_schema=SynthesisAssessment
        )
        
        if synthesis.is_complete or iteration == max_iterations:
            print("   -> Quality threshold met.")
            return synthesis.final_report
            
        # ANTI-TOKEN-HOG RULE: Limit parallel gap research
        safe_gaps = synthesis.coverage_gaps[:1]
        print(f"   -> Gaps identified. Dispatching {len(safe_gaps)} parallel gap searches (limited from {len(synthesis.coverage_gaps)})...")
        # Parallel gap research
        gap_tasks = [
            execute_task(f"Find information addressing this gap: {gap}", searcher_prompt) 
            for gap in safe_gaps
        ]
        new_findings = await asyncio.gather(*gap_tasks)
        context_bank.extend(new_findings)

if __name__ == "__main__":
    request = "Research the impact of AI on creative industries."
    try:
        result = asyncio.run(run_deterministic_sdk_workflow(request))
        print("\n=== FINAL SYNTHESIZED REPORT ===")
        print(result)
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")
