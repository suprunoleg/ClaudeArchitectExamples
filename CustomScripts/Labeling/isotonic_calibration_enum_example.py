"""
Isotonic Calibration with Uniform Tool Enum Threshold Params

This example demonstrates the enterprise standard for handling model confidence.
Instead of allowing different downstream tools to guess what a raw confidence
float (e.g., 0.85) means, the central orchestrator is responsible for:
1. Extracting the raw float from the LLM.
2. Applying calibration (e.g., Isotonic Regression) to get a true probability.
3. Translating the probability into a strongly typed Enum (low/medium/high).

Downstream tools only accept the Enum, completely eliminating human engineering
drift and standardizing semantics across all tools.
"""

import os
from enum import Enum
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load API key
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

# ==========================================
# 1. THE SHARED SCHEMA (The Source of Truth)
# ==========================================
# This is defined ONCE in a central repository. 
# All teams import this exact Enum.
class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# ==========================================
# 2. THE DOWNSTREAM TOOL (Authored by Team A)
# ==========================================
# Notice how the tool is completely blind to floats. 
# It cannot drift, because Pydantic will throw a validation 
# error if it receives anything other than 'low', 'medium', or 'high'.
class ApprovalToolSchema(BaseModel):
    transaction_id: str
    confidence: ConfidenceLevel  # Enforced at the type level!

def auto_approve_transaction(params: ApprovalToolSchema):
    print(f"🔧 Tool Execution -> Received Enum: {params.confidence.value.upper()}")
    if params.confidence == ConfidenceLevel.HIGH:
        return f"Transaction {params.transaction_id} APPROVED automatically."
    elif params.confidence == ConfidenceLevel.MEDIUM:
        return f"Transaction {params.transaction_id} FLAGGED for human review."
    else:
        return f"Transaction {params.transaction_id} REJECTED."

# ==========================================
# 3. LLM INTERFACE SCHEMA
# ==========================================
class LLMTransactionAssessment(BaseModel):
    transaction_id: str = Field(description="The ID of the transaction extracted from the text")
    raw_confidence: float = Field(description="Raw confidence score from 0.0 to 1.0 that this transaction is legitimate and safe")

# ==========================================
# 4. THE ORCHESTRATOR (The Central Brain)
# ==========================================
def apply_isotonic_calibration(raw_score: float) -> float:
    """
    Mock function representing your central MLOps calibration logic.
    Converts the AI's 'bragging' 0.99 into a true historical probability.
    """
    # Example: The model is overconfident, so a raw score is scaled down.
    # In a real system, this would use sklearn's IsotonicRegression model
    # fitted on historical ground truth data.
    return raw_score * 0.81  

def orchestrator_pipeline(transaction_text: str):
    print(f"\n" + "="*60)
    print(f"PROCESSING TRANSACTION")
    print(f"Text: '{transaction_text}'")
    print("="*60)
    
    # Step 1: Get raw float from LLM
    llm = ChatAnthropic(model=DEFAULT_MODEL, temperature=0)
    structured_llm = llm.with_structured_output(LLMTransactionAssessment)
    
    messages = [
        SystemMessage(content="You are a transaction risk analysis AI. Assess the transaction and output your raw confidence that it is legitimate (not fraud)."),
        HumanMessage(content=transaction_text)
    ]
    
    print("\n🧠 Step 1: Querying LLM...")
    try:
        llm_result = structured_llm.invoke(messages)
    except Exception as e:
        print(f"   ❌ LLM Error: {e}")
        return

    raw_llm_float = llm_result.raw_confidence
    txn_id = llm_result.transaction_id
    
    print(f"   Received raw LLM hallucinated score: {raw_llm_float}")
    
    # Step 2: Centralized Calibration (Fix the math)
    print("\n🧮 Step 2: Centralized Calibration")
    true_probability = apply_isotonic_calibration(raw_llm_float)
    print(f"   Calibrated true probability: {true_probability:.2f}")
    
    # Step 3: Centralized Normalization (Map to the schema)
    print("\n⚖️ Step 3: Centralized Normalization")
    if true_probability >= 0.85:
        canonical_enum = ConfidenceLevel.HIGH
    elif true_probability >= 0.50:
        canonical_enum = ConfidenceLevel.MEDIUM
    else:
        canonical_enum = ConfidenceLevel.LOW
        
    print(f"   Mapped to Canonical Enum: {canonical_enum.value}")
    
    # Step 4: Invoke the Tool (Safe and predictable)
    print("\n🛠️ Step 4: Invoke the Tool")
    try:
        tool_inputs = ApprovalToolSchema(
            transaction_id=txn_id, 
            confidence=canonical_enum
        )
        result = auto_approve_transaction(tool_inputs)
        print(f"   Tool Action Result: {result}")
    except Exception as e:
        print(f"   Validation Error: {e}")

if __name__ == "__main__":
    # Test case 1: Very safe transaction -> LLM outputs high confidence
    orchestrator_pipeline("Transaction TXN-10495: $5.00 coffee at Starbucks by returning customer.")
    
    # Test case 2: Suspicious transaction -> LLM outputs lower confidence
    orchestrator_pipeline("Transaction TXN-99382: $500.00 electronics purchase at 3 AM from new IP address.")
