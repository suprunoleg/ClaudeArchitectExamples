"""
Task Statement 1.2: Orchestrate multi-agent systems with coordinator-subagent patterns

Knowledge of:
- Hub-and-spoke architecture where a coordinator agent manages all inter-subagent communication
- How subagents operate with isolated context (they do not inherit history automatically)
- The role of the coordinator in task decomposition, delegation, and result aggregation
- Risks of overly narrow task decomposition

Skills in:
- Designing coordinator agents that dynamically select subagents (not just fixed pipelines)
- Partitioning research scope to minimize duplication
- Implementing iterative refinement loops (evaluating gaps and re-delegating)
- Routing all communication through the coordinator for observability
"""

import os
import asyncio
import logging
import uuid
import json
from typing import List, Any, Dict, Optional
from pydantic import BaseModel, Field
from anthropic import AsyncAnthropic

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
from dotenv import load_dotenv
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
client = AsyncAnthropic()

# ==============================================================================
# STRUCTURED OUTPUTS (Enforcing Deterministic Control Flow)
# ==============================================================================
# EXAM SKILL: We use Pydantic schemas instead of probabilistic system prompts 
# to enforce strict types and deterministic routing decisions in the pipeline.

class RoutingDecision(BaseModel):
    reasoning: str = Field(description="Explanation of why specific subagents are needed.")
    selected_subagents: List[str] = Field(description="Required subagents: e.g., 'searcher', 'synthesizer'.")
    extracted_parameters: Dict[str, Any] = Field(description="Query parameters scoped for each selected agent.")

class MessageEnvelope(BaseModel):
    """Standardized Communication Envelope (Observability)"""
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    destination: str
    payload: Dict[str, Any]
    error: Optional[str] = None

class EvaluatorAssessment(BaseModel):
    is_sufficient: bool = Field(description="True if synthesis fully answers the prompt.")
    identified_gaps: List[str] = Field(description="Missing topics requiring further research.")
    followup_queries: List[str] = Field(description="Targeted queries to address identified gaps.")


# ==============================================================================
# SUBAGENT IMPLEMENTATIONS (Isolated Context)
# ==============================================================================

class BaseSubAgent:
    def __init__(self, name: str):
        self.name = name

    async def execute(self, envelope: MessageEnvelope) -> MessageEnvelope:
        """Subagents ONLY accept envelopes from the coordinator and return envelopes to it."""
        task_data = envelope.payload.get("data", "")
        
        # EXAM SKILL: Subagents operate with isolated context. 
        # They do not automatically inherit the coordinator's history.
        # (Using a simulated async delay to represent the subagent's actual LLM generation)
        await asyncio.sleep(0.5) 
        result_data = f"[{self.name}] Completed task for: '{task_data}'"
        
        return MessageEnvelope(
            trace_id=envelope.trace_id,
            source=self.name,
            destination="Coordinator",
            payload={"result": result_data}
        )

# ==============================================================================
# COORDINATOR AGENT (Hub-and-Spoke, Dynamic Routing, Iterative Refinement)
# ==============================================================================

