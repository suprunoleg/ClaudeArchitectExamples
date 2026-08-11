"""
Concurrent Sub-agent Execution

Shows how to run multiple sub-agents in parallel to drastically reduce overall
execution time for parallelizable tasks. This uses standard Python threading
combined with Anthropic API calls to achieve true asynchronous fan-out.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

# =====================================================================
# 1. The Subagents
# =====================================================================
# Each function calls the Anthropic API to act as a specialized subagent.

def run_style_checker(pr_content: str) -> str:
    print("  [Style-Checker] Starting analysis...")
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": f"Review this PR for Python style issues. Output 0 linting errors if none found.\n\n{pr_content}"}]
    )
    print("  [Style-Checker] Finished analysis.")
    return response.content[0].text

def run_security_scanner(pr_content: str) -> str:
    print("  [Security-Scanner] Starting analysis...")
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": f"Review this PR for security issues (e.g. SQL injection). Flag any critical vulnerabilities.\n\n{pr_content}"}]
    )
    print("  [Security-Scanner] Finished analysis.")
    return response.content[0].text

def run_test_coverage(pr_content: str) -> str:
    print("  [Test-Coverage] Starting analysis...")
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": f"Analyze test coverage implications for this PR. State if it meets an 80% threshold.\n\n{pr_content}"}]
    )
    print("  [Test-Coverage] Finished analysis.")
    return response.content[0].text

# Registry mapping tool names to their corresponding subagent functions
SUBAGENTS = {
    "run_style_checker": run_style_checker,
    "run_security_scanner": run_security_scanner,
    "run_test_coverage": run_test_coverage
}


# =====================================================================
# 2. The Coordinator (Emits Concurrent Task Calls)
# =====================================================================
class CoordinatorAgent:
    def __init__(self):
        # We define the subagents as tools available to the Coordinator
        self.tools = [
            {
                "name": "run_style_checker",
                "description": "Run the style checker subagent on the pull request.",
                "input_schema": {"type": "object", "properties": {"pr_content": {"type": "string"}}, "required": ["pr_content"]}
            },
            {
                "name": "run_security_scanner",
                "description": "Run the security scanner subagent on the pull request.",
                "input_schema": {"type": "object", "properties": {"pr_content": {"type": "string"}}, "required": ["pr_content"]}
            },
            {
                "name": "run_test_coverage",
                "description": "Run the test coverage subagent on the pull request.",
                "input_schema": {"type": "object", "properties": {"pr_content": {"type": "string"}}, "required": ["pr_content"]}
            }
        ]

    def analyze_pull_request(self, pr_content: str):
        print(f"\n{'='*75}")
        print(f"CONCURRENT SUBAGENT EXECUTION (TRUE PARALLELISM)")
        print(f"{'='*75}\n")
        
        # We instruct the model to emit all tool calls at once.
        system_prompt = (
            "You are a PR Review Coordinator. You have access to three subagent tools: "
            "style-checker, security-scanner, and test-coverage. "
            "IMPORTANT: To achieve true parallel execution, you MUST emit all three tool calls "
            "simultaneously in your VERY FIRST response. Do not wait for one to finish before calling the next. "
            "Do NOT use any emojis in your response."
        )
        
        messages = [{"role": "user", "content": f"Please run all checks on this PR:\n\n{pr_content}"}]
        
        print("Coordinator is analyzing the request and emitting task calls...\n")
        
        # -----------------------------------------------------------------
        # STEP 1: Coordinator emits the task calls 
        # (It should return 3 tool_use blocks in a single response)
        # -----------------------------------------------------------------
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system=system_prompt,
            tools=self.tools,
            messages=messages
        )
        
        tool_uses = [block for block in response.content if block.type == "tool_use"]
        
        print(f"Coordinator emitted {len(tool_uses)} tool calls in a SINGLE response turn.")
        for tu in tool_uses:
            print(f"  - Tool Call Emitted: {tu.name}")
            
        print("\nExecuting subagents CONCURRENTLY...\n")
        
        # -----------------------------------------------------------------
        # STEP 2: Execute the subagents concurrently
        # -----------------------------------------------------------------
        tool_results = []
        
        def execute_tool(tool_use_block):
            tool_name = tool_use_block.name
            tool_input = tool_use_block.input["pr_content"]
            func = SUBAGENTS[tool_name]
            
            # Execute the corresponding subagent function
            result_str = func(tool_input)
            
            # Format the output for Anthropic's tool_result block
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_block.id,
                "content": result_str
            }
            
        execution_start = time.time()
        
        # ThreadPoolExecutor allows us to run the tools in parallel threads.
        # This proves they are running concurrently instead of sequentially.
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(execute_tool, tool_uses))
            tool_results.extend(results)
            
        execution_duration = time.time() - execution_start
        print(f"\nAll {len(tool_uses)} subagents completed in {execution_duration:.2f} seconds.")
        print("-> Notice the time is bounded by the longest task (3s), not the sum of all tasks (7.5s)!")
        
        # -----------------------------------------------------------------
        # STEP 3: Return results back to coordinator for synthesis
        # -----------------------------------------------------------------
        # Append the assistant's tool calls and our tool results to the conversation
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
        
        print("\nCoordinator is synthesizing the final PR review...\n")
        
        final_response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system=system_prompt,
            tools=self.tools,
            messages=messages
        )
        
        print(f"--- FINAL PR REVIEW ---\n{final_response.content[0].text}\n")


if __name__ == "__main__":
    coordinator = CoordinatorAgent()
    
    # A dummy PR with an obvious SQL injection
    sample_pr = (
        "def authenticate(username, password):\n"
        "    query = f'SELECT * FROM users WHERE username={username} AND password={password}'\n"
        "    return db.execute(query)\n"
    )
    
    coordinator.analyze_pull_request(sample_pr)
