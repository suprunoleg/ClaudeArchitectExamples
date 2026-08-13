"""
Task Statement 4.3: Enforce structured output using tool use and JSON schemas

Knowledge of:
- Tool use (tool_use) with JSON schemas as the most reliable approach for guaranteed schema-compliant structured output
- The distinction between tool_choice: "auto", "any", and forced tool selection
- Schema design considerations: required vs optional fields, enum fields with "other" + detail string patterns

Skills in:
- Defining extraction tools with JSON schemas as input parameters and extracting structured data
- Forcing a specific tool with tool_choice: {"type": "tool", "name": "extract_metadata"}
- Designing schema fields as optional (nullable)
- Adding enum values like "unclear" for ambiguous cases
"""

import os
import asyncio
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage
from dotenv import load_dotenv

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


# ==============================================================================
# STRUCTURED OUTPUT SCHEMAS
# ==============================================================================

class DocumentCategory(str, Enum):
    INVOICE = "invoice"
    CONTRACT = "contract"
    MEMO = "memo"
    UNCLEAR = "unclear"
    OTHER = "other"

class DocumentMetadata(BaseModel):
    category: DocumentCategory = Field(description="The primary category of the document.")
    category_detail: Optional[str] = Field(
        default=None, 
        description="If category is 'other', provide a brief custom string pattern here."
    )
    document_title: str = Field(description="The formal title of the document.")
    # Notice this is Optional (nullable) to prevent the model from hallucinating values if absent
    total_amount: Optional[float] = Field(
        default=None, 
        description="The total financial amount if present. Null if not mentioned."
    )
    entities_involved: List[str] = Field(
        default_factory=list, 
        description="List of companies or people mentioned in the document."
    )

async def extract_metadata(document_text: str):
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        # The SDK's output_format parameter automatically maps to tool_choice={"type": "tool", "name": "..."}
        # and translates the Pydantic model into a strict JSON Schema!
        output_format={
            "type": "json_schema",
            "schema": DocumentMetadata.model_json_schema(),
            # Enforce the specific schema extraction tool
            "name": "extract_metadata" 
        }
    )
    async for message in query(
        prompt=f"Extract metadata from this document:\n\n<document>\n{document_text}\n</document>",
        options=options
    ):
        if isinstance(message, ResultMessage):
            if message.structured_output:
                # Validate the raw dictionary output back into our strict Pydantic model
                metadata = DocumentMetadata.model_validate(message.structured_output)
                return metadata
            else:
                return "Failed to extract structured output."

if __name__ == "__main__":
    test_doc = "This memo is between Acme Corp and Globex. It is a quick reminder about the merger."
    result = asyncio.run(extract_metadata(test_doc))
