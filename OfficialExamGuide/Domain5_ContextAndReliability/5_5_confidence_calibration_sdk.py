"""
Task Statement 5.5: Design human review workflows and confidence calibration
(SDK VERSION)

Knowledge of:
- How to instruct an LLM to output a "confidence score".
- How to route low-confidence predictions to a human-in-the-loop (HITL) review queue.

Skills in:
- Using structured output schemas (Pydantic) to force a `confidence_score` float.
"""

import os
import asyncio
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
# STRUCTURED OUTPUT & CONFIDENCE SCORING
# ==============================================================================

class MedicalExtraction(BaseModel):
    diagnosis: str
    confidence_score: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Your confidence in this diagnosis from 0.0 to 1.0. If you are guessing based on vague symptoms, score < 0.8."
    )

async def run_confidence_calibration_sdk(patient_notes: str):
    print(f"\n--- Starting SDK Confidence Calibration Workflow ---")
    
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        system_prompt="You are a medical extractor. Extract the diagnosis and rate your confidence.",
        response_schema=MedicalExtraction
    )

    extracted_data = None
    try:
        async for msg in query(prompt=patient_notes, options=options):
            if isinstance(msg, ResultMessage):
                extracted_data = msg.result
    except Exception as e:
        print(f"[SDK Error - expected if dummy key] {e}")
        return
        
    if not extracted_data:
        return
        
    # EXAM SKILL: Routing based on confidence
    # If confidence is below 0.85, we escalate to a human doctor.
    confidence = extracted_data.get("confidence_score", 0.0)
    diagnosis = extracted_data.get("diagnosis", "Unknown")
    
    print(f"Extracted Diagnosis: {diagnosis}")
    print(f"Confidence Score: {confidence}")
    
    if confidence < 0.85:
        print(">> ESCALATION TRIGGERED: Confidence too low. Routing to human doctor for manual review.")
    else:
        print(">> HIGH CONFIDENCE: Proceeding with automated workflow.")

if __name__ == "__main__":
    try:
        # High confidence scenario
        notes_1 = "Patient presents with a clearly broken right femur protruding from the skin."
        print(f"\nPatient 1 Notes: {notes_1}")
        asyncio.run(run_confidence_calibration_sdk(notes_1))
        
        # Low confidence scenario (ambiguous)
        notes_2 = "Patient feels slightly dizzy and has a mild headache that comes and goes."
        print(f"\nPatient 2 Notes: {notes_2}")
        asyncio.run(run_confidence_calibration_sdk(notes_2))
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")
