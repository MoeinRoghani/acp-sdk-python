#!/usr/bin/env python3
"""
Basic ACP Server Example - Local Testing Version

Demonstrates how to create a simple ACP server to handle incoming requests.
Requires OAuth2 authentication with valid JWT tokens.

To test locally:
1. Configure OAuth2 environment variables
2. Run this server: python basic_server.py  
3. In another terminal, run the client: python ../client/basic_client.py
"""

import datetime
from acp import Server
from acp.models.generated import Message, Part, Role, Type, Type1, Type4, Status, TaskObject


def generate_mock_response(user_content: str) -> str:
    """Generate a mock AI response based on user input"""
    content_lower = user_content.lower()
    
    if "hello" in content_lower or "hi" in content_lower:
        return "Hello! I'm a local test agent. How can I help you today?"
    elif "database" in content_lower:
        return "I found 3 recent database issues: Connection timeouts (resolved), Index optimization needed, and Backup job failing. Would you like details on any specific issue?"
    elif "search" in content_lower:
        return "I've searched the knowledge base and found several relevant articles. Here are the top 3 results with solutions to similar problems."
    elif "ticket" in content_lower or "issue" in content_lower:
        return "I've created a new ticket #TK-2024-001 and assigned it to the appropriate team. You'll receive updates via email."
    elif "help" in content_lower:
        return "I'm here to help! I can assist with database issues, ticket management, knowledge searches, and general support tasks."
    elif "test" in content_lower:
        return "✅ Test successful! This is a mock response from the local ACP test server. Everything is working correctly!"
    else:
        return f"I received your message: '{user_content}'. This is a mock response from the local test server. In a real implementation, I would process your request and provide a meaningful response."


