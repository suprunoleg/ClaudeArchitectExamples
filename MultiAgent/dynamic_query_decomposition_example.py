import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

# =====================================================================
# 1. The Subagent (Specialized Researcher)
# =====================================================================
class ResearchSubagent:
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        self.name = f"Subagent_{self.agent_id}"

    def research(self, sub_query: str) -> str:
        print(f"  [{self.name}] Researching: '{sub_query}'")
        # In a real scenario, this agent would use tools to search the web or internal docs.
        # Here we just use the model to generate a simulated factual response.
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=400,
            system="You are an expert market research subagent. Provide concise, factual information strictly about the requested subtopic.",
            messages=[{"role": "user", "content": sub_query}]
        )
        return response.content[0].text


# =====================================================================
# 2. The Coordinator (Dynamic Task Decomposer & Synthesizer)
# =====================================================================
class CoordinatorAgent:
    def __init__(self):
        pass

    def dynamic_decompose(self, broad_query: str) -> list[str]:
        """
        Dynamically decomposes a broad query into a list of specific sub-queries
        by utilizing an LLM tool call, ensuring comprehensive coverage.
        """
        print(f"Coordinator is analyzing the broad query to generate comprehensive sub-tasks...")
        
        # We use tool calling to force Claude to return a structured list of sub-queries
        tool = {
            "name": "submit_subqueries",
            "description": "Submit a list of mutually exclusive, collectively exhaustive sub-queries that break down the main research query.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "sub_queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "The list of focused sub-queries that together cover the ENTIRE scope of the main query."
                    }
                },
                "required": ["sub_queries"]
            }
        }
        
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=500,
            system=(
                "You are a brilliant coordinator agent. Your job is to break down complex research "
                "queries into smaller, highly specific sub-queries. You MUST ensure that the resulting "
                "sub-queries comprehensively cover all aspects of the original query (e.g., if asked about "
                "a competitive landscape, include technology, pricing, key competitors, market share, and regulation)."
            ),
            tools=[tool],
            tool_choice={"type": "tool", "name": "submit_subqueries"},
            messages=[{"role": "user", "content": f"Decompose this query into 3 to 5 comprehensive sub-queries: {broad_query}"}]
        )
        
        # Extract the tool use arguments
        for block in response.content:
            if block.type == "tool_use" and block.name == "submit_subqueries":
                return block.input.get("sub_queries", [])
                
        return []

    def run_research_pipeline(self, broad_query: str):
        print(f"\n{'='*60}")
        print(f"DYNAMIC QUERY DECOMPOSITION PIPELINE")
        print(f"{'='*60}")
        print(f"Original Broad Query: '{broad_query}'\n")
        
        # 1. DECOMPOSITION PHASE
        sub_queries = self.dynamic_decompose(broad_query)
        
        print(f"\nCoordinator dynamically generated {len(sub_queries)} sub-queries:")
        for sq in sub_queries:
            print(f"  - {sq}")
        print()
        
        # 2. EXECUTION PHASE (Dynamically spinning up subagents)
        research_results = []
        for i, sq in enumerate(sub_queries):
            # Spin up a dynamic subagent for each query
            agent = ResearchSubagent(agent_id=i+1)
            result = agent.research(sq)
            research_results.append(f"--- Sub-query: {sq} ---\n{result}\n")
            
        # 3. SYNTHESIS PHASE
        print("\n=== SYNTHESIS PHASE ===")
        print("Coordinator is synthesizing the final comprehensive report...\n")
        
        synthesis_prompt = f"""
        Original Broad Query: {broad_query}
        
        Subagent Research Results:
        {"".join(research_results)}
        
        Please synthesize these results into a cohesive, comprehensive report 
        that directly answers the original broad query.
        """
        
        final_report = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            system="You are a report synthesizer. Synthesize the provided research into a cohesive, highly professional report.",
            messages=[{"role": "user", "content": synthesis_prompt}]
        ).content[0].text
        
        print(f"--- FINAL REPORT ---\n{final_report}\n")
        print(f"{'='*60}")
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print(f"{'='*60}")


if __name__ == "__main__":
    coordinator = CoordinatorAgent()
    query = "analyze the competitive landscape for electric vehicle charging networks"
    coordinator.run_research_pipeline(query)
