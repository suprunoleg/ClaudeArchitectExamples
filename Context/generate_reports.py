import os
import random

def generate_filler(topic: str, length: int) -> str:
    adjectives = ["robust", "dynamic", "standard", "marginal", "significant", "underwhelming", "consistent", "volatile", "predictable"]
    nouns = ["growth", "metrics", "indicators", "trends", "patterns", "outcomes", "trajectories", "developments", "shifts"]
    verbs = ["shows", "indicates", "suggests", "highlights", "demonstrates", "reveals", "points to", "confirms", "reflects"]
    buzzwords = ["synergy", "paradigm", "bandwidth", "alignment", "ecosystem", "optimization", "scalability", "integration", "innovation"]
    
    sentences = []
    for _ in range(length):
        sentence = f"The {topic} {random.choice(nouns)} {random.choice(verbs)} {random.choice(adjectives)} {random.choice(buzzwords)}."
        sentences.append(sentence)
    
    return " ".join(sentences)

def create_reports():
    base_dir = os.path.dirname(__file__)
    reports_dir = os.path.join(base_dir, "reports_data")
    os.makedirs(reports_dir, exist_ok=True)
    
    # Report 1: Market Sizing
    content1 = f"Market Sizing Report\n\n{generate_filler('market', 2600)}\n\nThe total addressable market is $50B.\n\n{generate_filler('market', 2600)}"
    with open(os.path.join(reports_dir, "report_1_market_sizing.txt"), "w", encoding="utf-8") as f:
        f.write(content1)
        
    # Report 2: Competitor Pricing
    content2 = f"Competitor Pricing\n\n{generate_filler('pricing', 2600)}\n\nCompetitors charge $10/mo.\n\n{generate_filler('pricing', 2600)}"
    with open(os.path.join(reports_dir, "report_2_competitor_pricing.txt"), "w", encoding="utf-8") as f:
        f.write(content2)
        
    # Report 3: Regulatory Risk (The Needle)
    content3 = f"Regulatory Risk\n\n{generate_filler('regulation', 1300)}\n\nCRITICAL_REGULATORY_RISK: The new EU data laws will ban our core product next year.\n\n{generate_filler('regulation', 1300)}"
    with open(os.path.join(reports_dir, "report_3_regulatory_risk.txt"), "w", encoding="utf-8") as f:
        f.write(content3)
        
    # Report 4: Customer Sentiment
    content4 = f"Customer Sentiment\n\n{generate_filler('sentiment', 2600)}\n\nCustomers love the UI.\n\n{generate_filler('sentiment', 2600)}"
    with open(os.path.join(reports_dir, "report_4_customer_sentiment.txt"), "w", encoding="utf-8") as f:
        f.write(content4)
        
    # Report 5: Distribution Channels
    content5 = f"Distribution Channels\n\n{generate_filler('distribution', 2600)}\n\nDirect sales are best.\n\n{generate_filler('distribution', 2600)}"
    with open(os.path.join(reports_dir, "report_5_distribution_channels.txt"), "w", encoding="utf-8") as f:
        f.write(content5)
        
    print(f"✅ Generated 5 massive report files in: {reports_dir}")

if __name__ == "__main__":
    create_reports()
