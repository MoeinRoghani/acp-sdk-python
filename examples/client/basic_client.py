#!/usr/bin/env python3
"""
Basic ACP Client Example

Demonstrates how to use the ACP client to communicate with remote agents.
"""

import asyncio
from acp import Client
from acp.models.generated import TasksCreateParams, Message, Part


async def main():
    """Basic client usage example"""
    
    # Create client instance
    client = Client(
        base_url="https://confluence-agent.example.com/jsonrpc",
        auth_token="your-oauth2-token-here"
    )
    
    # Create a task
    task_params = TasksCreateParams(
        initialMessage=Message(
            role="user",
            parts=[Part(
                type="TextPart",
                content="Search for recent tickets about database issues"
            )]
        ),
        priority="HIGH"
    )
    
    try:
        # Send task to remote agent
        print("Creating task...")
        response = await client.tasks_create(task_params)
        
        print(f"Task created successfully!")
        print(f"Task ID: {response.get('taskId')}")
        print(f"Status: {response.get('status')}")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 