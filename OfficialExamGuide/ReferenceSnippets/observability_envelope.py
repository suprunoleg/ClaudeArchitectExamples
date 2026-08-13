import asyncio
import logging
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# 1. Standardized Communication Envelope (Observability)
class MessageEnvelope(BaseModel):
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    destination: str
    payload: Dict[str, Any]
    error: Optional[str] = None

# 2. Isolated Subagents (Controlled Information Flow)
class BaseSubAgent:
    def __init__(self, name: str):
        self.name = name

    async def execute(self, envelope: MessageEnvelope) -> MessageEnvelope:
        """Subagents ONLY accept envelopes from the coordinator and return envelopes to it."""
        task_data = envelope.payload.get("data", "")
        
        # Simulated Work & Error Generation
        if self.name == "DatabaseAgent" and "crash" in task_data:
            raise ConnectionError("Database connection timed out.")
            
        result_data = f"[{self.name}] Processed: {task_data}"
        await asyncio.sleep(0.5) # Simulate API call
        
        return MessageEnvelope(
            trace_id=envelope.trace_id,
            source=self.name,
            destination="Coordinator",
            payload={"result": result_data}
        )

# 3. The Central Hub (Consistent Error Handling & Routing)
class CoordinatorAgent:
    def __init__(self):
        self.name = "Coordinator"
        self.agents = {
            "ResearchAgent": BaseSubAgent("ResearchAgent"),
            "DatabaseAgent": BaseSubAgent("DatabaseAgent"),
            "SummaryAgent": BaseSubAgent("SummaryAgent")
        }
        # Centralized State/Memory - Subagents do NOT have access to this
        self.global_context = []

    async def route_message(self, target_agent: str, data: Any, trace_id: str) -> MessageEnvelope:
        """All inter-agent communication flows through this single choke point."""
        
        # --- A. CONTROLLED INFORMATION FLOW ---
        # The coordinator explicitly slices the context. 
        # The subagent does NOT inherit the coordinator's full conversation history.
        outbound_envelope = MessageEnvelope(
            trace_id=trace_id,
            source=self.name,
            destination=target_agent,
            payload={"data": data}
        )
        
        # --- B. OBSERVABILITY ---
        logging.info(f"[Trace: {trace_id}] Routing message from {self.name} -> {target_agent}")

        agent = self.agents[target_agent]
        
        try:
            # Execute subagent
            inbound_envelope = await agent.execute(outbound_envelope)
            
            # Log successful return
            logging.info(f"[Trace: {trace_id}] Received reply from {target_agent} -> {self.name}")
            self.global_context.append(inbound_envelope.payload)
            return inbound_envelope

        except Exception as e:
            # --- C. CONSISTENT ERROR HANDLING ---
            # Exceptions are caught centrally; they do not crash the downstream agents.
            logging.error(f"[Trace: {trace_id}] {target_agent} Failed: {str(e)}")
            
            # Coordinator decides on fallback policy (e.g., return structured error, retry, or skip)
            return MessageEnvelope(
                trace_id=trace_id,
                source=target_agent,
                destination=self.name,
                payload={"result": None},
                error=f"Categorized Error: {type(e).__name__} - {str(e)}"
            )

    async def run_workflow(self, user_request: str):
        trace_id = str(uuid.uuid4())
        logging.info(f"--- Starting New Workflow [Trace: {trace_id}] ---")

        # Step 1: Route to Researcher
        research_res = await self.route_message("ResearchAgent", user_request, trace_id)
        
        # Step 2: Route to Database (Simulating a failure)
        db_res = await self.route_message("DatabaseAgent", "crash_command", trace_id)
        
        if db_res.error:
            logging.warning(f"[Trace: {trace_id}] Applying fallback for DatabaseAgent failure. Proceeding without DB data.")
            db_data = "Fallback Data"
        else:
            db_data = db_res.payload["result"]

        # Step 3: Route combined context to Summarizer
        # Notice how ResearchAgent and SummaryAgent never speak to each other.
        synthesis_payload = f"Research: {research_res.payload['result']} | DB: {db_data}"
        final_res = await self.route_message("SummaryAgent", synthesis_payload, trace_id)

        logging.info(f"--- Workflow Complete: {final_res.payload['result']} ---")
        return final_res.payload["result"]

if __name__ == "__main__":
    coordinator = CoordinatorAgent()
    asyncio.run(coordinator.run_workflow("Analyze Q3 metrics"))
