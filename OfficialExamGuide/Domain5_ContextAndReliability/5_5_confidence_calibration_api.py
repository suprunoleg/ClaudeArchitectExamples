"""
Task Statement 5.5: Design human review workflows and confidence calibration
(API VERSION)

This file demonstrates how to build the identical patterns tested in 5.5 using 
deterministic, code-first Python architecture instead of relying on the SDK.

Knowledge of:
- How to instruct an LLM to output a "confidence score".
- How to route low-confidence predictions to a human-in-the-loop (HITL) review queue.

Skills in:
- Using structured output tools to force a `confidence_score` float.
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
# STRUCTURED OUTPUT & CONFIDENCE SCORING
# ==============================================================================

EXTRACTION_TOOL = {
    "name": "extract_diagnosis",
    "description": "Extract the diagnosis and your confidence score.",
    "input_schema": {
        "type": "object",
        "properties": {
            "diagnosis": {"type": "string"},
            "confidence_score": {
                "type": "number",
                "description": "Your confidence from 0.0 to 1.0. If you are guessing based on vague symptoms, score < 0.8."
            }
        },
        "required": ["diagnosis", "confidence_score"]
    }
}

async def run_confidence_calibration_api(patient_notes: str):
    print(f"\n--- Starting Deterministic API Confidence Calibration Workflow ---")
    
    try:
        # We force the LLM to use the extraction tool to guarantee the schema
        response = await client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=500,
            system="You are a medical extractor.",
            messages=[{"role": "user", "content": patient_notes}],
            tools=[EXTRACTION_TOOL],
            tool_choice={"type": "tool", "name": "extract_diagnosis"}
        )
    except Exception as e:
        print(f"[API Error - expected if dummy key] {e}")
        return
        
    tool_block = next((b for b in response.content if b.type == 'tool_use'), None)
    if not tool_block:
        print("Failed to use tool.")
        return
        
    # EXAM SKILL: Routing based on confidence
    # If confidence is below 0.85, we escalate to a human doctor.
    extracted_data = tool_block.input
    confidence = float(extracted_data.get("confidence_score", 0.0))
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
        asyncio.run(run_confidence_calibration_api(notes_1))
        
        # Low confidence scenario (ambiguous)
        notes_2 = "Patient feels slightly dizzy and has a mild headache that comes and goes."
        print(f"\nPatient 2 Notes: {notes_2}")
        asyncio.run(run_confidence_calibration_api(notes_2))
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed: {e}")
