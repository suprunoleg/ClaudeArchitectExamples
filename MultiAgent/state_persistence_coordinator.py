"""
State Persistence Coordinator

Shows how a coordinator agent can save and load its internal state to pause
and resume complex workflows. This is vital for long-running workflows that
might be interrupted by user input or transient network failures.
"""

import os
import json
import sys
import argparse
import time
from anthropic import Anthropic
from dotenv import load_dotenv

# =====================================================================
# State Persistence Coordinator Example
# Demonstrates how a coordinator can use a manifest to recover state
# after a crash, injecting cached findings into remaining subagents
# instead of re-running expensive API calls.
# =====================================================================

load_dotenv()

WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "workspace")
MANIFEST_FILE = os.path.join(WORKSPACE_DIR, "manifest.json")

def load_manifest() -> dict:
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_manifest(manifest: dict):
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)

def save_findings(agent_id: str, content: str):
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    filepath = os.path.join(WORKSPACE_DIR, f"{agent_id}_findings.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def load_findings(agent_id: str) -> str:
    filepath = os.path.join(WORKSPACE_DIR, f"{agent_id}_findings.txt")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def run_subagent(client: Anthropic, agent_id: str, prompt: str) -> str:
    print(f"🤖 [API CALL] Subagent '{agent_id}' is executing its task...")
    
    # Simulate some processing time for realism
    time.sleep(1)
    
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

def main():
    parser = argparse.ArgumentParser(description="Multi-Agent State Persistence Coordinator")
    parser.add_argument("--simulate-crash", action="store_true", help="Simulate a crash after Agent 3")
    parser.add_argument("--reset", action="store_true", help="Clear the workspace and start fresh")
    args = parser.parse_args()
    
    if args.reset:
        print("🧹 Clearing workspace...")
        if os.path.exists(WORKSPACE_DIR):
            for file in os.listdir(WORKSPACE_DIR):
                os.remove(os.path.join(WORKSPACE_DIR, file))
        print("✅ Workspace cleared. Ready for fresh execution.\n")
    
    client = Anthropic()
    
    # Define our 5 subagents
    subagents = [
        {"id": "agent_1_market", "prompt": "Analyze the market sizing and give a 2-sentence summary."},
        {"id": "agent_2_competitors", "prompt": "Analyze competitor pricing and give a 2-sentence summary."},
        {"id": "agent_3_regulatory", "prompt": "Analyze EU regulatory risks and give a 2-sentence summary."},
        {"id": "agent_4_sentiment", "prompt": "Analyze customer sentiment and give a 2-sentence summary."},
        {"id": "agent_5_distribution", "prompt": "Analyze distribution channels and give a 2-sentence summary."}
    ]
    
    # Load state from manifest
    manifest = load_manifest()
    findings_cache = {}
    
    print("🚀 Starting Coordinator Process...\n")
    
    for i, agent in enumerate(subagents, 1):
        agent_id = agent["id"]
        
        # 1. State Recovery Check
        if manifest.get(agent_id) == "COMPLETED":
            print(f"✅ [CACHE HIT] {agent_id} already completed! Loading findings from disk, skipping API call.")
            findings_cache[agent_id] = load_findings(agent_id)
            continue
            
        # 2. Execution
        print(f"⏳ [PENDING] {agent_id} has not completed. Preparing to run...")
        
        # Inject previously recovered state into the prompt of the remaining agents
        # (Demonstrating the exact requirement: "inject their findings into the remaining prompts")
        context_prompt = agent["prompt"]
        if findings_cache:
            context_injection = "\n\nContext from previously completed agents:\n"
            for prev_id, prev_findings in findings_cache.items():
                context_injection += f"- {prev_id}: {prev_findings}\n"
            context_prompt += context_injection
            
        result = run_subagent(client, agent_id, context_prompt)
        
        # 3. State Persistence
        save_findings(agent_id, result)
        manifest[agent_id] = "COMPLETED"
        save_manifest(manifest)
        
        findings_cache[agent_id] = result
        print(f"💾 [SAVED] {agent_id} completed and exported findings to disk.\n")
        
        # 4. Crash Simulation
        if args.simulate_crash and i == 3:
            print("🔥 CRITICAL ERROR: Coordinator process crashed unexpectedly after Agent 3!")
            print("Exiting immediately without finishing remaining agents...")
            sys.exit(1)
            
    print("=================================================================")
    print("🎉 All subagents have successfully completed!")
    print("Coordinator is now aggregating all findings into the final report.")
    print("=================================================================\n")
    
    for agent_id, result in findings_cache.items():
        print(f"[{agent_id.upper()}]:\n{result}\n")
        
if __name__ == "__main__":
    main()
