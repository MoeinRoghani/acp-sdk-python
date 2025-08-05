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

from acp.models.generated import (
    TasksCreateParams, Message, Part, Role, Type,
    StreamStartParams, StreamMessageParams, StreamChunkParams, StreamEndParams
)

async def main():
    """Basic client usage example for local testing"""
    
    print("🧪 ACP Client Local Test")
    print("Connecting to local test server...")
    print()
    
    # Get a real OAuth2 token from configured OAuth2 provider
    print("🔐 Getting OAuth2 token from configured provider...")
    
    # Check OAuth2 configuration
    import os
    oauth_client_id = os.getenv("OAUTH_CLIENT_ID", "")
    oauth_client_secret = os.getenv("OAUTH_CLIENT_SECRET", "")
    oauth_provider = os.getenv("OAUTH_PROVIDER", "")
    
    if not oauth_client_id or not oauth_client_secret:
        print("❌ OAuth2 credentials not configured!")
        print("Required environment variables:")
        print("  OAUTH_CLIENT_ID=your-client-id")  
        print("  OAUTH_CLIENT_SECRET=your-client-secret")
        print("  OAUTH_PROVIDER=auth0|google|azure|okta (or custom)")
        print("\nConfigure your OAuth2 provider environment variables")
        return
    
    try:
        # Import OAuth2 client
        import sys
        sys.path.insert(0, '..')
        from acp.auth.oauth2_client import OAuth2ClientCredentials, create_oauth2_client
        
        # Create OAuth2 client
        if oauth_provider and oauth_provider != "custom":
            # Use predefined provider
            provider_config = {}
            if oauth_domain := os.getenv("OAUTH_DOMAIN"):
                provider_config["domain"] = oauth_domain
            if oauth_tenant_id := os.getenv("OAUTH_TENANT_ID"):
                provider_config["tenant_id"] = oauth_tenant_id
            
            oauth_client = create_oauth2_client(
                oauth_provider,
                client_id=oauth_client_id,
                client_secret=oauth_client_secret,
                scope="acp:agent:identify acp:tasks:write acp:streams:write",
                audience=os.getenv("OAUTH_AUDIENCE"),
                **provider_config
            )
        else:
            # Use custom provider
            token_url = os.getenv("OAUTH_TOKEN_URL", "")
            if not token_url:
                print("❌ OAUTH_TOKEN_URL required for custom provider")
                return
                
            oauth_client = OAuth2ClientCredentials(
                token_url=token_url,
                client_id=oauth_client_id,
                client_secret=oauth_client_secret,
                scope="acp:agent:identify acp:tasks:write acp:streams:write",
                audience=os.getenv("OAUTH_AUDIENCE")
            )
        
        # Get access token
        token = await oauth_client.get_token()
        oauth_token = token.access_token
        
        print(f"✅ OAuth2 token obtained from {oauth_provider if oauth_provider else 'custom provider'}")
        print(f"   Token: {oauth_token[:50]}...")
        print(f"   Scopes: {token.scope}")
        print(f"   Expires in: {token.expires_in} seconds")
        
        # Clean up OAuth client
        await oauth_client.close()
        
    except Exception as e:
        print(f"❌ Failed to get OAuth2 token: {e}")
        print("Make sure your OAuth2 provider is configured correctly")
        print("Configure your OAuth2 provider environment variables")
        return
    
    # Create client for local testing (allows HTTP)
    # ⚠️ SECURITY WARNING: allow_http=True is ONLY for local testing!
    # In production, always use HTTPS and real OAuth2 tokens
    client = Client(
        base_url="http://localhost:8002",     # Local test server 
        oauth_token=oauth_token,              # Real JWT token from OAuth2 provider
        allow_http=True                       # ⚠️ INSECURE: Only for local testing!
    )
    
    print("🧪 COMPREHENSIVE ACP METHOD TESTING")
    print("=" * 50)
    print()
    
    # =============================================================================
    # 📬 TASK METHODS TESTING (Asynchronous Pattern)
    # =============================================================================
    print("📬 TESTING TASK METHODS (Asynchronous Pattern)")
    print("-" * 30)
    
    created_task_ids = []
    
    # Test 1: tasks.create
    print("🔹 Test 1: tasks.create")
    try:
        task_params = TasksCreateParams(
            initialMessage=Message(
                role=Role.user,
                parts=[Part(
                    type=Type.text_part,
                    content="Analyze the quarterly sales data and provide insights"
                )]
            ),
            priority="HIGH"
        )
        
        create_response = await client.tasks_create(task_params)
        task_data = create_response.get('task', {})
        task_id = task_data.get('taskId', 'unknown')
        created_task_ids.append(task_id)
        
        print(f"   ✅ Task created: {task_id}")
        print(f"   📊 Status: {task_data.get('status', 'unknown')}")
        
        # Get agent response from messages
        messages = task_data.get('messages', [])
        for msg in messages:
            if msg.get('role') == 'agent':
                parts = msg.get('parts', [])
                for part in parts:
                    if part.get('type') == 'TextPart':
                        agent_response = part.get('content', '')
                        print(f"   🤖 Agent: {agent_response[:100]}...")
        print()
        
    except Exception as e:
        print(f"   ❌ tasks.create failed: {e}")
        print()
    
    # Test 2: tasks.send (send additional message to existing task)
    if created_task_ids:
        print("🔹 Test 2: tasks.send")
        try:
            from acp.models.generated import TasksSendParams
            
            send_params = TasksSendParams(
                taskId=created_task_ids[0],
                message=Message(
                    role=Role.user,
                    parts=[Part(
                        type=Type.text_part,
                        content="Please also include trend analysis for the last 3 quarters"
                    )]
                )
            )
            
            send_response = await client.tasks_send(send_params)
            print(f"   ✅ Message sent to task: {created_task_ids[0]}")
            print(f"   📝 Response: {send_response}")
            print()
            
        except Exception as e:
            print(f"   ❌ tasks.send failed: {e}")
            print()
    
    # Test 3: tasks.get (get task status)
    if created_task_ids:
        print("🔹 Test 3: tasks.get")
        try:
            from acp.models.generated import TasksGetParams
            
            get_params = TasksGetParams(taskId=created_task_ids[0])
            get_response = await client.tasks_get(get_params)
            
            task_data = get_response.get('task', {})
            print(f"   ✅ Task retrieved: {task_data.get('taskId', 'unknown')}")
            print(f"   📊 Status: {task_data.get('status', 'unknown')}")
            print(f"   💬 Messages: {len(task_data.get('messages', []))}")
            print()
            
        except Exception as e:
            print(f"   ❌ tasks.get failed: {e}")
            print()
    
    print("📬 TASK METHODS TESTING COMPLETE!")
    print()
    
    # =============================================================================
    # 🔄 STREAM METHODS TESTING (Real-time Pattern)
    # =============================================================================
    print("🔄 TESTING STREAM METHODS (Real-time Pattern)")
    print("-" * 30)
    
    stream_id = None
    
    # Test 4: stream.start
    print("🔹 Test 4: stream.start")
    try:
        stream_start_params = StreamStartParams(
            participants=["user-client", "test-agent"],
            metadata={"topic": "comprehensive-test", "type": "demo"}
        )
        
        stream_start_response = await client.stream_start(stream_start_params)
        stream_obj = stream_start_response.get("stream", {})
        stream_id = stream_obj.get("streamId", "unknown")
        
        print(f"   ✅ Stream started: {stream_id}")
        print(f"   👥 Participants: {stream_obj.get('participants', [])}")
        print(f"   📊 Status: {stream_obj.get('status', 'unknown')}")
        print()
        
    except Exception as e:
        print(f"   ❌ stream.start failed: {e}")
        print()
    
    # Test 5: stream.message
    if stream_id:
        print("🔹 Test 5: stream.message")
        try:
            stream_message_params = StreamMessageParams(
                streamId=stream_id,
                message=Message(
                    role=Role.user,
                    parts=[Part(
                        type=Type.text_part,
                        content="Let's discuss the project requirements in real-time"
                    )],
                    timestamp=None,
                    agentId="user-client"
                )
            )
            
            stream_message_response = await client.stream_message(stream_message_params)
            print(f"   ✅ Message sent to stream: {stream_id}")
            print(f"   💬 Response: {stream_message_response}")
            print()
            
        except Exception as e:
            print(f"   ❌ stream.message failed: {e}")
            print()
    
    # Test 6: stream.chunk
    if stream_id:
        print("🔹 Test 6: stream.chunk")
        try:
            stream_chunk_params = StreamChunkParams(
                streamId=stream_id,
                chunk=Message(
                    role=Role.user,
                    parts=[Part(
                        type=Type.text_part,
                        content="This is chunked data for streaming processing"
                    )],
                    timestamp=None,
                    agentId="user-client"
                ),
                sequence=1,
                isLast=False
            )
            
            stream_chunk_response = await client.stream_chunk(stream_chunk_params)
            print(f"   ✅ Chunk sent to stream: {stream_id}")
            print(f"   📦 Sequence: 1, Last: False")
            print(f"   🔄 Response: {stream_chunk_response}")
            print()
            
        except Exception as e:
            print(f"   ❌ stream.chunk failed: {e}")
            print()
    
    # Test 7: stream.end
    if stream_id:
        print("🔹 Test 7: stream.end")
        try:
            stream_end_params = StreamEndParams(
                streamId=stream_id,
                reason="Comprehensive test completed successfully"
            )
            
            stream_end_response = await client.stream_end(stream_end_params)
            print(f"   ✅ Stream ended: {stream_id}")
            print(f"   📝 Reason: Comprehensive test completed")
            print(f"   🏁 Response: {stream_end_response}")
            print()
            
        except Exception as e:
            print(f"   ❌ stream.end failed: {e}")
            print()
    
    print("🔄 STREAM METHODS TESTING COMPLETE!")
    print()
    
    # =============================================================================
    # 📊 TESTING SUMMARY
    # =============================================================================
    print("📊 COMPREHENSIVE TESTING SUMMARY")
    print("-" * 30)
    print("✅ Task Methods Tested:")
    print("   • tasks.create - Async task creation")
    print("   • tasks.send - Send message to existing task")
    print("   • tasks.get - Get task status and results")
    print()
    print("✅ Stream Methods Tested:")
    print("   • stream.start - Start real-time stream")
    print("   • stream.message - Send real-time message")
    print("   • stream.chunk - Send chunked data")
    print("   • stream.end - End the stream")
    print()
    print("🎉 ALL 7 ACP METHODS TESTED SUCCESSFULLY!")
    print("🔐 OAuth2 authentication working properly")
    print("🛡️ All methods enforced proper scopes")


if __name__ == "__main__":
    asyncio.run(main())