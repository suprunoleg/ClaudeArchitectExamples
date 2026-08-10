import os
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

def generate_filler(topic: str, length: int = 50) -> str:
    return f"The {topic} analysis shows standard positive growth indicators. " * length

market_sizing = f"Market Sizing Report\n{generate_filler('market')}\nThe total addressable market is $50B.\n{generate_filler('market')}"
competitor_pricing = f"Competitor Pricing\n{generate_filler('pricing')}\nCompetitors charge $10/mo.\n{generate_filler('pricing')}"

# THE MIDDLE SECTION (Vulnerable to being ignored)
regulatory_risk = f"Regulatory Risk\n{generate_filler('regulation', 20)}\nCRITICAL_REGULATORY_RISK: The new EU data laws will ban our core product next year.\n{generate_filler('regulation', 20)}"

customer_sentiment = f"Customer Sentiment\n{generate_filler('sentiment')}\nCustomers love the UI.\n{generate_filler('sentiment')}"
distribution = f"Distribution Channels\n{generate_filler('distribution')}\nDirect sales are best.\n{generate_filler('distribution')}"

reports = [
    ("Market Sizing", market_sizing),
    ("Competitor Pricing", competitor_pricing),
    ("Regulatory Risk", regulatory_risk),
    ("Customer Sentiment", customer_sentiment),
    ("Distribution Channels", distribution)
]


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
    
    response = client.messages.create(
        model="claude-sonnet-4-5", # Model changed per project rules
        max_tokens=300,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Here is the aggregated report to analyze:\n\n<report_content>\n{document}\n</report_content>"}]
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
