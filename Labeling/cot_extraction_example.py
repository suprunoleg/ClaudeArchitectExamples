import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

class CoTFinancialExtraction(BaseModel):
    scratchpad: str = Field(description="Your step-by-step mathematical reasoning. Calculate the parts first before determining the final revenue.")
    revenue: float = Field(description="The extracted final revenue value in millions.")

DATASET = [
    {"id": 11, "text": "We sold 100,000 units at $500 each. However, a bulk discount of 15% applies to all units sold past the 50,000 mark. Calculate total revenue in millions.", "true_revenue": 46.25},
    {"id": 15, "text": "Gross sales were 1,000,000 units at $50 each. We had a return rate of 5%. We also gave a 10% rebate on 200,000 of those units. Calculate net revenue in millions.", "true_revenue": 46.5}
]

def run_cot():
    # Haiku failed on these without CoT!
    llm = ChatAnthropic(model="claude-haiku-4-5", temperature=0)
    structured_llm = llm.with_structured_output(CoTFinancialExtraction)
    
    print("=" * 80)
    print("🧠 RUNNING CHAIN OF THOUGHT (CoT) PIPELINE")
    print("=" * 80)
    
    for item in DATASET:
        messages = [
            SystemMessage(content="Extract the core/final revenue from the text. Follow all explicit mathematical instructions. Output the value in millions."),
            HumanMessage(content=item["text"])
        ]
        
        try:
            extraction = structured_llm.invoke(messages)
            is_correct = abs(extraction.revenue - item["true_revenue"]) < 0.01
            status = "✅ FIXED IT!" if is_correct else "❌ STILL FAILED"
            
            print(f"\nID {item['id']} | True: {item['true_revenue']} | Pred: {extraction.revenue} | {status}")
            print(f"Reasoning Scratchpad:\n{extraction.scratchpad}\n")
            print("-" * 80)
        except Exception as e:
            print(f"ID {item['id']} | ❌ Error extracting: {e}")

if __name__ == "__main__":
    run_cot()
