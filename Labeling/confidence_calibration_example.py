import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

# Load API key
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

class FinancialExtraction(BaseModel):
    revenue: float = Field(description="The extracted revenue value in millions.")
    confidence_score: float = Field(description="Your confidence that this revenue extraction is completely correct, from 0.0 to 1.0.")

# Mock Ground Truth Dataset
# These are deliberately complex to confuse smaller models and force a calibration failure.
DATASET = [
    {"id": 1, "text": "Q3 revenue was 45.2 million, a solid quarter.", "true_revenue": 45.2},
    {"id": 2, "text": "We saw a gross volume of 100 million, while net revenue after costs was 40 million.", "true_revenue": 40.0},
    {"id": 3, "text": "Total income was 50 million, consisting of 30M from investments and 20M from operations. The operations figure represents our core revenue.", "true_revenue": 20.0},
    {"id": 4, "text": "Sales were strong at 50 million, though actual recognized revenue was deferred by 20% leaving us with 40 million.", "true_revenue": 40.0},
    {"id": 5, "text": "The gross revenue was 50M. The net revenue was 30M. However, according to our strict internal accounting standard XYZ, revenue is defined as gross revenue minus a 15M flat franchise fee.", "true_revenue": 35.0},
    {"id": 6, "text": "Q1: 10.15M, Q2: 12.25M, Q3: 11.35M, Q4: 15.42M. Total annual revenue is the exact sum of these quarters.", "true_revenue": 49.17},
    {"id": 7, "text": "Revenue: 15.2M EUR. Note: You must convert to USD assuming 1 EUR = 1.1 USD to get the final revenue figure.", "true_revenue": 16.72},
    {"id": 8, "text": "Net income was $5M, total assets $100M, and revenue came in at $25M.", "true_revenue": 25.0},
    {"id": 9, "text": "Our gross bookings hit 150M. We recognize 50% immediately and 50% next year. Furthermore, we had a 10M clawback on this year's recognized portion. What is this year's final recognized revenue?", "true_revenue": 65.0},
    {"id": 10, "text": "Base revenue is 40M. We also own a 30% stake in a subsidiary that made 100M in revenue. According to equity method accounting, we do not consolidate their revenue. What is our consolidated revenue?", "true_revenue": 40.0},
    {"id": 11, "text": "We sold 100,000 units at $500 each. However, a bulk discount of 15% applies to all units sold past the 50,000 mark. Calculate total revenue in millions.", "true_revenue": 46.25},
    {"id": 12, "text": "We operate two segments: Hardware and Software. Hardware generated 30M in Q1 and 40M in Q2. Software generated 10M per quarter for the entire year. We divested the Hardware division on July 1st, so its H2 revenue is excluded. What is our total annual retained revenue across both segments?", "true_revenue": 110.0},
    {"id": 13, "text": "Our SaaS ARR grew from 100M to 150M this year. Usage-based revenue was 20M. We also recognized 5M in professional services. What is our total recognized revenue for the year? Note: ARR is a forward-looking metric; our actual recognized subscription revenue was only 120M.", "true_revenue": 145.0},
    {"id": 14, "text": "A multi-year contract was signed for 36M over 36 months. We recognize revenue monthly. The contract started on October 1st. What is the recognized revenue for this first calendar year?", "true_revenue": 3.0},
    {"id": 15, "text": "Gross sales were 1,000,000 units at $50 each. We had a return rate of 5%. We also gave a 10% rebate on 200,000 of those units. Calculate net revenue in millions.", "true_revenue": 46.5}
]

def run_calibration():
    # Using Haiku to intentionally demonstrate high-confidence errors on complex reasoning
    llm = ChatAnthropic(model="claude-haiku-4-5", temperature=0)
    structured_llm = llm.with_structured_output(FinancialExtraction)
    
    print("=" * 80)
    print("🧪 RUNNING FINANCIAL EXTRACTION PIPELINE")
    print("=" * 80)
    
    results = []
    
    for item in DATASET:
        messages = [
            SystemMessage(content="Extract the core/final revenue from the text. Follow all explicit mathematical instructions or definitions in the text. Output the value in millions (e.g. 45.2). Provide a confidence score from 0.0 to 1.0."),
            HumanMessage(content=item["text"])
        ]
        
        # We use a try/except in case the LLM fails to parse
        try:
            extraction = structured_llm.invoke(messages)
            # Floating point comparison safely
            is_correct = abs(extraction.revenue - item["true_revenue"]) < 0.01
            
            results.append({
                "id": item["id"],
                "true": item["true_revenue"],
                "pred": extraction.revenue,
                "conf": extraction.confidence_score,
                "correct": is_correct
            })
            
            status = "✅" if is_correct else "❌"
            print(f"ID {item['id']} | True: {item['true_revenue']:>5.2f} | Pred: {extraction.revenue:>5.2f} | Conf: {extraction.confidence_score:.2f} | {status}")
        except Exception as e:
            print(f"ID {item['id']} | ❌ Error extracting: {e}")

    # --- CALIBRATION ANALYSIS ---
    print("\n" + "=" * 80)
    print("📊 CALIBRATION ANALYSIS: Validating the 0.85 Arbitrary Threshold")
    print("=" * 80)
    
    threshold_arbitrary = 0.85
    auto_approved = [r for r in results if r["conf"] >= threshold_arbitrary]
    
    if auto_approved:
        errors_in_approved = [r for r in auto_approved if not r["correct"]]
        accuracy = (len(auto_approved) - len(errors_in_approved)) / len(auto_approved) * 100
        
        print(f"Using arbitrary threshold {threshold_arbitrary}:")
        print(f"- Sent to auto-approval: {len(auto_approved)} fields")
        print(f"- Errors that slipped through: {len(errors_in_approved)}")
        print(f"- Accuracy of auto-approved fields: {accuracy:.1f}%")
        
        if errors_in_approved:
            print("\n🚨 CONCLUSION: The 0.85 threshold failed!")
            print("Reviewers are complaining because high-confidence errors are slipping through.")
            print("Confidence scores from AI models are relative signals, not absolute probabilities of correctness.")
            print("Without validating threshold choices against labeled data, there is no guarantee that high-confidence predictions are accurate.")
        else:
            print("\n(Note: The model got everything right above 0.85 in this small test run, but in production, arbitrary thresholds are dangerous!)")
    
    # Find empirical threshold
    print("\n" + "=" * 80)
    print("🎯 FINDING EMPIRICAL THRESHOLD FOR 100% RELIABILITY")
    print("=" * 80)
    
    incorrect_results = [r for r in results if not r["correct"]]
    if incorrect_results:
        highest_incorrect_conf = max(r["conf"] for r in incorrect_results)
        empirical_threshold = highest_incorrect_conf + 0.01
        print(f"The model made mistakes with confidence as high as {highest_incorrect_conf:.2f}.")
        print(f"To guarantee 100% accuracy on auto-approved items based on this ground truth labeled data,")
        print(f"the threshold MUST be calibrated to at least {empirical_threshold:.2f}.")
    else:
        print("The model made no mistakes on this tiny dataset. A much larger ground truth dataset is needed to find the true calibrated threshold.")

if __name__ == "__main__":
    run_calibration()
