import os
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

# =====================================================================
# 1. The Subagent (File Reviewer)
# =====================================================================
def review_single_file(file_path: str) -> dict:
    """
    Simulates a subagent reviewing a single file. 
    In a real workflow, this would make an API call to Claude (e.g., claude-haiku) 
    for each individual file. We mock the API call here to avoid making 
    200 simultaneous real API calls in this demonstration.
    """
    # Simulate API latency (100ms - 300ms)
    time.sleep(random.uniform(0.1, 0.3)) 
    
    # Randomly generate some "findings" (10% chance of finding an error)
    has_error = random.random() < 0.10 
    
    if has_error:
        status = "CHANGES_REQUESTED"
        
        # Pick a random mock issue
        issues = [
            "Found potential SQL injection vulnerability. Needs parameterized queries.",
            "Legacy API usage detected. Please update to v2 endpoint.",
            "Missing unit test coverage for the error handling block.",
            "Hardcoded credentials found. Move to environment variables."
        ]
        comments = random.choice(issues)
    else:
        status = "APPROVED"
        comments = "Code meets migration standards."
        
    return {
        "file": file_path,
        "status": status,
        "comments": comments
    }


# =====================================================================
# 2. The Orchestration Workflow Tool (Deterministic Script)
# =====================================================================
class MigrationReviewWorkflow:
    def __init__(self, max_concurrent_workers: int = 30):
        self.max_workers = max_concurrent_workers

    def run_large_scale_review(self, files_to_review: list[str]):
        print(f"\n{'='*80}")
        print(f"SCRIPTED WORKFLOW ORCHESTRATION ({len(files_to_review)} FILES)")
        print(f"{'='*80}")
        print("Instead of having an LLM coordinate 200 files turn-by-turn (which would")
        print("hit context limits, lose track, and cost a fortune), we use a deterministic")
        print("Python script to orchestrate the subagents in parallel.\n")
        
        start_time = time.time()
        
        results = []
        issues_found = []
        
        print(f"Processing {len(files_to_review)} files with {self.max_workers} concurrent subagents...")
        
        # -----------------------------------------------------------------
        # STEP 1: Parallel Execution via Script (Not an LLM orchestrator)
        # -----------------------------------------------------------------
        # ThreadPoolExecutor is our "workflow tool" coordinating the parallelization
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all 200 file reviews to the thread pool
            future_to_file = {executor.submit(review_single_file, file): file for file in files_to_review}
            
            completed = 0
            for future in as_completed(future_to_file):
                completed += 1
                result = future.result()
                results.append(result)
                
                # Keep track of files that failed review
                if result["status"] != "APPROVED":
                    issues_found.append(result)
                    
                # Print a progress update every 20 files
                if completed % 20 == 0 or completed == len(files_to_review):
                    print(f"  [{completed}/{len(files_to_review)}] files reviewed...")

        execution_time = time.time() - start_time
        print(f"\nCompleted {len(files_to_review)} individual subagent reviews in {execution_time:.2f} seconds.")
        print(f"Found {len(issues_found)} files requiring changes.\n")
        
        # -----------------------------------------------------------------
        # STEP 2: LLM Synthesis of the Structured Results
        # -----------------------------------------------------------------
        # Now we bring Claude back in for a single, high-level task: synthesis.
        print("Synthesizing final migration report using Claude...\n")
        
        # We ONLY pass the problematic files to the LLM to save on context window size
        issues_text = "\n".join([f"- {r['file']}: {r['comments']}" for r in issues_found])
        
        if not issues_found:
            issues_text = "No issues found. All files approved."
            
        synthesis_prompt = f"""
        A large codebase migration involving {len(files_to_review)} files has been reviewed by automated subagents.
        {len(results) - len(issues_found)} files were approved automatically.
        
        The following {len(issues_found)} files were flagged with issues:
        {issues_text}
        
        Please provide a short executive summary of the migration review status.
        Group the issues by type if possible, and provide next steps for the engineering team.
        Do NOT use any emojis in your response.
        """
        
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=600,
            system="You are a Lead Staff Engineer synthesizing code review results. Keep it professional and concise.",
            messages=[{"role": "user", "content": synthesis_prompt}]
        )
        
        print(f"--- EXECUTIVE SUMMARY ---\n{response.content[0].text}\n")
        print(f"{'='*80}")
        print("WORKFLOW COMPLETED SUCCESSFULLY")
        print(f"{'='*80}")


if __name__ == "__main__":
    # Generate 200 dummy file names to simulate a large migration
    dummy_migration_files = [f"src/legacy/PaymentModule_{i}.ts" for i in range(1, 201)]
    
    workflow = MigrationReviewWorkflow(max_concurrent_workers=40)
    workflow.run_large_scale_review(dummy_migration_files)
