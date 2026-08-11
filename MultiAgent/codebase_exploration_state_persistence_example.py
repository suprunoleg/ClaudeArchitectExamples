"""
Stateful Codebase Exploration

Demonstrates an agent traversing a codebase while persisting its exploration
state, preventing redundant work across sessions. Tracking visited files and
outstanding questions allows the agent to pause and safely resume long-running
codebase audits.
"""

import os
import json
import sys
import argparse
import time
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

# =====================================================================
# Codebase Exploration State Persistence Example
# Demonstrates "structured state persistence" where agents export 
# progress to a known location, and the coordinator loads a manifest 
# to resume after a simulated process crash without restarting from zero.
# =====================================================================

WORKSPACE_DIR = os.path.join(os.path.dirname(__file__), "exploration_state")
MANIFEST_FILE = os.path.join(WORKSPACE_DIR, "exploration_manifest.json")

def load_manifest() -> dict:
    """Loads the manifest of agent states from a known file location on resume."""
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_manifest(manifest: dict):
    """Saves the updated manifest after an agent successfully completes its slice."""
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)

def save_agent_state(module_name: str, findings: str):
    """Each agent exports its state (findings) to a known file location as it progresses."""
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    filepath = os.path.join(WORKSPACE_DIR, f"{module_name}_state.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(findings)

def load_agent_state(module_name: str) -> str:
    """The coordinator loads previously saved state for context injection."""
    filepath = os.path.join(WORKSPACE_DIR, f"{module_name}_state.txt")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def explore_module(module_name: str, previous_context: str) -> str:
    """Simulates a sub-agent exploring a large module over time."""
    print(f" [AGENT WORKING] Exploring codebase module: '{module_name}'...")
    
    # Simulating long-running API calls/exploration
    time.sleep(1.5)
    
    try:
        # We pass context from previous modules to give the agent a unified view
        prompt = f"Analyze the {module_name} module. Prior context: {previous_context}"
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        # Fallback for dummy keys or missing API keys during testing
        return f"Mocked architecture findings for {module_name} (dependencies mapped)."

def run_exploration():
    parser = argparse.ArgumentParser(description="Large Codebase Exploration with State Persistence")
    parser.add_argument("--simulate-crash", action="store_true", help="Simulate a crash halfway through")
    parser.add_argument("--reset", action="store_true", help="Clear the persistence directory and start fresh")
    args = parser.parse_args()
    
    if args.reset:
        print(" Clearing previous state and manifest...")
        if os.path.exists(WORKSPACE_DIR):
            for file in os.listdir(WORKSPACE_DIR):
                os.remove(os.path.join(WORKSPACE_DIR, file))
        print("Ready for fresh execution.\n")
    
    # 1. Define the large codebase modules to explore (takes hours in real life)
    codebase_modules = [
        "AuthenticationService",
        "PaymentGateway",
        "UserProfiles",
        "NotificationQueue",
        "ReportingEngine"
    ]
    
    # 2. Coordinator loads manifest of agent states on resume
    manifest = load_manifest()
    
    # We will aggregate previously explored knowledge to give context to subsequent modules
    accumulated_context = ""
    
    print(f"{'='*80}")
    print("LARGE CODEBASE EXPLORATION ORCHESTRATOR")
    print(f"{'='*80}\n")
    
    for i, module in enumerate(codebase_modules, 1):
        # Check Manifest
        if manifest.get(module) == "COMPLETED":
            print(f"[CACHE HIT] Module '{module}' was already explored. Resuming from manifest.")
            state_data = load_agent_state(module)
            accumulated_context += f" [{module}: {state_data}] "
            continue
            
        # Agent execution
        print(f" [PENDING] Module '{module}' needs exploration...")
        findings = explore_module(module, accumulated_context)
        
        # Each agent exports its state to a known file location as it progresses
        save_agent_state(module, findings)
        
        # Coordinator updates the manifest
        manifest[module] = "COMPLETED"
        save_manifest(manifest)
        
        accumulated_context += f" [{module}: {findings}] "
        print(f" [STATE EXPORTED] Progress for '{module}' saved to disk.\n")
        
        # Simulate an unexpected process crash (e.g. OOM, network failure)
        if args.simulate_crash and i == 3:
            print(" CRITICAL FAILURE: Process crashed unexpectedly while exploring large codebase!")
            print("To see structured state persistence in action, run this script again WITHOUT --simulate-crash.")
            sys.exit(1)
            
    print(f"{'='*80}")
    print("ALL MODULES EXPLORED SUCCESSFULLY")
    print("The coordinator did not have to start from zero thanks to the manifest!")
    print(f"{'='*80}\n")
    
    print(" SYNTHESIZING FINAL REPORT...")
    try:
        final_prompt = f"You are a lead architect. Synthesize the following module findings into a single cohesive architectural summary:\n\n{accumulated_context}"
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=500,
            messages=[{"role": "user", "content": final_prompt}]
        )
        final_report = response.content[0].text
    except Exception as e:
        final_report = "Mocked final synthesized architecture report."
        
    # Prevent Windows cp1252 print errors if Claude uses emojis or special quotes
    safe_report = final_report.encode('cp1252', errors='replace').decode('cp1252')
    print(f"\nFINAL ARCHITECTURE REPORT:\n{'-'*30}\n{safe_report}\n{'-'*30}")

if __name__ == "__main__":
    run_exploration()
