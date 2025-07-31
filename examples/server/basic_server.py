#!/usr/bin/env python3
"""
Basic ACP Server Example

Demonstrates how to create a simple ACP server to handle incoming requests.
"""

from acp import ACPServer
from acp.models.generated import Message, Part


def main():
    """Basic server usage example"""
    
    # Create server instance
    server = ACPServer(
        agent_name="Example Agent",
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
        # Extract the initial message
        initial_message = params.get("initialMessage", {})
        
        # Simple response - in a real agent, you'd process the request
        task_response = {
            "type": "task",
            "task": {
                "taskId": f"task-{context.request_id}",
                "status": "SUBMITTED",
                "createdAt": "2024-01-15T10:30:00Z",
                "assignedAgent": "example-agent",
                "messages": [initial_message],
                "artifacts": [],
                "metadata": {
                    "priority": params.get("priority", "NORMAL"),
                    "source": "basic_server_example"
                }
            }
        }
        
        return task_response
    
    @server.method_handler("tasks.get")
    async def handle_task_get(params, context):
        """Handle task status requests"""
        task_id = params.get("taskId")
        
        # Simple mock response
        return {
            "type": "task", 
            "task": {
                "taskId": task_id,
                "status": "COMPLETED",
                "createdAt": "2024-01-15T10:30:00Z",
                "updatedAt": "2024-01-15T10:35:00Z",
                "assignedAgent": "example-agent",
                "messages": [
                    {
                        "role": "agent",
                        "parts": [
                            {
                                "type": "TextPart", 
                                "content": f"Task {task_id} has been completed successfully."
                            }
                        ],
                        "timestamp": "2024-01-15T10:35:00Z",
                        "agentId": "example-agent"
                    }
                ],
                "artifacts": []
            }
        }
    
    # Start the server
    print("Starting ACP server on http://localhost:8000")
    print("JSON-RPC endpoint: http://localhost:8000/jsonrpc")
    print("Press Ctrl+C to stop")
    
    server.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main() 