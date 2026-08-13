"""
Tree-Structured Synthesis Example

This example demonstrates the enterprise architectural pattern for addressing the
"Lost in the Middle" context problem during Multi-Agent Synthesis.

Problem:
A Multi-Agent workflow delegates research to 12 subagents. Each produces a 5KB
finding. Concatenating all findings creates a 60KB payload. When the central 
synthesizer model processes this, mid-list findings are often ignored or 
underrepresented due to LLM attention weighting (the "Lost in the Middle" effect).

Solution:
A tree-structured (hierarchical) aggregator. Instead of one massive synthesis step,
the system groups the 12 findings into batches (e.g., 4 groups of 3). 
The model summarizes each group first, bounding the context window to ~15KB per call,
keeping everything in the high-attention zone. Finally, the model synthesizes the 
4 intermediate summaries into the final report. This preserves the multi-agent
pattern while eliminating lost-in-the-middle exposure at each level.
"""

import os
import time
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load API key
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

def generate_mock_findings():
    """Simulates 12 subagents returning detailed findings."""
    print("🤖 Subagents are gathering data...")
    # In a real scenario, these would be 5KB each.
    # We use distinct facts so we can verify they made it into the final report.
    findings = [
        "Finding 1 (Q1 Sales): North America region grew by 15% due to the new product launch.",
        "Finding 2 (Q1 Marketing): Ad spend was optimized, reducing CPA by $12.",
        "Finding 3 (Q1 Operations): Supply chain delays in Asia caused a 3-day average shipping delay.",
        
        "Finding 4 (Q2 Sales): Europe expansion resulted in 2M EUR in net new ARR.",
        "Finding 5 (Q2 Marketing): The summer campaign went viral, tripling social media engagement.",
        "Finding 6 (Q2 Operations): A new warehouse in Berlin reduced EU shipping times by 40%.",
        
        "Finding 7 (Q3 Sales): Churn spiked to 5% in the Enterprise segment due to missing features.",
        "Finding 8 (Q3 Marketing): Re-engagement email sequence recovered 15% of at-risk accounts.",
        "Finding 9 (Q3 Operations): Server outage on Black Friday resulted in $50k SLA penalties.",
        
        "Finding 10 (Q4 Sales): Record-breaking holiday sales, hitting 120% of the quarterly quota.",
        "Finding 11 (Q4 Marketing): Influencer partnerships drove 40% of Q4 acquisition.",
        "Finding 12 (Q4 Operations): Successfully migrated to the new cloud infrastructure with zero downtime."
    ]
    
    # Simulate some delay to make it feel like real agent work
    time.sleep(1)
    return findings

def summarize_batch(llm, batch_id, findings_chunk):
    """Summarizes a small batch of findings (keeping context size small)."""
    text = "\n\n".join(findings_chunk)
    print(f"   [Intermediate] Synthesizing Batch {batch_id} (Length: {len(findings_chunk)} findings)...")
    
    messages = [
        SystemMessage(content="You are a data analyst. Concisely summarize the following findings. Extract the key metrics and facts."),
        HumanMessage(content=text)
    ]
    
    response = llm.invoke(messages)
    return response.content

def run_tree_synthesis():
    print("=" * 70)
    print("🌳 TREE-STRUCTURED SYNTHESIS PIPELINE")
    print("=" * 70)
    
    llm = ChatAnthropic(model=DEFAULT_MODEL, temperature=0.2)
    findings = generate_mock_findings()
    
    print(f"\n✅ Generated {len(findings)} raw findings from subagents.")
    
    # Step 1: Intermediate Synthesis (Group by 3)
    print("\n🔄 LEVEL 1: Intermediate Synthesis (Chunking to avoid 'Lost in the Middle')")
    
    chunk_size = 3
    intermediate_summaries = []
    
    for i in range(0, len(findings), chunk_size):
        chunk = findings[i:i + chunk_size]
        batch_id = (i // chunk_size) + 1
        summary = summarize_batch(llm, batch_id, chunk)
        intermediate_summaries.append(f"--- BATCH {batch_id} SUMMARY ---\n{summary}")
        
    print("\n✅ Level 1 Synthesis Complete. Reduced 12 findings down to 4 dense summaries.")
    
    # Step 2: Final Synthesis
    print("\n🔄 LEVEL 2: Final Synthesis (Combining the intermediate summaries)")
    
    combined_text = "\n\n".join(intermediate_summaries)
    
    messages = [
        SystemMessage(content="You are a Lead Strategic Analyst. Read the following intermediate regional/quarterly summaries and produce a cohesive final executive report. Ensure that facts from the middle of the year (Q2/Q3) are explicitly included. Use bullet points for key achievements and challenges."),
        HumanMessage(content=combined_text)
    ]
    
    final_report = llm.invoke(messages)
    
    print("\n" + "=" * 70)
    print("📑 FINAL EXECUTIVE REPORT")
    print("=" * 70)
    print(final_report.content)
    print("=" * 70)
    print("\n💡 Architecture Note: Because the final synthesis only looked at 4 dense summaries")
    print("instead of 12 verbose findings, the middle-list data (Q2/Q3) received full attention weight.")

if __name__ == "__main__":
    run_tree_synthesis()
