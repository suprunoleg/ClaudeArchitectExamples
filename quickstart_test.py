"""
Quickstart Test

A simple test script to verify that the Anthropic API connection and
authentication are working correctly. Run this first to ensure your `.env`
file and API keys are properly configured before diving into more complex
examples.
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load the environment variables from .env
load_dotenv()

print("Initializing Anthropic client...")
client = Anthropic(
    # This is the default and can be omitted, but shown here for clarity
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

print("Sending test message to claude-sonnet-4-5...")
try:
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": "Hello, Claude! Are you receiving this? Please reply with a short greeting."}
        ]
    )
    print("\n✅ SUCCESS! Claude responded:")
    print("-" * 50)
    for block in message.content:
        if block.type == "text":
            print(block.text)
    print("-" * 50)
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    if hasattr(e, "response"):
        print(f"DETAILS: {getattr(e.response, 'text', 'No text available')}")
