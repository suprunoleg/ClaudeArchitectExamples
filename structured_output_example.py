"""
Structured Output

Shows the basic approach for extracting structured data (JSON) from text using
tool use with the Anthropic API. Tool use provides a reliable way to force the
model into a deterministic JSON format, significantly reducing parsing errors.
"""

import asyncio
import os
from pydantic import BaseModel, Field
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

# ==============================================================================
# STRUCTURED OUTPUT FORMAT EXAMPLE
# ==============================================================================
# This example demonstrates how to use Pydantic models to force Claude to return
# its final answer in a strictly typed JSON format. This is heavily tested on
# the Anthropic Architect Certification!

# 1. Define schema via Pydantic
class AnalysisResult(BaseModel):
    company_name: str = Field(description="The name of the company being researched")
    founded_year: int = Field(description="The year the company was founded")
    key_findings: list[str] = Field(description="Summary of key discoveries made by agent tools")
    citations: list[str] = Field(description="List of verifiable sources for the findings")

async def main():
    print("="*50)
    print("Starting Structured Output Research")
    print("="*50)
    
    # 2. Pass the Pydantic schema into agent options via output_format
    # We use model_json_schema() to easily convert the Pydantic class into JSON Schema!
    options = ClaudeAgentOptions(
        output_format={
            "type": "json_schema",
            "schema": AnalysisResult.model_json_schema()
        }
    )

    # 3. We use the SDK's `query` helper to run the agent loop automatically
    print("Agent is researching Anthropic...")
    async for message in query(
        prompt="Research Anthropic and summarize their core history and tech.",
        options=options
    ):
        # Optional: Print out the agent's progress
        if message.type == "assistant":
            pass # You can log intermediate thoughts here
        elif message.type == "tool_use":
            print(f"  [Tool Use] Calling {message.tool_name}...")
            
        # 4. Retrieve structured output from ResultMessage
        if isinstance(message, ResultMessage):
            print("\n✅ Task Complete! Extracting structured output...")
            if message.structured_output:
                # Parse the raw dictionary back into a fully-typed Pydantic object
                result = AnalysisResult.model_validate(message.structured_output)
                
                print(f"\n🏢 Company: {result.company_name} ({result.founded_year})")
                print("🔍 Findings:")
                for finding in result.key_findings:
                    print(f"   - {finding}")
                print("📚 Citations:")
                for citation in result.citations:
                    print(f"   - {citation}")
            else:
                print("No structured output was returned!")

if __name__ == "__main__":
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("WARNING: Using dummy API key. Calls will fail, but the architecture is visible.")
        os.environ["ANTHROPIC_API_KEY"] = "dummy_key"
        
    asyncio.run(main())
