"""
Task Statement 2.4: Integrate MCP servers into Claude Code and agent workflows
(SDK VERSION)

Knowledge of:
- The difference between in-process MCP SDK servers and external stdio/SSE servers.
- Environment variable expansion and credential management.

Skills in:
- Configuring agent workflows to use external MCP servers over stdio.
- Passing MCP server credentials securely.
"""

import os
import asyncio
from dotenv import load_dotenv

from claude_agent_sdk import ClaudeAgentOptions, query, ResultMessage

# Constants
DEFAULT_MODEL = "claude-haiku-4-5"

# Load environment variables
load_dotenv()
if "ANTHROPIC_API_KEY" not in os.environ:
    os.environ["ANTHROPIC_API_KEY"] = "dummy_key"


# ==============================================================================
# EXAM SKILL: Integrating external stdio MCP servers
# ==============================================================================
# Unlike `create_sdk_mcp_server()` which runs in the same Python process,
# a true MCP server runs externally and communicates over stdio or SSE.

async def run_mcp_integration_sdk(user_request: str):
    print("\n--- Starting SDK MCP Integration Workflow ---")
    
    # In a production app, this would point to a real installed MCP server like PostgreSQL
    postgres_mcp_config = {
        "command": "npx",
        "args": [
            "-y",
            "@modelcontextprotocol/server-postgres",
            # EXAM SKILL: Securely passing credentials using environment variables
            # NEVER hardcode the database URL in the configuration block.
            os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost/mockdb")
        ],
        "env": {
            # Any specific environment variables the server needs
            "PGPASSWORD": os.environ.get("PGPASSWORD", "mock_pass")
        }
    }
    
    options = ClaudeAgentOptions(
        model=DEFAULT_MODEL,
        # Connecting the external server to the Claude Agent SDK
        mcp_servers={
            "postgres_server": postgres_mcp_config
        }
    )

    try:
        final_output = None
        async for msg in query(prompt=user_request, options=options):
            if isinstance(msg, ResultMessage):
                final_output = msg.result
        return final_output
    except Exception as e:
        # We expect this to fail if `npx` isn't installed or the server doesn't exist
        pass

if __name__ == "__main__":
    try:
        req = "Query the PostgreSQL database for the top 5 users."
        res = asyncio.run(run_mcp_integration_sdk(req))
        print(f"\n[Agent Response]\n{res}")
    except Exception as e:
        print(f"\n[SYSTEM] Run complete or failed: {e}")
