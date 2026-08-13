"""
Verification Loop

Shows a pattern where the model's output is evaluated and potentially fed back
into the model for self-correction or multi-step verification. This iterative
critique process is highly effective for complex reasoning tasks that require
high precision.
"""

import os
import re
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"


load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

class FinancialExtraction(BaseModel):
    revenue: float = Field(description="The extracted final revenue value in millions.")

@tool
def calculate(expression: str) -> str:
    """Evaluates a mathematical expression and returns the result. Do not include commas or currency symbols in the expression."""
    try:
        # Very basic safe eval for math
        allowed_chars = set("0123456789+-*/(). ")
        if not set(expression).issubset(allowed_chars):
            return "Error: Invalid characters in expression. Only numbers and +-/* are allowed."
        return str(eval(expression))
    except Exception as e:
        return f"Error evaluating expression: {e}"

DATASET = [
    {"id": 11, "text": "We sold 100,000 units at $500 each. However, a bulk discount of 15% applies to all units sold past the 50,000 mark. Calculate total revenue in millions.", "true_revenue": 46.25},
    {"id": 15, "text": "Gross sales were 1,000,000 units at $50 each. We had a return rate of 5%. We also gave a 10% rebate on 200,000 of those units. Calculate net revenue in millions.", "true_revenue": 46.5}
]

def run_verification_loop():
    llm = ChatAnthropic(model=DEFAULT_MODEL, temperature=0)
    
    # Agent A: The blind extractor
    extractor_llm = llm.with_structured_output(FinancialExtraction)
    
    # Agent B: The Auditor using LangGraph React Agent
    auditor_agent = create_react_agent(
        llm,
        tools=[calculate]
    )
    
    print("=" * 80)
    print("🕵️ RUNNING TOOL-AUGMENTED VERIFICATION LOOP")
    print("=" * 80)
    
    for item in DATASET:
        print(f"\nProcessing ID {item['id']}...")
        
        # --- STEP 1: INITIAL EXTRACTION ---
        extract_msgs = [
            SystemMessage(content="Extract the core/final revenue from the text. Output the value in millions."),
            HumanMessage(content=item["text"])
        ]
        
        try:
            initial_extraction = extractor_llm.invoke(extract_msgs)
            print(f"  [Agent A] Initial Extraction: {initial_extraction.revenue}")
            
            # --- STEP 2: AUDIT & VERIFY ---
            audit_prompt = f"""You are a financial auditor. Your job is to verify Agent A's math step-by-step. You MUST use the calculate tool for ALL mathematical operations. Once verified, end your final response with exactly: 'FINAL_REVENUE: <number>' where <number> is your final corrected value in millions.

Original Text: "{item['text']}"
Agent A extracted: {initial_extraction.revenue} million.

Verify this extraction step-by-step using your calculate tool. End your final response with 'FINAL_REVENUE: <number>'."""
            
            # Run the react agent loop
            result = auditor_agent.invoke({"messages": [HumanMessage(content=audit_prompt)]})
            
            final_message = result["messages"][-1].content
            
            # Print the steps it took
            for msg in result["messages"][1:-1]: # Skip the first human msg and final msg
                if getattr(msg, "tool_calls", None):
                    for call in msg.tool_calls:
                        print(f"  [Agent B] 🧮 Calling Calculator: {call['args']['expression']}")
                elif getattr(msg, "name", None) == "calculate":
                    print(f"  [Agent B] 🧮 Calculator Result: {msg.content}")
            
            # Parse final answer
            match = re.search(r"FINAL_REVENUE:\s*([\d.]+)", final_message)
            if match:
                corrected_revenue = float(match.group(1))
                # print(f"  [Agent B] Final Audit Conclusion:\n{final_message}\n")
            else:
                corrected_revenue = initial_extraction.revenue
                print(f"  [Agent B] Failed to parse final revenue. Defaulting to Agent A's answer.")
            
            # Check against ground truth
            is_correct = abs(corrected_revenue - item["true_revenue"]) < 0.01
            status = "✅ FINAL ANSWER CORRECT!" if is_correct else "❌ FINAL ANSWER STILL WRONG"
            
            print(f"  Result -> True: {item['true_revenue']} | Final Pred: {corrected_revenue} | {status}")
            
        except Exception as e:
            print(f"ID {item['id']} | ❌ Error: {e}")

if __name__ == "__main__":
    run_verification_loop()
