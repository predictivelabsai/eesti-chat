"""Issue API keys: `python -m mcp_server.keys new` prints a key and its hash.

Give the key to the client; append ONLY the hash to MCP_API_KEY_HASHES (comma-separated).
"""

import secrets
import sys

from mcp_server.auth import hash_key

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "hash":
        print(hash_key(sys.argv[2]))
    else:
        key = "ek_" + secrets.token_urlsafe(32)
        print(f"key:  {key}\nhash: {hash_key(key)}")