class DeterministicCoordinator:
    def __init__(self):
        self.agents = {
            "searcher": BaseSubAgent("Searcher"),
            "synthesizer": BaseSubAgent("Synthesizer")
        }
        self.global_context = []

    async def route_message(self, target_agent: str, data: Any, trace_id: str) -> MessageEnvelope:
        """EXAM SKILL: Routing all communication through the coordinator for observability."""
        outbound = MessageEnvelope(
            trace_id=trace_id, 
            source="Coordinator", 
            destination=target_agent, 
            payload={"data": data}
        )
        
        logging.info(f"[Trace: {trace_id}] Routing from Coordinator -> {target_agent}")
        
        agent = self.agents.get(target_agent)
        if not agent:
            raise ValueError(f"Agent {target_agent} not found.")

        try:
            # Execute subagent with isolated context
            inbound = await agent.execute(outbound)
            logging.info(f"[Trace: {trace_id}] Received reply from {target_agent} -> Coordinator")
            
            # Centralized Memory
            self.global_context.append(inbound.payload)
            return inbound
            
        except Exception as e:
            # Consistent error handling: exceptions don't crash downstream agents
            logging.error(f"[Trace: {trace_id}] {target_agent} Failed: {str(e)}")
            return MessageEnvelope(
                trace_id=trace_id, 
                source=target_agent, 
                destination="Coordinator", 
                payload={"result": None}, 
                error=str(e)
            )

    async def analyze_and_route(self, user_query: str) -> RoutingDecision:
        """EXAM SKILL: Dynamic Task Decomposition & Routing"""
        prompt = f"Analyze request: '{user_query}'. Select required subagents."
        
        try:
            # In a real app, you would pass the RoutingDecision schema to the tool_choice parameter
            response = await client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=500,
                system="You are an intent router. Determine the required agents.",
                messages=[{"role": "user", "content": prompt}]
            )
        except Exception:
            pass # Dummy key handling

        # Mocking the structured parse for this deterministic example
        return RoutingDecision(
            reasoning="Broad research requested. Needs both searcher and synthesizer.",
            selected_subagents=["searcher", "synthesizer"],
            extracted_parameters={"searcher": user_query, "synthesizer": "Synthesize findings"}
        )

    async def evaluate_synthesis(self, synthesis: str, iteration: int) -> EvaluatorAssessment:
        """EXAM SKILL: Evaluates output for gaps."""
        # Simulated LLM evaluation logic: 
        # Fails the first iteration to prove the refinement loop works.
        is_sufficient = iteration >= 2
        
        return EvaluatorAssessment(
            is_sufficient=is_sufficient,
            identified_gaps=[] if is_sufficient else ["Missing specific industry metrics."],
            followup_queries=[] if is_sufficient else ["industry metrics"]
        )

    async def execute_query(self, user_query: str):
        trace_id = str(uuid.uuid4())
        logging.info(f"--- Starting Workflow [Trace: {trace_id}] ---")

        # Step 1: Dynamic classification (Partitioning research scope)
        decision = await self.analyze_and_route(user_query)
        logging.info(f"Routing Reasoning: {decision.reasoning}")
        logging.info(f"Selected Subagents: {decision.selected_subagents}")

        if "searcher" not in decision.selected_subagents:
            return "No search required."

        # Step 2: EXAM SKILL: Iterative refinement loops
        max_iterations = 3
        current_context = ""
        
        # Initial search delegation
        search_res = await self.route_message("searcher", decision.extracted_parameters["searcher"], trace_id)
        current_context += str(search_res.payload["result"])

        for iteration in range(1, max_iterations + 1):
            logging.info(f"--- Refinement Iteration {iteration}/{max_iterations} ---")
            
            # Synthesize current findings
            synth_payload = f"Topic: {user_query} | Context: {current_context}"
            synth_res = await self.route_message("synthesizer", synth_payload, trace_id)
            
            # Evaluate for gaps
            assessment = await self.evaluate_synthesis(str(synth_res.payload["result"]), iteration)
            
            if assessment.is_sufficient or iteration == max_iterations:
                logging.info("[Coordinator] Coverage sufficient. Finalizing.")
                return synth_res.payload["result"]
                
            logging.info(f"[Coordinator] Gaps identified: {assessment.identified_gaps}")
            logging.info(f"[Coordinator] Dispatching targeted queries: {assessment.followup_queries}")
            
            # Re-delegate missing topics (using parallel execution to save time)
            # EXAM SKILL: Parallel execution for multiple gaps
            tasks = [self.route_message("searcher", q, trace_id) for q in assessment.followup_queries]
            new_findings = await asyncio.gather(*tasks)
            
            for f in new_findings:
                current_context += "\n" + str(f.payload["result"])

if __name__ == "__main__":
    coordinator = DeterministicCoordinator()
    result = asyncio.run(coordinator.execute_query("Research AI impact on art"))
    
    # High-value print statement to prove state changed
    print("\n=== FINAL RESULT ===")
    print(result)
