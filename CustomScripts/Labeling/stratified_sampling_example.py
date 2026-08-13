"""
Stratified Sampling for Calibration

Demonstrates how to use stratified sampling to select a representative mix of 
cases for human review/calibration, avoiding the pitfall of rare sub-populations 
being under-represented by purely random sampling.
"""

import os
import sys
import random
from collections import defaultdict
from dotenv import load_dotenv
from anthropic import Anthropic

# Configure stdout to support emojis/UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"


# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


def generate_mock_cases(num_cases=1000):
    """
    Generates a mock dataset of customer support cases with heavily skewed distributions.
    E.g. 80% Consumer, 15% SMB, 5% Enterprise.
    And 70% High confidence, 20% Medium, 10% Low.
    """
    cases = []
    for i in range(num_cases):
        # Skewed segment distribution
        rand_seg = random.random()
        if rand_seg < 0.8:
            segment = "Consumer"
        elif rand_seg < 0.95:
            segment = "SMB"
        else:
            segment = "Enterprise"
            
        # Skewed confidence distribution
        rand_conf = random.random()
        if rand_conf < 0.7:
            confidence = "High"
        elif rand_conf < 0.9:
            confidence = "Medium"
        else:
            confidence = "Low"
            
        cases.append({
            "case_id": f"CASE_{i:04d}",
            "segment": segment,
            "confidence": confidence
        })
    return cases


def random_sampling(cases, sample_size=100):
    """Simple random sampling. May completely miss rare strata like Enterprise+Low."""
    return random.sample(cases, sample_size)


def stratified_sampling(cases, sample_size=100):
    """
    Stratified sampling by segment and confidence bucket.
    Ensures proportional representation across all sub-populations.
    """
    # 1. Group by strata (segment + confidence)
    strata = defaultdict(list)
    for case in cases:
        key = (case["segment"], case["confidence"])
        strata[key].append(case)
        
    total_cases = len(cases)
    sampled_cases = []
    
    # 2. Sample proportionally from each stratum
    for key, items in strata.items():
        # Calculate proportion this stratum represents in the total dataset
        proportion = len(items) / total_cases
        
        # Determine how many items to sample for this stratum
        # We use max(1, ...) to ensure even the rarest stratum gets at least 1 sample 
        # if it exists, which is crucial for calibration!
        stratum_sample_size = max(1, int(round(proportion * sample_size)))
        
        # Don't sample more than we actually have
        stratum_sample_size = min(stratum_sample_size, len(items))
        
        # Sample randomly from within this specific stratum
        sampled_cases.extend(random.sample(items, stratum_sample_size))
        
    # Trim down to exact sample_size if rounding caused us to go slightly over
    if len(sampled_cases) > sample_size:
        sampled_cases = random.sample(sampled_cases, sample_size)
        
    return sampled_cases


def analyze_sample(sample_name, sampled_cases):
    """Helper to print the distribution of a sample."""
    distribution = defaultdict(int)
    for case in sampled_cases:
        key = f"{case['segment']} | {case['confidence']}"
        distribution[key] += 1
        
    print(f"\n--- {sample_name} (Size: {len(sampled_cases)}) ---")
    
    # Sort for consistent display
    for key in sorted(distribution.keys()):
        print(f"  {key:<22}: {distribution[key]} cases")
        
    # Highlight missing rare combinations
    print(f"  Total unique combinations: {len(distribution)}")


def calibrate_with_claude(sampled_case):
    """
    Demonstrates sending a sampled case to Claude for calibration/review.
    """
    print(f"\nSending {sampled_case['case_id']} ({sampled_case['segment']} | {sampled_case['confidence']}) to Claude for review...")
    
    client = Anthropic()
    prompt = f"""
    Please review the following customer support case for calibration.
    Case ID: {sampled_case['case_id']}
    Customer Segment: {sampled_case['segment']}
    Model Confidence: {sampled_case['confidence']}
    
    Evaluate if the model's confidence aligns with the expected difficulty of this segment.
    """
    
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    
    print(f"Claude's Calibration Review:\n{response.content[0].text}\n")


def main():
    print("="*60)
    print("STRATIFIED RANDOM SAMPLING vs. PURE RANDOM SAMPLING")
    print("="*60)
    print("Scenario: We have 10,000 production customer support cases.")
    print("We want to route exactly 100 cases to human review for calibration.")
    print("If we use pure random sampling, rare segments (e.g. Enterprise)")
    print("or low-confidence buckets might be completely missed.")
    
    random.seed(42) # For reproducible output
    
    # Generate 10,000 cases with a realistic, skewed distribution
    all_cases = generate_mock_cases(10000)
    
    # Perform pure random sampling
    random_sample = random_sampling(all_cases, sample_size=100)
    
    # Perform stratified sampling
    stratified_sample = stratified_sampling(all_cases, sample_size=100)
    
    # Analyze the difference
    print("\n[ANALYSIS]")
    analyze_sample("Pure Random Sampling", random_sample)
    
    analyze_sample("Stratified Sampling", stratified_sample)
    
    print("\n[CONCLUSION]")
    print("Notice how rare combinations (like 'Enterprise | Low') might be completely")
    print("missed in the Pure Random Sample. Stratified sampling guarantees that")
    print("EVERY stratum (sub-population) is represented proportionally, ensuring")
    print("our calibration metrics are accurate across the board!")

    print("\n" + "="*60)
    print("STEP 2: CALIBRATION REVIEW WITH CLAUDE")
    print("="*60)
    print("Now that we have a perfectly representative stratified sample,")
    print("we can route these cases to Claude (or a human) for quality calibration.")
    
    # Find that rare Enterprise | Low case we captured to demonstrate!
    rare_case = next(c for c in stratified_sample if c["segment"] == "Enterprise" and c["confidence"] == "Low")
    calibrate_with_claude(rare_case)


if __name__ == "__main__":
    main()
