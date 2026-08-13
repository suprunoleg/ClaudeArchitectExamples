"""
Nested Structured Output

Demonstrates how to use the Anthropic API to generate complex, deeply nested
JSON structures using Pydantic models and the `client.messages.parse()`
method. This is particularly useful when extracting hierarchical data like
chapters and sections from a book, ensuring the LLM adheres to strict schemas.
"""

import os
import json
from pydantic import BaseModel, Field
from anthropic import Anthropic
from dotenv import load_dotenv

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"



# ==============================================================================
# NESTED STRUCTURED OUTPUT VIA RAW ANTHROPIC API (parse method)
# ==============================================================================
# In recent versions of the Anthropic SDK, you don't need to manually create tools 
# and parse the tool_choice. You can use `client.messages.parse()` which natively 
# accepts a Pydantic class in the `response_model` argument!

# 1. Define a DEEPLY NESTED schema via Pydantic
class Citation(BaseModel):
    source: str = Field(description="Name of the source or author")
    year: int = Field(description="Year of publication")
    url: str | None = Field(default=None, description="URL if available")

class Subsection(BaseModel):
    title: str = Field(description="Title of the subsection")
    content: str = Field(description="Detailed factual content")
    citations: list[Citation] = Field(description="Citations supporting this subsection")

class Section(BaseModel):
    heading: str = Field(description="Main section heading")
    subsections: list[Subsection] = Field(description="Nested subsections")

class DeepResearchReport(BaseModel):
    topic: str = Field(description="The core topic being researched")
    executive_summary: str = Field(description="High-level summary of the findings")
    sections: list[Section] = Field(description="The deeply nested sections of the report")

def generate_nested_report(topic: str):
    print(f"\n{'='*70}")
    print(f"ðŸ•µï¸ Starting Raw API Researcher Agent: '{topic}'")
    print(f"{'='*70}")
    
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "dummy_key"))
    
    system_prompt = (
        "You are an expert Researcher Agent. "
        "Your task is to compile a highly detailed, deeply nested research report on the requested topic. "
    )
    
    try:
        print("[RESEARCHER] ðŸ¤” Thinking and building nested structure via messages.parse()...")
        # 2. Use client.messages.parse() and pass the Pydantic model directly to response_model!
        response = client.messages.parse(
            model=DEFAULT_MODEL,
            max_tokens=4096,  # Nested outputs can be large!
            system=system_prompt,
            messages=[{"role": "user", "content": f"Research topic: {topic}"}],
            response_model=DeepResearchReport
        )
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")
        return

    # 3. Access the perfectly validated Pydantic object directly via response.parsed
    if getattr(response, "parsed", None):
        print("\nâœ… Task Complete! Extracting deeply nested Pydantic Object...")
        
        report = response.parsed
        
        print(f"\nðŸ“‘ TOPIC: {report.topic}")
        print(f"ðŸ“‹ EXECUTIVE SUMMARY: {report.executive_summary}\n")
        
        for section in report.sections:
            print(f"ðŸ”¹ {section.heading.upper()}")
            for sub in section.subsections:
                print(f"   ðŸ”¸ {sub.title}")
                print(f"      {sub.content}")
                for cit in sub.citations:
                    url_str = f" ({cit.url})" if cit.url else ""
                    print(f"      ðŸ“š Source: {cit.source}, {cit.year}{url_str}")
            print()
    else:
        print("Model failed to call the required tool.")

if __name__ == "__main__":
        
    request = "The architectural evolution of AI Transformers (2017-2024)"
    generate_nested_report(request)
