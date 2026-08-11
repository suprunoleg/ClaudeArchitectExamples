"""
Lost in the Middle Mitigation

Demonstrates strategies to mitigate the "lost in the middle" phenomenon where
LLMs struggle to recall information placed in the middle of long contexts.
Techniques like prompt re-ordering and attention-forcing cues are used to
ensure the model evaluates all provided data.
"""

import os
import random
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

# =====================================================================
# 1. Mock Subagent Data
# =====================================================================
# To simulate the "Lost in the Middle" phenomenon reliably without burning 
# 100k tokens, we pack a very specific flag ("CRITICAL_REGULATORY_RISK: True") 
# into the exact middle section, surrounded by lots of distracting filler text.

def load_reports_from_disk():
    base_dir = os.path.dirname(__file__)
    reports_dir = os.path.join(base_dir, "reports_data")
    
    files = [
        ("Market Sizing", "report_1_market_sizing.txt"),
        ("Competitor Pricing", "report_2_competitor_pricing.txt"),
        ("Regulatory Risk", "report_3_regulatory_risk.txt"),
        ("Customer Sentiment", "report_4_customer_sentiment.txt"),
        ("Distribution Channels", "report_5_distribution_channels.txt")
    ]
    
    loaded_reports = []
    for title, filename in files:
        filepath = os.path.join(reports_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            loaded_reports.append((title, f.read()))
            
    return loaded_reports

reports = load_reports_from_disk()


# =====================================================================
# 2. Architecting the Prompts
# =====================================================================

def build_bad_aggregated_document():
    """Anti-Pattern: Concatenates everything into a massive wall of text."""
    doc = ""
    for _, text in reports:
        doc += text + "\n\n"
    return doc


def build_good_aggregated_document():
    """
    Best Practice (Subdomain 5.1): 
    1. Top-load a Key Findings Summary.
    2. Use explicit XML section headers for the detailed content.
    """
    key_findings = [
        "- Market Sizing: TAM is $50B.",
        "- Competitor Pricing: Average competitor charges $10/mo.",
        "- Regulatory Risk: WARNING - EU data laws threaten product viability.",
        "- Customer Sentiment: Positive UI feedback.",
        "- Distribution Channels: Direct sales recommended."
    ]
    
    doc = "<key_findings_summary>\n"
    doc += "\n".join(key_findings)
    doc += "\n</key_findings_summary>\n\n"
    
    doc += "<detailed_reports>\n"
    for i, (title, text) in enumerate(reports, 1):
        doc += f"<report index=\"{i}\">\n  <title>{title}</title>\n  <content>\n{text}\n  </content>\n</report>\n\n"
    doc += "</detailed_reports>"
    
    return doc


# =====================================================================
# 3. Execution and Comparison
# =====================================================================
def run_synthesis(document: str, strategy_name: str):
    print(f"\n" + "="*80)
    print(f"🧠 RUNNING SYNTHESIS WITH: {strategy_name}")
    print("="*80)
    
    system_prompt = "You are a Chief Strategy Officer. Synthesize the provided research document into a brief 3-bullet point executive summary. You MUST capture the most critical existential threats to the business."
    
    user_prompt = f"Here is the aggregated report to analyze:\n\n<report_content>\n{document}\n</report_content>"
    
    # Save the prompt to a file so we can inspect what the model sees
    filename = strategy_name.split()[0].lower() + "_pattern_prompt.txt"
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"--- SYSTEM PROMPT ---\n{system_prompt}\n\n--- USER PROMPT ---\n{user_prompt}")
    print(f"💾 Saved full context to: {filepath}")
    
    response = client.messages.create(
        model="claude-haiku-4-5", # Using haiku to intentionally exacerbate context-window attention issues
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    
    result = response.content[0].text
    print(result)
    
    # Analyze if the regulatory risk survived
    if "EU" in result or "regulatory" in result.lower() or "threat" in result.lower() or "ban" in result.lower():
        print("\n✅ RESULT: Regulatory Risk successfully surfaced!")
    else:
        print("\n❌ RESULT: LOST IN THE MIDDLE! Regulatory Risk was completely omitted.")


if __name__ == "__main__":
    print("Preparing documents...")
    
    # 1. Test the Bad Pattern
    bad_doc = build_bad_aggregated_document()
    run_synthesis(bad_doc, "Bad Pattern (Wall of Text)")
    
    # 2. Test the Good Pattern (The Fix)
    good_doc = build_good_aggregated_document()
    run_synthesis(good_doc, "Good Pattern (Top-Loaded Summary & XML Headers)")
