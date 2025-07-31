#!/usr/bin/env python3
"""
Basic ACP Server Example - Local Testing Version

Demonstrates how to create a simple ACP server to handle incoming requests.
This version is configured for local testing with mock authentication.

To test locally:
1. Run this server: python basic_server.py
2. In another terminal, run the client: python ../client/basic_client.py
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
    print("📋 Mock OAuth tokens accepted: any token starting with 'dev-'")
    print("🔐 Example: Authorization: Bearer dev-local-test-token")
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
    
    @server.method_handler("tasks.get")
    async def handle_task_get(params, context):
        """Handle task status requests"""
        task_id = params.task_id
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
    
    # Start the server
    print()
    print("🌐 Server URLs:")
    print("  • Health check: http://localhost:8002/health")
    print("  • Agent info: http://localhost:8002/.well-known/agent.json")
    print("  • JSON-RPC endpoint: http://localhost:8002/jsonrpc")
    print()
    print("🧪 Test with client: python ../client/basic_client.py")
    print("⏹️  Press Ctrl+C to stop")
    print()
    
    server.run(host="0.0.0.0", port=8002)


if __name__ == "__main__":
    main() 