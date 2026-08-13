"""
Task Statement 4.4: Implement validation, retry, and feedback loops for extraction quality
(API VERSION)

This file demonstrates how to build the identical patterns tested in 4.4 using 
deterministic, code-first Python architecture instead of relying on the SDK.

Knowledge of:
- How to validate LLM outputs against strict business logic rules.
- How to feed validation errors back into the prompt so the LLM can self-correct.

Skills in:
- Implementing a programmatic retry loop (`for _ in range(max_retries)`).
- Injecting the specific error message back into the prompt.
"""

import os
import asyncio
import json
from typing import Optional
from pydantic import BaseModel, ValidationError
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = AsyncAnthropic()

# ==============================================================================
# STRUCTURED OUTPUT & VALIDATION RULES
# ==============================================================================
class UserExtraction(BaseModel):
    name: str
    age: int
    email: str

def validate_business_logic(data: UserExtraction):
    if data.age < 18:
        raise ValueError("Business Rule Violation: Age must be 18 or older.")
    if "@" not in data.email:
        raise ValueError("Business Rule Violation: Invalid email format.")
    return True

EXTRACTION_TOOL = {
    "name": "extract_user",
    "description": "Extract the user's details.",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "email": {"type": "string"}
        },
        "required": ["name", "age", "email"]
    }
}

# ==============================================================================
# WORKFLOW
# ==============================================================================
async def run_validation_retry_api(messy_text: str):
    
    system_prompt = "You are a data extractor. Extract the user's name, age, and email."
    
    # We maintain the conversation history so the LLM sees its past mistakes
    messages = [{"role": "user", "content": messy_text}]
    
    max_retries = 3
    
    for attempt in range(max_retries):
        
        try:
            # Force the model to use the extraction tool
            response = await client.messages.create(
                model=DEFAULT_MODEL,
                max_tokens=1000,
                system=system_prompt,
                messages=messages,
                tools=[EXTRACTION_TOOL],
                tool_choice={"type": "tool", "name": "extract_user"}
            )
        except Exception as e:
            return None
            
        # Append the assistant's response to history
        messages.append({"role": "assistant", "content": response.content})
        
        tool_block = next((b for b in response.content if b.type == 'tool_use'), None)
        if not tool_block:
            messages.append({"role": "user", "content": "You must use the extract_user tool."})
            continue
            
        try:
            # First, check if the LLM output can be parsed into the schema
            parsed = UserExtraction(**tool_block.input)
            
            # Second, run strict business logic validation
            validate_business_logic(parsed)
            return parsed
            
        except (ValidationError, ValueError) as e:
            error_msg = str(e)
            
            # We return an error to the tool call so the LLM knows it failed
            messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "is_error": True,
                    "content": f"Validation Failed: {error_msg}\nPlease fix the data and try again."
                }]
            })
    return None

if __name__ == "__main__":
    req = "My name is Timmy, I am 16 years old, and my email is timmy@example.com."
    asyncio.run(run_validation_retry_api(req))
