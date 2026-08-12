"""
LangGraph Multi-Agent System

Provides an example of building a multi-agent system using the LangGraph
framework for structured state and routing. LangGraph offers a cyclic graph
approach, making it easier to define robust loops and conditional transitions
between agents.
"""

import os
from typing import TypedDict
from pydantic import BaseModel, Field

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"


# ==============================================================================
# LANGGRAPH MULTI-AGENT DETERMINISTIC WORKFLOW
# ==============================================================================
# This implements a flawless deterministic state machine:
# START -> Analyst Node -> Synthesizer Node -> END
# Both nodes use strict Pydantic parsing via .with_structured_output()

# --- 1. Define Pydantic Schemas (The Structured Handoffs) ---
class Citation(BaseModel):
    source: str = Field(description="Name of the source or author")
    year: int = Field(description="Year of publication")
    url: str = Field(description="URL linking to the source material")

class AnalystFact(BaseModel):
    claim: str = Field(description="The factual claim")
    citation: Citation = Field(description="The source of the claim")

class AnalystFindings(BaseModel):
    topic: str = Field(description="The topic analyzed")
    facts: list[AnalystFact] = Field(description="List of facts with their citations")

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

# --- 2. Define the Graph State ---
class GraphState(TypedDict):
    topic: str
    raw_facts: AnalystFindings | None
    final_report: DeepResearchReport | None

# --- 3. Define the Nodes (The Agents) ---
def analyst_node(state: GraphState) -> GraphState:
    print(f"\n[NODE: ANALYST] 🕵️ Gathering structured facts on: '{state['topic']}'")
    
    # Langchain's ChatAnthropic automatically handles structured output binding!
    llm = ChatAnthropic(model=DEFAULT_MODEL, temperature=0)
    structured_llm = llm.with_structured_output(AnalystFindings)
    
    messages = [
        SystemMessage(content="You are an Analyst Agent. Extract highly accurate facts and strictly cite your sources."),
        HumanMessage(content=f"Analyze topic: {state['topic']}")
    ]
    
    # Execute and parse natively
    findings = structured_llm.invoke(messages)
    print(f"[NODE: ANALYST] ✅ Extracted {len(findings.facts)} cited facts.")
    
    # Save the raw findings to a JSON file for inspection
    try:
        with open("analyst_raw_facts.json", "w", encoding="utf-8") as f:
            f.write(findings.model_dump_json(indent=2))
        print("[NODE: ANALYST] 💾 Saved raw facts to analyst_raw_facts.json")
    except Exception as e:
        print(f"[NODE: ANALYST] ❌ Failed to save raw facts: {e}")
    
    return {"raw_facts": findings}

def synthesizer_node(state: GraphState) -> GraphState:
    print(f"\n[NODE: SYNTHESIZER] 📝 Formatting data into deeply nested Pydantic structure...")
    
    llm = ChatAnthropic(model=DEFAULT_MODEL, temperature=0)
    structured_llm = llm.with_structured_output(DeepResearchReport)
    
    # We pass the Analyst's Pydantic model directly into the prompt as a string
    raw_notes_str = state["raw_facts"].model_dump_json(indent=2)
    
    messages = [
        SystemMessage(content="You are a Synthesizer Agent. Convert the raw notes into the highly structured nested report."),
        HumanMessage(content=f"Topic: {state['topic']}\n\nRaw Notes:\n{raw_notes_str}")
    ]
    
    report = structured_llm.invoke(messages)
    print("[NODE: SYNTHESIZER] ✅ Parsed successfully into final report!")
    
    return {"final_report": report}

# --- 4. Compile the Deterministic Graph ---
def build_and_run_graph(topic: str):
    print(f"\n{'='*70}\n[LANGGRAPH] 🧠 Initializing Deterministic Workflow\n{'='*70}")
    
    workflow = StateGraph(GraphState)
    
    # Add Nodes
    workflow.add_node("Analyst", analyst_node)
    workflow.add_node("Synthesizer", synthesizer_node)
    
    # Define Deterministic Edges (No LLM Routing)
    workflow.add_edge(START, "Analyst")
    workflow.add_edge("Analyst", "Synthesizer")
    workflow.add_edge("Synthesizer", END)
    
    app = workflow.compile()
    
    # Run the graph
    initial_state = {"topic": topic, "raw_facts": None, "final_report": None}
    
    try:
        final_state = app.invoke(initial_state)
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")
        return
        
    report = final_state.get("final_report")
    
    if report:
        print(f"\n\n{'='*70}\n🏆 FINAL EXTRACTED PYDANTIC OBJECT\n{'='*70}")
        print(f"📑 TOPIC: {report.topic}")
        print(f"📋 EXECUTIVE SUMMARY: {report.executive_summary}\n")
        for section in report.sections:
            print(f"🔹 {section.heading.upper()}")
            for sub in section.subsections:
                print(f"   🔸 {sub.title}")
                for cit in sub.citations:
                    print(f"      📚 Source: {cit.source}, {cit.year} ({cit.url})")
            print()
            
        # Generate PDF Report
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            
            def safe_txt(t):
                return t.encode('latin-1', 'replace').decode('latin-1')
            
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(0, 10, safe_txt(report.topic), new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(10)
            
            pdf.set_font("helvetica", "B", 12)
            pdf.cell(0, 10, "Executive Summary", new_x="LMARGIN", new_y="NEXT")
            
            pdf.set_font("helvetica", "", 10)
            pdf.multi_cell(0, 7, safe_txt(report.executive_summary))
            pdf.ln(5)
            
            for section in report.sections:
                pdf.set_font("helvetica", "B", 14)
                pdf.cell(0, 10, safe_txt(section.heading.upper()), new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
                
                for sub in section.subsections:
                    pdf.set_font("helvetica", "B", 11)
                    pdf.cell(0, 8, safe_txt(sub.title), new_x="LMARGIN", new_y="NEXT")
                    
                    pdf.set_font("helvetica", "", 10)
                    pdf.multi_cell(0, 6, safe_txt(sub.content))
                    
                    if sub.citations:
                        for cit in sub.citations:
                            pdf.set_font("helvetica", "I", 9)
                            pdf.set_text_color(100, 100, 100)
                            text = safe_txt(f"Source: {cit.source}, {cit.year} ")
                            pdf.write(5, text)
                            
                            pdf.set_text_color(0, 0, 255)
                            pdf.write(5, safe_txt(cit.url), cit.url)
                            pdf.set_text_color(0, 0, 0)
                            pdf.ln(5)
                    pdf.ln(4)
            
            pdf_filename = "research_report.pdf"
            pdf.output(pdf_filename)
            print(f"\n[SYSTEM] ✅ Successfully saved report to {pdf_filename}")
        except Exception as e:
            print(f"\n[SYSTEM] ❌ Failed to generate PDF: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("WARNING: Using dummy API key. Calls will fail, but the architecture is visible.")
        os.environ["ANTHROPIC_API_KEY"] = "dummy_key"
        
    request = "The architectural evolution of AI Transformers (2017-2024)"
    build_and_run_graph(request)