def main():
    """Basic server usage example"""
    
    print("🚀 Starting ACP Local Test Server...")
    print("🔐 Requires OAuth2 authentication with valid JWT tokens")
    print("🛠️  Configure OAuth2 environment variables")
    print()
    
    # Create server instance
    server = Server(
        agent_name="Local Test Agent",
        enable_cors=True,
        enable_logging=True
    )
    

    @server.method_handler("tasks.create")
    async def handle_task_create(params, context):
        """
        Handle incoming task creation requests.
        
        Args:
            params: TasksCreateParams containing the task details
            context: Request context with authentication info
            
        Returns:
            Task creation response
        """
        try:
            print(f"📨 Received task creation request from user: {context.user_id}")
            
            # Extract the initial message
            initial_message = params.initial_message
            user_content = ""
            if initial_message and initial_message.parts:
                for part in initial_message.parts:
                    if part.type == Type.text_part:
                        user_content = part.content or ""
                        break
            
            print(f"💬 User message: {user_content}")
            
            # Generate timestamp
            now_dt = datetime.datetime.now()
            now_iso = now_dt.isoformat() + "Z"
            task_id = f"task-{now_dt.strftime('%Y%m%d-%H%M%S')}"
            
            # Mock AI response based on content
            ai_response = generate_mock_response(user_content)
            
            # Create agent response message
            agent_message = Message(
                role=Role.agent,
                parts=[Part(
                    type=Type.text_part,
                    content=ai_response
                )],
                timestamp=now_dt,
                agentId="local-test-agent"  # Use alias, not agent_id
            )
            
            # Create TaskObject instance using aliased field names
            task_obj = TaskObject(
                taskId=task_id,  # Use alias, not task_id
                status=Status.completed,
                createdAt=now_dt,  # Use alias, not created_at
                updatedAt=now_dt,  # Use alias, not updated_at
                assignedAgent="local-test-agent",  # Use alias, not assigned_agent
                messages=[initial_message, agent_message],
                artifacts=[],
                metadata={
                    "priority": params.priority.value if params.priority else "NORMAL",
                    "source": "local_test_server",
                    "processed_at": now_iso
                }
            )
            
            # Create response with proper Pydantic instances
            task_response = {
                "type": Type1.task,
                "task": task_obj  # Now a TaskObject instance, not dict
            }
            
            print(f"✅ Task {task_id} completed successfully")
            return task_response
            
        except Exception as e:
            print(f"❌ Error in tasks.create handler: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @server.method_handler("tasks.send")
    async def handle_task_send(params, context):
        """Handle sending additional messages to existing tasks"""
        task_id = params.taskId
        message = params.message
        
        print(f"📨 Sending message to task: {task_id}")
        
        # Extract message content
        user_content = ""
        if message and message.parts:
            for part in message.parts:
                if part.type == Type.text_part:
                    user_content = part.content or ""
                    break
        
        print(f"💬 Additional message: {user_content}")
        
        # Generate response to the additional message
        ai_response = generate_mock_response(user_content)
        
        now_dt = datetime.datetime.now()
        
        # Create agent response to the new message
        agent_message = Message(
            role=Role.agent,
            parts=[Part(
                type=Type.text_part,
                content=f"📨 Received additional message for task {task_id}. {ai_response}"
            )],
            timestamp=now_dt,
            agentId="local-test-agent"
        )
        
        # Return task update response
        return {
            "type": Type1.task,
            "task": {
                "taskId": task_id,
                "status": "WORKING",
                "updatedAt": now_dt,
                "newMessage": agent_message
            }
        }

    @server.method_handler("tasks.get")
    async def handle_task_get(params, context):
        """Handle task status requests"""
        task_id = params.taskId
        print(f"📋 Getting status for task: {task_id}")
        
        now_dt = datetime.datetime.now()
        
        # Create mock message for task status
        status_message = Message(
            role=Role.agent,
            parts=[Part(
                type=Type.text_part,
                content=f"✅ Task {task_id} has been completed successfully. This is a mock response for testing."
            )],
            timestamp=now_dt,
            agentId="local-test-agent"  # Use alias, not agent_id
        )
        
        # Create TaskObject instance using aliased field names
        task_obj = TaskObject(
            taskId=task_id,  # Use alias, not task_id
            status=Status.completed,
            createdAt=now_dt,  # Use alias, not created_at
            updatedAt=now_dt,  # Use alias, not updated_at
            assignedAgent="local-test-agent",  # Use alias, not assigned_agent
            messages=[status_message],
            artifacts=[]
        )
        
        # Return proper Pydantic structure
        return {
            "type": Type1.task,
            "task": task_obj  # Now a TaskObject instance, not dict
        }
    
    def has_stream_scope(context):
        """Check if context has required stream scope (uses proper OAuth2 validation)"""
        return context.has_scope('acp:streams:write')

    @server.method_handler("stream.start")
    async def handle_stream_start(params, context):
        """
        Handle stream start requests (mock implementation).
        """
        print("DEBUG context:", context)
        print("DEBUG context dict:", getattr(context, '__dict__', {}))
        try:
            if not has_stream_scope(context):
                raise Exception("Stream operations require 'acp:streams:write' scope (bypassed for dev tokens)")
            stream_id = f"stream-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
            now_dt = datetime.datetime.now()
            stream_obj = {
                "streamId": stream_id,
                "status": "ACTIVE",
                "participants": getattr(params, "participants", [context.user_id]),
                "createdAt": now_dt,
                "metadata": getattr(params, "metadata", {})
            }
            print(f"🟢 Stream started: {stream_id} by {context.user_id}")
            return {"type": "stream", "stream": stream_obj}
        except Exception as e:
            print(f"❌ Error in stream.start handler: {e}")
            import traceback; traceback.print_exc(); raise

    @server.method_handler("stream.message")
    async def handle_stream_message(params, context):
        """
        Handle stream message requests (mock implementation).
        """
        try:
            if not has_stream_scope(context):
                raise Exception("Stream operations require 'acp:streams:write' scope (bypassed for dev tokens)")
            stream_id = getattr(params, "streamId", None)
            message = getattr(params, "message", None)
            print(f"💬 Received stream message for {stream_id} from {context.user_id}: {message}")
            return {"type": "stream_message_ack", "streamId": stream_id}
        except Exception as e:
            print(f"❌ Error in stream.message handler: {e}")
            import traceback; traceback.print_exc(); raise

    @server.method_handler("stream.end")
    async def handle_stream_end(params, context):
        """
        Handle stream end requests (mock implementation).
        """
        try:
            if not has_stream_scope(context):
                raise Exception("Stream operations require 'acp:streams:write' scope (bypassed for dev tokens)")
            stream_id = getattr(params, "streamId", None)
            reason = getattr(params, "reason", "User requested end")
            print(f"🔴 Stream ended: {stream_id} by {context.user_id} (Reason: {reason})")
            return {"type": "stream_end_ack", "streamId": stream_id, "reason": reason}
        except Exception as e:
            print(f"❌ Error in stream.end handler: {e}")
            import traceback; traceback.print_exc(); raise

    @server.method_handler("stream.chunk")
    async def handle_stream_chunk(params, context):
        """
        Handle stream chunk notifications (mock implementation).
        """
        try:
            if not has_stream_scope(context):
                raise Exception("Stream operations require 'acp:streams:write' scope")
            stream_id = getattr(params, "streamId", None)
            chunk = getattr(params, "chunk", None)
            sequence = getattr(params, "sequence", 0)
            is_last = getattr(params, "isLast", False)
            
            # Extract chunk content if it's a message
            chunk_content = "Unknown chunk"
            if chunk and hasattr(chunk, 'parts'):
                for part in chunk.parts:
                    if part.type == Type.text_part:
                        chunk_content = part.content or ""
                        break
            
            print(f"🟣 Stream chunk for {stream_id}: seq={sequence}, last={is_last}")
            print(f"   📦 Chunk content: {chunk_content[:50]}...")
            
            return {
                "type": "stream_chunk_ack", 
                "streamId": stream_id, 
                "sequence": sequence, 
                "isLast": is_last,
                "processed": True
            }
        except Exception as e:
            print(f"❌ Error in stream.chunk handler: {e}")
            import traceback; traceback.print_exc(); raise
    
    # Start the server
    print()
    print("🌐 Server URLs:")
    print("  • Health check: http://localhost:8002/health")
    print("  • Agent info: http://localhost:8002/.well-known/agent.json")
    print("  • JSON-RPC endpoint: http://localhost:8002/jsonrpc")
    print()
    print("🎯 ALL ACP METHODS SUPPORTED:")
    print("   📬 Task Methods:")
    print("     • tasks.create - Create async tasks")
    print("     • tasks.send - Send messages to existing tasks")
    print("     • tasks.get - Get task status and results")
    print("   🔄 Stream Methods:")
    print("     • stream.start - Start real-time streams")
    print("     • stream.message - Send real-time messages")
    print("     • stream.chunk - Send chunked data")
    print("     • stream.end - End streams")
    print()
    print("🔐 OAuth2 scopes required:")
    print("   • acp:agent:identify (all operations)")
    print("   • acp:tasks:write (task creation/sending)")
    print("   • acp:tasks:read (task retrieval)")
    print("   • acp:streams:write (stream operations)")
    print()
    print("🧪 Test with: python ../client/basic_client.py")
    print("⏹️  Press Ctrl+C to stop")
    print()
    
    server.run(host="0.0.0.0", port=8002)


if __name__ == "__main__":
    main()