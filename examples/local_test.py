#!/usr/bin/env python3
"""
ACP Local Test Runner

Runs both the ACP server and client for easy local testing.
This script demonstrates a complete ACP communication flow.

Usage:
    python local_test.py

What it does:
1. Starts a local ACP server in the background
2. Waits for it to start up
3. Runs the client to test communication
4. Shuts down the server

Requirements:
- Run from the examples/ directory
- Requires acp-sdk-python to be installed
"""

import asyncio
import subprocess
import time
import sys
import signal
import os
from pathlib import Path


def check_server_health(max_attempts=10):
    """Check if the server is running by making HTTP requests"""
    import httpx
    
    for attempt in range(max_attempts):
        try:
            response = httpx.get("http://localhost:8002/health", timeout=1.0)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(0.5)
    return False


async def run_client_test():
    """Run the client test"""
    print("🚀 Running client test...")
    print("=" * 50)
    
    # Import and run the client
    from client.basic_client import main as client_main
    await client_main()


def main():
    """Main test orchestrator"""
    print("🧪 ACP Local Test Runner")
    print("=" * 50)
    print()
    
    # Check if we're in the right directory
    if not Path("client/basic_client.py").exists() or not Path("server/basic_server.py").exists():
        print("❌ Error: Please run this script from the examples/ directory")
        print("   Current directory should contain client/ and server/ folders")
        sys.exit(1)
    
    server_process = None
    
    try:
        # Start the server
        print("🔧 Starting ACP server...")
        server_process = subprocess.Popen(
            [sys.executable, "server/basic_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        if not check_server_health():
            print("❌ Server failed to start")
            if server_process:
                server_process.terminate()
            sys.exit(1)
        
        print("✅ Server is running!")
        print()
        
        # Run client test
        asyncio.run(run_client_test())
        
        print()
        print("=" * 50)
        print("✅ Local test completed successfully!")
        print("💡 You can also test manually:")
        print("   1. Terminal 1: python server/basic_server.py")
        print("   2. Terminal 2: python client/basic_client.py")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        
    finally:
        # Clean up server
        if server_process:
            print("\n🔧 Shutting down server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
            print("✅ Server stopped")


if __name__ == "__main__":
    main()