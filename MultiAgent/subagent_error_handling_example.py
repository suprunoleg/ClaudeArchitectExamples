"""
Sub-agent Error Handling

Demonstrates robust error handling and recovery mechanisms when sub-agents
fail or return invalid responses. It implements automatic retries and fallback
strategies to ensure the top-level coordinator doesn't crash.
"""

import os
from dotenv import load_dotenv

from anthropic import Anthropic
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

# Load API key
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

# Initialize raw client for the subagent's internal stream
anthropic_client = Anthropic()

@tool
def research_subagent(topic: str) -> str:
    """
    A long-running foreground subagent that performs deep research on a topic.
    Call this tool to get detailed analysis.
    """
    print(f"\n[SUBAGENT] 🏃 Starting deep research on: '{topic}'")
    print(f"[SUBAGENT] 📡 Streaming response from server...\n")
    
    partial_text = ""
    try:
        # We use the raw Anthropic client here to easily simulate a stream interruption
        with anthropic_client.messages.stream(
            model="claude-sonnet-4-5",
            max_tokens=1000,
            messages=[{"role": "user", "content": f"Write a detailed 3-paragraph research analysis on {topic}"}]
        ) as stream:
            chunk_count = 0
            for text in stream.text_stream:
                partial_text += text
                # Print the chunks exactly as they stream in to show the foreground process
                print(text, end="", flush=True)
                chunk_count += 1
                
                # SIMULATE SERVER OVERLOAD ERROR MID-GENERATION!
                # We let it generate about 20 chunks (usually a sentence or two), then crash it.
                if chunk_count > 20:
                    raise Exception("503 Server Overload Error")
                    
        return partial_text
        
    except Exception as e:
        # GRACEFUL DEGRADATION (Question 22 Pattern)
        # Catch the exception, and return the partial text + system note back to the Coordinator!
        error_msg = f"\n\n🚨 [SYSTEM NOTE: Subagent didn't finish due to error: {e}]"
        print(error_msg)
        return partial_text + error_msg

def build_and_run_workflow():
    print("=" * 70)
    print("🧠 Initializing Resilient Coordinator Workflow")
    print("=" * 70)
    
    # Initialize the Coordinator LLM
    llm = ChatAnthropic(model="claude-sonnet-4-5", temperature=0)
    
    # Define system instructions for the Coordinator
    system_prompt = (
        "You are a Research Coordinator. Use the `research_subagent` to get analysis on the user's topic. "
        "IMPORTANT: If the subagent returns a partial response with a [SYSTEM NOTE] about an error, "
        "DO NOT call the tool again to retry. The server is overloaded. "
        "Instead, simply synthesize whatever partial text you successfully received, provide a helpful answer, "
        "and inform the user that the research was cut short due to an upstream server error."
    )
    
    # Create the React Agent (Coordinator)
    coordinator = create_react_agent(
        llm, 
        tools=[research_subagent], 
        prompt=system_prompt
    )
    
    user_request = "Please research the history of the Apollo 11 mission and summarize it for me."
    print(f"\n[USER] 👤 {user_request}")
    
    # Stream the events from the Coordinator
    inputs = {"messages": [("user", user_request)]}
    
    for event in coordinator.stream(inputs, stream_mode="values"):
        message = event["messages"][-1]
        
        # If it's an AI message, it's the Coordinator thinking/speaking
        if message.type == "ai":
            if hasattr(message, "tool_calls") and message.tool_calls:
                print(f"\n[COORDINATOR] 🛠️ Decided to call tool: {message.tool_calls[0]['name']}")
            elif message.content:
                print(f"\n\n{'='*70}\n[COORDINATOR FINAL ANSWER] 🎯\n{'='*70}")
                print(message.content)

if __name__ == "__main__":
    build_and_run_workflow()
