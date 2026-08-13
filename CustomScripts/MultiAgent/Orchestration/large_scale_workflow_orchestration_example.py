"""
Large Scale Workflow Orchestration

Explores techniques for coordinating many agents across long-running, multi-
step workflows. It highlights best practices for state management and
checkpointing so that failures do not require restarting the entire workflow.
"""

import os
import random
import asyncio
from dotenv import load_dotenv

# SDK Imports
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
from pydantic import BaseModel, Field

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"


# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

# =====================================================================
# 1. Structured Output Definition (Pydantic)
# =====================================================================
class MigrationSynthesis(BaseModel):
    executive_summary: str = Field(description="A short executive summary of the migration review status.")
    critical_issues_count: int = Field(description="Total number of critical issues found.")
    recommended_next_steps: list[str] = Field(description="Actionable next steps for the engineering team.")

class FileReviewResult(BaseModel):
    status: str = Field(description="'APPROVED' or 'CHANGES_REQUESTED'")
    comments: str = Field(description="Review comments or vulnerabilities found.")

# =====================================================================
# 2. The Subagent (File Reviewer)
# =====================================================================
async def review_single_file_async(file_path: str) -> dict:
    """
    An SDK subagent reviewing a single file using a real LLM call.
    Uses asyncio.to_thread to run the synchronous SDK call without blocking.
    """
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        output_format={
            "type": "json_schema",
            "schema": FileReviewResult.model_json_schema()
        }
    )
    
    # In a real app we'd load the file content here
    content = f"Simulated code content for {file_path}" 
    
    result_dict = {"status": "CHANGES_REQUESTED", "comments": "Failed to extract result."}
    
    async for msg in query(
        prompt=f"Review this file for security issues or legacy APIs:\n\n{content}",
        options=options
    ):
        if isinstance(msg, ResultMessage) and msg.structured_output:
            result_dict = msg.structured_output
            break
    
    return {
        "file": file_path,
        "status": result_dict.get("status", "CHANGES_REQUESTED"),
        "comments": result_dict.get("comments", "")
    }

# =====================================================================
# 3. The Orchestration Workflow Tool (Deterministic Async Script)
# =====================================================================
class MigrationReviewWorkflow:
    def __init__(self, max_concurrent_workers: int = 50):
        # We use a semaphore to limit concurrent async tasks across the SDK
        self.semaphore = asyncio.Semaphore(max_concurrent_workers)

    async def _bounded_review(self, file_path: str):
        """Wrapper to enforce concurrency limits on our async subagents."""
        async with self.semaphore:
            return await review_single_file_async(file_path)

    async def run_large_scale_review(self, files_to_review: list[str]):
        print(f"\n{'='*80}")
        print(f"SDK WORKFLOW ORCHESTRATION ({len(files_to_review)} FILES)")
        print(f"{'='*80}")
        print("Instead of having an LLM coordinate 200 files turn-by-turn (which would")
        print("hit context limits, lose track, and cost a fortune), we use a deterministic")
        print("Python async workflow script to orchestrate the subagents in parallel.\n")
        
        # -----------------------------------------------------------------
        # STEP 1: Parallel Execution via Asyncio (Not turn-by-turn LLM)
        # -----------------------------------------------------------------
        print(f"Processing {len(files_to_review)} files with {self.semaphore._value} concurrent async workers...")
        start_time = asyncio.get_event_loop().time()
        
        # Schedule all 200 tasks concurrently
        tasks = [self._bounded_review(f) for f in files_to_review]
        results = await asyncio.gather(*tasks)
        
        issues_found = [r for r in results if r["status"] != "APPROVED"]
        
        execution_time = asyncio.get_event_loop().time() - start_time
        print(f"\nCompleted {len(files_to_review)} individual subagent reviews in {execution_time:.2f} seconds.")
        print(f"Found {len(issues_found)} files requiring changes.\n")
        
        # -----------------------------------------------------------------
        # STEP 2: SDK Synthesis of the Structured Results
        # -----------------------------------------------------------------
        print("Synthesizing final migration report using claude-agent-sdk...\n")
        
        issues_text = "\n".join([f"- {r['file']}: {r['comments']}" for r in issues_found])
        if not issues_found:
            issues_text = "No issues found. All files approved."
            
        synthesis_prompt = f"""
        A large codebase migration involving {len(files_to_review)} files has been reviewed by automated subagents.
        {len(results) - len(issues_found)} files were approved automatically.
        
        The following files were flagged with issues:
        {issues_text}
        
        Please synthesize these code review results. Do NOT use emojis.
        """
        
        # Using the SDK to enforce structured output for the final report
        options = ClaudeAgentOptions(
            system_prompt="You are a Lead Staff Engineer synthesizing code review results.",
            model=DEFAULT_MODEL,
            output_format={
                "type": "json_schema",
                "schema": MigrationSynthesis.model_json_schema()
            }
        )
        
        # Stream the results from the SDK's query helper
        async for msg in query(
            prompt=synthesis_prompt,
            options=options
        ):
            if isinstance(msg, ResultMessage) and msg.structured_output:
                # Validate the raw dictionary back into a fully-typed Pydantic object
                result = MigrationSynthesis.model_validate(msg.structured_output)
                print("--- EXECUTIVE SUMMARY ---")
                print(f"{result.executive_summary}\n")
                print(f"Critical Issues Found: {result.critical_issues_count}")
                print("\nRecommended Next Steps:")
                for step in result.recommended_next_steps:
                    print(f"  - {step}")

        print(f"\n{'='*80}")
        print("WORKFLOW COMPLETED SUCCESSFULLY")
        print(f"{'='*80}")

if __name__ == "__main__":
    # Generate 5 dummy file names (scaled down from 200 to avoid API rate limits in demo)
    dummy_migration_files = [f"src/legacy/PaymentModule_{i}.ts" for i in range(1, 6)]
    
    workflow = MigrationReviewWorkflow(max_concurrent_workers=50)
    asyncio.run(workflow.run_large_scale_review(dummy_migration_files))
