"""
Centralized Coordinator Agent

Implements a hierarchical multi-agent pattern where a central coordinator
routes tasks to specialized sub-agents and aggregates results. This separation
of concerns allows each sub-agent to have a highly focused prompt, improving
overall system accuracy.
"""

import os
import time
from dotenv import load_dotenv
from anthropic import Anthropic

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"


# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

# =====================================================================
# 1. The Dumb Subagents (The "Spokes")
# =====================================================================
# Notice how the subagents have NO try/except blocks, NO retry logic, 
# and NO custom print statements for logging. They just return data.

class ResearcherSubagent:
    def __init__(self, simulate_transient_failure=False):
        self.name = "Researcher"
        self.simulate_transient_failure = simulate_transient_failure
        self.attempts = 0

    def generate_response(self, prompt: str) -> str:
        self.attempts += 1
        
        # We simulate a transient network error on the first attempt 
        # to prove the Coordinator handles it centrally.
        if self.simulate_transient_failure and self.attempts == 1:
            raise TimeoutError("Researcher API connection timed out.")
            
        return client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=300,
            system="You are a researcher. Summarize the requested topic briefly.",
            messages=[{"role": "user", "content": prompt}]
        ).content[0].text


class AnalystSubagent:
    def __init__(self):
        self.name = "Analyst"

    def generate_response(self, research_data: str) -> str:
        return client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=300,
            system="You are an analyst. Extract the most important metric/fact from the research.",
            messages=[{"role": "user", "content": research_data}]
        ).content[0].text


# =====================================================================
# 2. The Centralized Coordinator (The "Hub")
# =====================================================================
class CentralCoordinator:
    def __init__(self):
        self.max_retries = 3

    def log(self, agent_name: str, message_type: str, message: str):
        """Unified logging format for the entire system."""
        print(f"[COORDINATOR LOG] [{agent_name}] [{message_type.upper()}] - {message}")

    def execute_subagent_with_retry(self, agent, prompt: str) -> str:
        """Centralized retry and exponential backoff logic applied to all subagents."""
        for attempt in range(self.max_retries):
            try:
                self.log(agent.name, "execution", f"Starting attempt {attempt + 1}...")
                result = agent.generate_response(prompt)
                self.log(agent.name, "success", "Response generated successfully.")
                return result
                
            except TimeoutError as e:
                backoff = 2 ** attempt
                self.log(agent.name, "error", f"Transient error caught: {e}")
                
                if attempt == self.max_retries - 1:
                    self.log(agent.name, "fatal", "Max retries reached. Aborting subtask.")
                    raise e
                    
                self.log(agent.name, "retry", f"Applying exponential backoff. Waiting {backoff}s...")
                time.sleep(backoff)
            except Exception as e:
                # Catch-all for non-transient errors (hard fail)
                self.log(agent.name, "fatal", f"Unexpected error: {e}")
                raise e

    def run_research_pipeline(self, topic: str):
        """Orchestrates the multi-agent workflow."""
        print("=" * 80)
        print("🔄 STARTING CENTRALIZED COORDINATOR PIPELINE")
        print("=" * 80)
        
        # Instantiate subagents (We force the researcher to fail once to demo the retry logic)
        researcher = ResearcherSubagent(simulate_transient_failure=True)
        analyst = AnalystSubagent()

        # Step 1: Research
        self.log("Coordinator", "info", f"Dispatching topic to Researcher: '{topic}'")
        try:
            research_data = self.execute_subagent_with_retry(researcher, topic)
            print(f"\n--- RESEARCH DATA ---\n{research_data}\n---------------------\n")
        except Exception as e:
            self.log("Coordinator", "fatal", "Pipeline halted due to Researcher failure.")
            return

        # Step 2: Analysis
        self.log("Coordinator", "info", "Dispatching research data to Analyst.")
        try:
            analysis_data = self.execute_subagent_with_retry(analyst, research_data)
            print(f"\n--- FINAL ANALYSIS ---\n{analysis_data}\n----------------------\n")
        except Exception as e:
            self.log("Coordinator", "fatal", "Pipeline halted due to Analyst failure.")
            return
            
        self.log("Coordinator", "success", "Pipeline completed successfully!")

if __name__ == "__main__":
    coordinator = CentralCoordinator()
    coordinator.run_research_pipeline("The population growth of Tokyo over the last 50 years.")
