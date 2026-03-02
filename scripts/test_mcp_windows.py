"""
Test MCP stdio communication - Windows compatible version.
"""

import asyncio
import subprocess
import json
import sys
import time
import threading
import queue


def read_output(pipe, output_queue):
    """Read output from pipe in separate thread."""
    try:
        for line in iter(pipe.readline, ''):
            output_queue.put(('stdout', line.strip()))
    except:
        pass
    finally:
        pipe.close()


def read_errors(pipe, error_queue):
    """Read stderr in separate thread."""
    try:
        for line in iter(pipe.readline, ''):
            error_queue.put(line.strip())
    except:
        pass
    finally:
        pipe.close()


def test_mcp_stdio():
    """Test MCP server stdio communication (Windows compatible)."""
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
    
    # Queues for communication
    stdout_queue = queue.Queue()
    stderr_queue = queue.Queue()
    
    # Start reader threads
    stdout_thread = threading.Thread(target=read_output, args=(process.stdout, stdout_queue))
    stderr_thread = threading.Thread(target=read_errors, args=(process.stderr, stderr_queue))
    stdout_thread.daemon = True
    stderr_thread.daemon = True
    stdout_thread.start()
    stderr_thread.start()
    
    try:
        # Give server time to start
        time.sleep(2)
        
        # Check if server is still running
        if process.poll() is not None:
            print("Server crashed on startup!", file=sys.stderr)
            # Collect stderr
            time.sleep(0.5)
            errors = []
            while not stderr_queue.empty():
                errors.append(stderr_queue.get())
            print(f"Server errors:\n{'\n'.join(errors)}", file=sys.stderr)
            return False
        
        print("Server started successfully", file=sys.stderr)
        
        # Print any startup logs from stderr
        time.sleep(0.5)
        startup_logs = []
        while not stderr_queue.empty():
            startup_logs.append(stderr_queue.get())
        if startup_logs:
            print("Server startup logs:", file=sys.stderr)
            for log in startup_logs:
                print(f"  {log}", file=sys.stderr)
        
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
        
        # Wait for response
        print("Waiting for response (timeout 10s)...", file=sys.stderr)
        
        response_line = None
        timeout = time.time() + 10
        
        while time.time() < timeout:
            try:
                source, line = stdout_queue.get(timeout=0.1)
                if source == 'stdout' and line:
                    response_line = line
                    break
            except queue.Empty:
                # Check stderr for any errors
                try:
                    err = stderr_queue.get_nowait()
                    print(f"Server log: {err}", file=sys.stderr)
                except queue.Empty:
                    pass
                continue
        
        if not response_line:
            print("TIMEOUT: No response from server", file=sys.stderr)
            return False
        
        print(f"Received: {response_line}", file=sys.stderr)
        
        # Try to parse as JSON
        try:
            response = json.loads(response_line)
            print(f"Parsed response: {json.dumps(response, indent=2)}", file=sys.stderr)
            
            if "result" in response or "error" in response:
                print("✓ VALID JSON-RPC response received!", file=sys.stderr)
                return True
            else:
                print("✗ Invalid JSON-RPC response (no result or error)", file=sys.stderr)
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
