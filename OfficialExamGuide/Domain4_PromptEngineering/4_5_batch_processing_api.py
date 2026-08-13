"""
Task Statement 4.5: Design efficient batch processing strategies
(API VERSION)

Knowledge of:
- Anthropic's Message Batch API and when to use it (asynchronous, large-scale, cost-sensitive).
- How to structure a batch request.

Skills in:
- Constructing a batch request using the raw `anthropic` SDK.
"""

import os
import asyncio
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = AsyncAnthropic()

async def run_batch_processing():
    
    # 1. Processing 10,000 document summaries overnight.
    # 2. Running a massive evaluation suite.
    # Why? It provides a 50% discount but takes up to 24 hours to complete.
    
    # We construct a list of standard message request objects, each wrapped in a Request structure
    requests = [
        {
            "custom_id": "doc-123",
            "params": {
                "model": DEFAULT_MODEL,
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Summarize Document A"}]
            }
        },
        {
            "custom_id": "doc-124",
            "params": {
                "model": DEFAULT_MODEL,
                "max_tokens": 100,
                "messages": [{"role": "user", "content": "Summarize Document B"}]
            }
        }
    ]
    
    try:
        message_batch = await client.messages.batches.create(
            requests=requests
        )
        
        # In a real system, you would save `message_batch.id` to a database and poll/webhook for completion later.
        
        # Example of retrieving results later:
        # results = await client.messages.batches.results(message_batch.id)
        # for result in results:
        #     if result.result.type == "succeeded":
        #         print(f"{result.custom_id}: {result.result.message.content[0].text}")
                
        return message_batch.id
    except Exception as e:
        return "Failed to submit batch."

if __name__ == "__main__":
    asyncio.run(run_batch_processing())
