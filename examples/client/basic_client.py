#!/usr/bin/env python3
"""
Basic ACP Client Example - Local Testing Version

Demonstrates how to use the ACP client to communicate with a local test server.

To test locally:
1. Start the server: python ../server/basic_server.py  
2. Run this client: python basic_client.py

Note: This example uses a local HTTP server for testing. In production,
always use HTTPS and real OAuth2 tokens.
"""

import asyncio
from acp import Client
from acp.models.generated import TasksCreateParams, Message, Part, Role, Type


async def main():
    """Basic client usage example for local testing"""
    
    print("🧪 ACP Client Local Test")
    print("Connecting to local test server...")
    print()
    
    # Create client for local testing (allows HTTP)
    # ⚠️ SECURITY WARNING: allow_http=True is ONLY for local testing!
    # In production, always use HTTPS and real OAuth2 tokens
    client = Client(
        base_url="http://localhost:8002",     # Local test server 
        oauth_token="dev-local-test-token",   # Mock token for local testing
        allow_http=True                       # ⚠️ INSECURE: Only for local testing!
    )
    
    # Test different types of messages
    test_messages = [
        "Hello! This is a test message.",
        "Search for recent tickets about database issues",
        "Help me with a technical problem",
        "Create a new ticket for this issue"
    ]
    
    print("🎯 Testing different message types:")
    print()
    
    for i, message_content in enumerate(test_messages, 1):
        print(f"📤 Test {i}: {message_content}")
        
        # Create a task
        task_params = TasksCreateParams(
            initialMessage=Message(
                role=Role.user,
                parts=[Part(
                    type=Type.text_part,
                    content=message_content
                )]
            ),
            priority="NORMAL"
        )
        
        try:
            # Send task to local test agent
            response = await client.tasks_create(task_params)
            
            # Extract task info
            task_data = response.get('task', {})
            task_id = task_data.get('taskId', 'unknown')
            status = task_data.get('status', 'unknown')
            
            print(f"✅ Task created: {task_id} (Status: {status})")
            
            # Get agent response from messages
            messages = task_data.get('messages', [])
            for msg in messages:
                if msg.get('role') == 'agent':
                    parts = msg.get('parts', [])
                    for part in parts:
                        if part.get('type') == 'TextPart':
                            agent_response = part.get('content', '')
                            print(f"🤖 Agent: {agent_response}")
            
            print()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
            break
    
    print("🎉 Local testing completed successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 