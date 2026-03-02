"""
Test MCP stdio communication - CRITICAL for debugging hangs.

This test verifies that:
1. Server starts without printing to stdout
2. JSON-RPC messages flow correctly
3. No stdout corruption occurs
"""

import asyncio
import subprocess
import json
import sys
import time


def test_mcp_stdio():
    """Test MCP server stdio communication."""
    print("Testing MCP stdio communication...", file=sys.stderr)
    
    # Start server
    process = subprocess.Popen(
        [sys.executable, "-m", "backend.mcp_broker.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    try:
        # Give server time to start
        time.sleep(2)
        
        # Check if server is still running
        if process.poll() is not None:
            stderr = process.stderr.read()
            print(f"Server crashed! stderr: {stderr}", file=sys.stderr)
            return False
        
        print("Server started successfully", file=sys.stderr)
        
        # Send initialize request (MCP protocol)
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }
        
        request_str = json.dumps(init_request)
        print(f"Sending: {request_str}", file=sys.stderr)
        
        process.stdin.write(request_str + "\n")
        process.stdin.flush()
        
        # Read response (with timeout)
        print("Waiting for response...", file=sys.stderr)
        import select
        
        ready, _, _ = select.select([process.stdout], [], [], 10)
        if not ready:
            print("TIMEOUT: No response from server", file=sys.stderr)
            return False
        
        response_line = process.stdout.readline()
        print(f"Received: {response_line}", file=sys.stderr)
        
        # Try to parse as JSON
        try:
            response = json.loads(response_line)
            print(f"Parsed response: {response}", file=sys.stderr)
            
            if "result" in response or "error" in response:
                print("✓ Valid JSON-RPC response received!", file=sys.stderr)
                return True
            else:
                print("✗ Invalid JSON-RPC response", file=sys.stderr)
                return False
                
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON: {e}", file=sys.stderr)
            print(f"Raw response: {repr(response_line)}", file=sys.stderr)
            return False
            
    finally:
        process.terminate()
        try:
            process.wait(timeout=2)
        except:
            process.kill()


if __name__ == "__main__":
    success = test_mcp_stdio()
    sys.exit(0 if success else 1)
