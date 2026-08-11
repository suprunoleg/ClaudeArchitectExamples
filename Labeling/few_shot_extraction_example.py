"""
Few-Shot Extraction

Illustrates how to use few-shot examples (providing examples in the prompt) to
guide the model in correctly formatting and labeling outputs. Providing
explicit positive and negative examples often yields better zero-shot
performance than detailed prompt instructions alone.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

class FinancialExtraction(BaseModel):
    revenue: float = Field(description="The extracted final revenue value in millions.")

DATASET = [
    {"id": 11, "text": "We sold 100,000 units at $500 each. However, a bulk discount of 15% applies to all units sold past the 50,000 mark. Calculate total revenue in millions.", "true_revenue": 46.25},
    {"id": 15, "text": "Gross sales were 1,000,000 units at $50 each. We had a return rate of 5%. We also gave a 10% rebate on 200,000 of those units. Calculate net revenue in millions.", "true_revenue": 46.5}
]

# We inject a specific example of how to handle tiered mathematical operations.
FEW_SHOT_PROMPT = """Extract the core/final revenue from the text. Follow all explicit mathematical instructions. Output the value in millions.

Here is an example of how to process a tiered mathematical operation correctly:
<example>
Input: We sold 20,000 units at $10 each. A bulk discount of 50% applies to units sold past the 10,000 mark.
Correct Logic: 
1) First 10,000 units are full price: 10,000 * 10 = $100,000.
2) Remaining 10,000 units are discounted by 50% (price is $5): 10,000 * 5 = $50,000.
3) Total = $150,000 (0.15 million).
Output: 0.15
</example>

Here is an example of handling rebates and returns:
<example>
Input: Gross sales 5,000 units at $100. Return rate 10%. Rebate of 20% on 1,000 units.
Correct Logic:
1) Gross = 5,000 * 100 = $500,000
2) Returns = 10% of 500,000 = $50,000
3) Rebate = 1,000 units * $100 = $100,000. 20% rebate on those = $20,000.
4) Net = 500,000 - 50,000 - 20,000 = $430,000 (0.43 million).
Output: 0.43
</example>
"""

def run_few_shot():
    # Haiku failed on these without few-shot prompting!
    llm = ChatAnthropic(model="claude-haiku-4-5", temperature=0)
    structured_llm = llm.with_structured_output(FinancialExtraction)
    
    print("=" * 80)
    print("🎯 RUNNING FEW-SHOT PIPELINE")
    print("=" * 80)
    
    for item in DATASET:
        messages = [
            SystemMessage(content=FEW_SHOT_PROMPT),
            HumanMessage(content=item["text"])
        ]
        
        try:
            extraction = structured_llm.invoke(messages)
            is_correct = abs(extraction.revenue - item["true_revenue"]) < 0.01
            status = "✅ FIXED IT!" if is_correct else "❌ STILL FAILED"
            
            print(f"ID {item['id']} | True: {item['true_revenue']} | Pred: {extraction.revenue} | {status}")
        except Exception as e:
            print(f"ID {item['id']} | ❌ Error extracting: {e}")

if __name__ == "__main__":
    run_few_shot()
