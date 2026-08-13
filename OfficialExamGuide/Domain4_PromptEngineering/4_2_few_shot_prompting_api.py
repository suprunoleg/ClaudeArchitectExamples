"""
Task Statement 4.2: Apply few-shot prompting to improve output consistency and quality
(API VERSION)

Knowledge of:
- How to structure few-shot examples using XML tags (`<examples><example>...`).
- When to use few-shot examples (when the output format or tonal voice is very specific).

Skills in:
- Writing a prompt with multiple diverse examples.
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

# ==============================================================================
# ==============================================================================

SYSTEM_PROMPT = """
You are a data normalizer. Convert the user's messy text into a standard CSV format:
Name, Age, Location

<examples>
<example>
<user_input>
My name is John. I am 35 years old and I live in Seattle, WA.
</user_input>
<ideal_output>
John, 35, Seattle
</ideal_output>
</example>

<example>
<user_input>
I'm Sarah. I live in London.
</user_input>
<ideal_output>
Sarah, N/A, London
</ideal_output>
</example>
</examples>

Follow the exact format from the examples. Do not write any other text.
"""

async def run_few_shot_api(messy_text: str):
    
    try:
        response = await client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=50,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": messy_text}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return "[Mock Response expected if dummy key]"

if __name__ == "__main__":
    req = "Hi! I am David. I'm 22 and based out of New York City."
    res = asyncio.run(run_few_shot_api(req))
