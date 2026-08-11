"""
Native Citations

Demonstrates how to use Anthropic's native citation features to ground model
responses in specific documents and retrieve exact quotes. This feature is
critical for building trustworthy RAG applications where users need to verify
the source of the model's claims.
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

def demonstrate_native_citations():
    """
    Demonstrates Claude's Native Citations API on a plain text document.
    Notice how we don't have to write a complex prompt asking it to "quote its sources".
    We simply provide a document block and set citations.enabled = True.
    """
    print(f"{'='*80}")
    print("NATIVE CITATIONS API EXAMPLE (char_location)")
    print(f"{'='*80}\n")
    
    # 1. The Source Document
    source_text = """
    Acme Corp Financial Report Q3 2023.
    Revenue increased by 15% to $4.2 million.
    Operating costs were reduced by 5% due to the new cloud infrastructure.
    The CEO, Jane Doe, stated that Q4 will focus on AI expansion.
    """
    
    print("1. Sending Request with Native Citations Enabled...")
    
    # 2. API Request
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
                            "data": source_text
                        },
                        "title": "Q3 Financials",
                        
                        #  THE ARCHITECTURAL SWITCH 
                        # This turns on native citations for this document
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
    
    print("2. Parsing the structured response blocks...\n")
    print(f"{'-'*40}")
    print("GENERATED RESPONSE WITH CITATIONS:")
    print(f"{'-'*40}\n")
    
    # 3. Parsing the Structured Output
    # The API returns a list of TextBlocks, some of which contain embedded Citation objects
    for block in response.content:
        # Print the generated text chunk
        print(block.text, end="")
        
        # If this chunk is backed by a citation, print the exact citation metadata!
        if getattr(block, "citations", None):
            for cit in block.citations:
                print(f"\n    [CITATION: {cit.document_title}]")
                # Because it's plain text, we get exact character offsets
                if cit.type == "char_location":
                    print(f"       (Chars {cit.start_char_index}-{cit.end_char_index})")
                print(f"       Exact Source Text: \"{cit.cited_text.strip()}\"\n", end="")
                
    print("\n\n" + "="*80)
    print("ARCHITECTURAL TAKEAWAY:")
    print("Notice how Claude seamlessly interweaves plain text blocks with cited text blocks.")
    print("The cited_text field is provided for convenience and does NOT bill as output tokens!")
    print("="*80)


if __name__ == "__main__":
    demonstrate_native_citations()
