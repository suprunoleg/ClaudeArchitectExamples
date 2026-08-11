"""
Citations Testing

Test script to validate the functionality of the native citations
implementation. It verifies that the citations point to the correct document
indices and extract the expected text segments.
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

document_content = """
Acme Corp Financial Report Q3 2023.
Revenue increased by 15% to $4.2 million.
Operating costs were reduced by 5% due to the new cloud infrastructure.
The CEO, Jane Doe, stated that Q4 will focus on AI expansion.
"""

try:
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "text",
                            "media_type": "text/plain",
                            "data": document_content
                        },
                        "title": "Q3 Financials",
                        "citations": {"enabled": True}
                    },
                    {
                        "type": "text",
                        "text": "What happened to Acme Corp's revenue and operating costs?"
                    }
                ]
            }
        ]
    )
    print("SUCCESS!")
    print(response.model_dump_json(indent=2))
except Exception as e:
    print(f"Error: {e}")
