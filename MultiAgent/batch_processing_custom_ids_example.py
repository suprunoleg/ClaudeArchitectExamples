"""
Batch Processing with Custom IDs

Shows how to efficiently process multiple independent tasks (batching) while
tracking them using custom identifiers. This asynchronous approach is
essential for scaling LLM workflows to handle thousands of documents
concurrently.
"""

import os
import re
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"

client = Anthropic()

# The strict regex constraint from the Message Batches API
# (Only alphanumeric, hyphens, and underscores allowed, max 64 chars)
VALID_CUSTOM_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

def generate_valid_custom_id(original_filename: str, index: int) -> str:
    """
    Sanitizes a filename or string to be a valid custom_id for the Anthropic Batch API.
    """
    # Replace invalid characters (like spaces, colons, hashes) with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', original_filename)
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "doc_unknown"
        
    # Append the index to guarantee uniqueness within the batch
    # We must leave room for the suffix so we truncate to 50 chars max before appending
    unique_id = f"{sanitized[:50]}_idx{index}"
    
    return unique_id

def run_batch_example():
    print(f"\n{'='*80}")
    print("ANTHROPIC MESSAGE BATCHES API - CUSTOM ID CORRELATION")
    print(f"{'='*80}\n")
    
    # 1. A list of raw document names/identifiers that need translation.
    # Notice these violate the Batch API constraints (spaces, colons, hashes, length).
    raw_documents = [
        "doc 2026 report final v2",              # Invalid: spaces
        "doc/2026/report:final",                 # Invalid: slashes, colons
        "doc#2026#report#final#v2",              # Invalid: hashes
        "doc-2026-report_final",                 # Valid! (This matches the correct answer)
        "this_is_an_extremely_long_document_name_that_exceeds_sixty_four_characters_limit_by_a_lot_v3" # Invalid: too long
    ]
    
    # 2. Maintain a local mapping of custom_id -> original context.
    # This is how you correlate the asynchronous batch results back to your system.
    local_database_mapping = {}
    batch_requests = []
    
    print("STEP 1: Preparing batch requests and sanitizing IDs...\n")
    
    for i, doc_name in enumerate(raw_documents):
        # Sanitize the ID to comply with ^[a-zA-Z0-9_-]{1,64}$
        custom_id = generate_valid_custom_id(doc_name, i)
        
        # Verify it passes the regex
        is_valid = bool(VALID_CUSTOM_ID_REGEX.match(custom_id))
        
        status = "Valid" if is_valid else "Invalid"
        print(f"Original : '{doc_name}'")
        print(f"Sanitized: '{custom_id}' [{status}]\n")
        
        if is_valid:
            # Store in our local mapping for later correlation
            local_database_mapping[custom_id] = {
                "original_filename": doc_name,
                "status": "pending"
            }
            
            # Construct the API request object
            batch_requests.append({
                "custom_id": custom_id,
                "params": {
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 500,
                    "system": "You are a professional translator. Translate the text to French.",
                    "messages": [
                        {"role": "user", "content": f"Please translate the contents of {doc_name}."}
                    ]
                }
            })
            
    print(f"{'-'*80}")
    print(f"Created {len(batch_requests)} valid batch requests.")
    print(f"{'-'*80}\n")
    
    # 3. Submitting the batch to Anthropic
    print("STEP 2: Submitting batch to Anthropic API...\n")
    try:
        # In a real environment with a valid key, this creates the batch.
        batch = client.messages.batches.create(
            requests=batch_requests
        )
        print(f"Batch created successfully! Batch ID: {batch.id}")
        print(f"Batch Status: {batch.processing_status}")
        
    except Exception as e:
        print(f"Could not submit batch (expected if using dummy API key):\n{e}\n")
        print("Moving on to demonstrate correlation...\n")

    print(f"{'='*80}")
    print("STEP 3: POLLING & ASYNCHRONOUS RESULT CORRELATION")
    print(f"{'='*80}")
    print("We will now poll the API to wait for the batch to complete.")
    print("The results will return out of order, so we MUST use the custom_id to match them up.\n")
    
    import time
    
    # Poll until the batch completes (or we hit a timeout for this example)
    max_polls = 10
    poll_interval = 10 # seconds
    
    for attempt in range(max_polls):
        batch = client.messages.batches.retrieve(batch.id)
        status = batch.processing_status
        print(f"Poll {attempt+1}/{max_polls} - Status: {status}")
        
        if status == "ended":
            print("\nBatch processing completed!")
            break
        elif status in ["canceled", "expired"]:
            print(f"\nBatch processing stopped with status: {status}")
            return
            
        time.sleep(poll_interval)
    else:
        print("\nBatch is taking longer than expected for this quick demo.")
        print("In a real application, you would continue polling or use webhooks.")
        return
        
    print("\nRetrieving results and correlating...\n")
    
    # client.messages.batches.results() returns an iterator of JSONL records
    results_iterator = client.messages.batches.results(batch.id)
    
    for result_record in results_iterator:
        c_id = result_record.custom_id
        
        # Correlate!
        if c_id in local_database_mapping:
            original = local_database_mapping[c_id]["original_filename"]
            print(f"Matched Result for custom_id '{c_id}'!")
            print(f"   -> Correlates to original file: '{original}'")
            
            if result_record.result.type == "succeeded":
                # Extract the translation
                translated_text = result_record.result.message.content[0].text
                print(f"   -> Translation snippet: '{translated_text[:40]}...'")
            else:
                print(f"   -> Translation failed: {result_record.result.error}")
            print()

if __name__ == "__main__":
    run_batch_example()
