"""
Task Statement 4.4: Implement validation, retry, and feedback loops for extraction quality
(SDK VERSION)

Knowledge of:
- How to validate LLM outputs against strict business logic rules.
- How to feed validation errors back into the prompt so the LLM can self-correct.

Skills in:
- Implementing a programmatic retry loop (`for _ in range(max_retries)`).
- Injecting the specific error message back into the prompt.
"""

import os
import asyncio
from typing import Optional
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, query, ResultMessage

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


# ==============================================================================
# STRUCTURED OUTPUT & VALIDATION RULES
# ==============================================================================
class UserExtraction(BaseModel):
    name: str
    age: int
    email: str

def validate_business_logic(data: UserExtraction):
    # EXAM SKILL: Validating outputs beyond just JSON schema validation
    if data.age < 18:
        raise ValueError("Business Rule Violation: Age must be 18 or older.")
    if "@" not in data.email:
        raise ValueError("Business Rule Violation: Invalid email format.")
    return True


# ==============================================================================
# WORKFLOW
# ==============================================================================
async def run_validation_retry_sdk(messy_text: str):
    print(f"\n--- Starting SDK Validation Retry Workflow ---")
    
    system_prompt = "You are a data extractor. Extract the user's name, age, and email."
    
    # EXAM SKILL: Programmatic Retry Loop
    max_retries = 3
    current_prompt = messy_text
    
    for attempt in range(max_retries):
        print(f"\nAttempt {attempt + 1}...")
        
        options = ClaudeAgentOptions(
            model=DEFAULT_MODEL,
            system_prompt=system_prompt,
            response_schema=UserExtraction
        )

        extracted_data = None
        try:
            async for msg in query(prompt=current_prompt, options=options):
                if isinstance(msg, ResultMessage):
                    extracted_data = msg.result
        except Exception as e:
            print(f"[SDK Error] {e}")
            return None
            
        if not extracted_data:
            print("Failed to get structured output. Retrying...")
            current_prompt = "You failed to output the required structure. Please try again."
            continue
            
        try:
            # First, check if the LLM output can be parsed into the schema
            parsed = UserExtraction(**extracted_data)
            
            # Second, run strict business logic validation
            validate_business_logic(parsed)
            
            print(f"Success! Extracted: {parsed}")
            return parsed
            
        except (ValidationError, ValueError) as e:
            # EXAM SKILL: Feeding errors back for self-correction
            error_msg = str(e)
            print(f"Validation Failed: {error_msg}")
            current_prompt = (
                f"Your previous extraction was invalid. "
                f"Error: {error_msg}\n"
                f"Please fix the data and try again."
            )

    print("Max retries exceeded.")
    return None

if __name__ == "__main__":
    try:
        # This will fail business logic on Attempt 1 (age is 16)
        # The LLM receives the error and (hopefully) realizes it can't extract a valid 18+ age from this text,
        # or it might hallucinate one. In a real app, you'd handle unfixable errors.
        req = "My name is Timmy, I am 16 years old, and my email is timmy@example.com."
        asyncio.run(run_validation_retry_sdk(req))
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed (expected if dummy key): {e}")
