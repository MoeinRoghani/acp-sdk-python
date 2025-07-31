# ACP Python Examples

This directory contains practical examples demonstrating how to use the ACP Python SDK to build agent communication systems.

## Quick Start

### Prerequisites

1. Python 3.8+
2. Install the ACP Python SDK:
   ```bash
   pip install acp-sdk-python
   ```

## Examples Overview

### 📋 Basic Client (`client/basic_client.py`)

Demonstrates the fundamentals of ACP client usage:

- Create an ACP client
- Connect to a remote agent
- Send a task request
- Handle responses and errors

**Key concepts**: Client initialization, task creation, error handling

### 🖥️ Basic Server (`server/basic_server.py`) 

Shows how to build a simple ACP agent server:

- Create an ACP server
- Register method handlers
- Process incoming requests
- Return structured responses

**Key concepts**: Server setup, method handlers, request processing

### 🎯 Agent Cards (`agent-cards/`)

Example agent capability discovery files:

- **confluence-agent-card.json**: Search agent for Confluence
- **servicenow-agent-card.json**: ServiceNow integration agent

**Key concepts**: Agent discovery, capability declaration, OAuth2 scopes

## Running the Examples

### Client Example

```bash
cd client/
python basic_client.py
```

### Server Example

```bash  
cd server/
python basic_server.py
```

The server will start on `http://localhost:8000` with the JSON-RPC endpoint at `/jsonrpc`.

## Integration Examples

### Client Usage

```python
from acp import ACPClient
from acp.models.generated import TasksCreateParams, Message, Part

client = ACPClient("https://agent.example.com/jsonrpc")

# Create a task
response = await client.tasks_create(
    TasksCreateParams(
        initialMessage=Message(
            role="user", 
            parts=[Part(type="TextPart", content="Hello")]
        )
    )
)
```

### Server Usage

```python
from acp import ACPServer

server = ACPServer()

@server.method_handler("tasks.create")
async def handle_task(params, context):
    return {
        "type": "task",
        "task": {
            "taskId": "task-123",
            "status": "SUBMITTED"
        }
    }

server.run()
```

## Getting Started

1. Install the SDK: `pip install acp-sdk-python`
2. Review the basic examples above
3. Copy and modify examples for your use case
4. Check the [full documentation](https://docs.acp-protocol.org) for advanced features

## Authentication

All examples assume you have valid OAuth2 credentials. See the [authentication guide](https://docs.acp-protocol.org/auth) for setup instructions.

## More Examples

For more advanced examples including:
- Real-time streaming communication
- Multi-agent collaboration
- Complex task workflows
- Production deployment patterns

Visit: [https://github.com/MoeinRoghani/acp-sdk-python/tree/main/examples](https://github.com/MoeinRoghani/acp-sdk-python/tree/main/examples) 