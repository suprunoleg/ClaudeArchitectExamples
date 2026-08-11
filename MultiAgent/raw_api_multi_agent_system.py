"""
Raw API Multi-Agent System

Shows how to build a multi-agent system from scratch using only the raw
Anthropic API without higher-level frameworks. This gives developers maximum
control and visibility over the exact messages and tool calls being sent to
the model.
"""

import os
import json
from pydantic import BaseModel, Field
from anthropic import Anthropic

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"


# ==============================================================================
# RAW API MULTI-AGENT SYSTEM with .PARSE() STRUCTURED OUTPUT
# ==============================================================================
# This is the ultimate Anthropic Architect Certification pattern:
# 1. A Coordinator LLM orchestrates the workflow using tool calling.
# 2. A Researcher Subagent (raw API) gathers raw unstructured facts.
# 3. A Synthesizer Subagent (raw API) uses `client.messages.parse()` to force 
#    the final deliverable into a deeply nested Pydantic schema!

# --- 1. Define the Pydantic Schema for the final Synthesizer ---
class Citation(BaseModel):
    source: str = Field(description="Name of the source or author")
    year: int = Field(description="Year of publication")

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

# --- 2. Define the Pydantic Schema for the Analyst ---
class AnalystFact(BaseModel):
    claim: str = Field(description="The factual claim")
    citation: Citation = Field(description="The source of the claim")

class AnalystFindings(BaseModel):
    topic: str = Field(description="The topic analyzed")
    facts: list[AnalystFact] = Field(description="List of facts with their citations")

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "dummy_key"))

# --- 3. Define the Subagents as Python Functions ---
def analyst_agent(topic: str) -> str:
    print(f"\n[ANALYST] 🕵️ Gathering structured facts and citations on: '{topic}'")
    
    system_prompt = (
        "You are an Analyst Agent. Your job is to extract highly accurate facts about the topic. "
        "You have access to a `web_search` tool. Use it to find real data and citations. "
        "CRITICAL REQUIREMENT: Every single fact MUST have a verifiable citation. "
        "When you are finished researching, you MUST use the `submit_findings` tool to output your facts."
    )
    
    tools = [
        {
            "name": "web_search",
            "description": "Mock tool to search the internet for facts.",
            "input_schema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        },
        {
            "name": "submit_findings",
            "description": "Submit your final structured findings and citations.",
            "input_schema": AnalystFindings.model_json_schema()
        }
    ]
    
    messages = [{"role": "user", "content": f"Analyze topic: {topic}"}]
    
    while True:
        try:
            print("[ANALYST] 🤔 Thinking / Searching...")
            response = client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=2048,
                system=system_prompt,
                tools=tools,
                messages=messages
            )
        except Exception as e:
            return f"Analysis failed: {e}"
            
        messages.append({"role": "assistant", "content": response.content})
        
        if response.stop_reason != "tool_use":
            break
            
        tool_use = next(block for block in response.content if block.type == "tool_use")
        
        if tool_use.name == "web_search":
            query = tool_use.input.get("query")
            print(f"[ANALYST] 🌐 Searching web for: {query}")
            # Mock web search result
            mock_result = f"Search results for '{query}': Found 3 relevant papers from 2023."
            messages.append({
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": mock_result}]
            })
        elif tool_use.name == "submit_findings":
            print("[ANALYST] 📥 Submitting structured findings!")
            # 4. Extract and validate against Pydantic model natively from the tool input
            findings = AnalystFindings.model_validate(tool_use.input)
            print(f"[ANALYST] ✅ Extracted {len(findings.facts)} structured facts with citations.")
            # Return JSON string to Coordinator
            return findings.model_dump_json(indent=2)
            
    return "{}"

def synthesizer_agent(raw_notes: str, topic: str) -> DeepResearchReport | str:
    print(f"\n[SYNTHESIZER] 📝 Formatting data into deeply nested Pydantic structure...")
    try:
        # MAGIC: We use `.parse()` exclusively on the Synthesizer to guarantee the final output structure!
        response = client.messages.parse(
            model=DEFAULT_MODEL,
            max_tokens=4096,
            system="You are a Synthesizer Agent. Convert the raw notes into the highly structured nested report.",
            messages=[{"role": "user", "content": f"Topic: {topic}\n\nRaw Notes:\n{raw_notes}"}],
            response_model=DeepResearchReport
        )
        print("[SYNTHESIZER] ✅ Parsed successfully into Pydantic objects!")
        return response.parsed
    except Exception as e:
        return f"Synthesis failed: {e}"

# --- 4. The Deterministic Coordinator Workflow ---
def run_deterministic_workflow(user_request: str):
    print(f"\n{'='*70}\n[WORKFLOW] 🧠 Received Request: '{user_request}'\n{'='*70}")
    
    # 1. Analyst Phase
    print("\n[WORKFLOW] ⏳ PHASE 1: Triggering Analyst Agent...")
    analyst_result_json = analyst_agent(user_request)
    
    if "Failed" in analyst_result_json or not analyst_result_json:
        print("[WORKFLOW] ❌ Analyst failed to return data. Aborting.")
        return
        
    # 2. Synthesizer Phase
    print("\n[WORKFLOW] ⏳ PHASE 2: Triggering Synthesizer Agent...")
    final_report = synthesizer_agent(analyst_result_json, user_request)
    
    if not isinstance(final_report, DeepResearchReport):
        print(f"[WORKFLOW] ❌ Synthesizer failed: {final_report}")
        return
        
    # 3. Output
    print(f"\n\n{'='*70}\n🏆 FINAL EXTRACTED PYDANTIC OBJECT\n{'='*70}")
    print(f"📑 TOPIC: {final_report.topic}")
    print(f"📋 EXECUTIVE SUMMARY: {final_report.executive_summary}\n")
    for section in final_report.sections:
        print(f"🔹 {section.heading.upper()}")
        for sub in section.subsections:
            print(f"   🔸 {sub.title}")
            print(f"      {sub.content}")
            for cit in sub.citations:
                print(f"      📚 Source: {cit.source}, {cit.year}")
        print()

if __name__ == "__main__":
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("WARNING: Using dummy API key. Calls will fail, but the architecture is visible.")
        os.environ["ANTHROPIC_API_KEY"] = "dummy_key"
        
    request = "Research the architectural evolution of AI Transformers (2017-2024) and build a structured report."
    run_deterministic_workflow(request)
