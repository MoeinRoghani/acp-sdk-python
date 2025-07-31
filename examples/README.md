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

### 🚀 Quick Local Test (Recommended)

Run both server and client together for immediate testing:

```bash
cd examples/
python local_test.py
```

This will:
1. Start the local ACP server
2. Run the client with test messages  
3. Show the complete request/response flow
4. Automatically clean up

### 📋 Manual Testing

#### Server Example

```bash  
cd server/
python basic_server.py
```

The server will start on `http://localhost:8001` with:
- JSON-RPC endpoint: `/jsonrpc`
- Health check: `/health`
- Agent info: `/.well-known/agent.json`

#### Client Example

```bash
cd client/
python basic_client.py
```

**Note**: Start the server first, then run the client in another terminal.

### 🧪 Local Testing Features

The examples are designed for immediate local testing:

#### Mock Authentication
- **Server**: Accepts any OAuth2 token starting with `dev-`
- **Client**: Uses `dev-local-test-token` for testing
- **Validation**: Real OAuth2 validation disabled for local development

#### Intelligent Responses  
The local server provides context-aware mock responses:
- **"hello"** → Greeting message
- **"database"** → Database issue simulation  
- **"search"** → Knowledge base search simulation
- **"ticket"** → Ticket creation simulation
- **"help"** → Help menu
- **"test"** → Test confirmation

#### Security Warnings ⚠️
- **HTTP**: Local examples use HTTP for simplicity (production requires HTTPS)
- **Mock OAuth**: Uses fake tokens (production requires real OAuth2)
- **Development Only**: Never use `allow_http=True` in production

## Integration Examples

### Client Usage

```python
from acp import Client
from acp.models.generated import TasksCreateParams, Message, Part, Role, Type

client = Client("https://agent.example.com")

# Create a task
response = await client.tasks_create(
    TasksCreateParams(
        initialMessage=Message(
            role=Role.user, 
            parts=[Part(type=Type.text_part, content="Hello")]
        )
    )
)
```

### Server Usage

```python
from acp import Server

server = Server()

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

## Security Requirements ⚠️

**ACP Protocol has mandatory security requirements:**

### 🔒 HTTPS Only
- All communication **MUST** use HTTPS (TLS 1.2+)
- HTTP connections are **strictly prohibited**  
- Example: ✅ `https://agent.example.com` ❌ `http://agent.example.com`

### 🛡️ OAuth2 Required  
- All API calls **MUST** include OAuth2 Bearer token
- Either provide `oauth_token` or `oauth_config` 
- Example: `Client(base_url="https://...", oauth_token="your-token")`

### Validation
The SDK automatically validates these requirements and will raise `ValueError` if:
- Base URL doesn't start with `https://`
- No OAuth2 authentication is provided

## Authentication

All examples assume you have valid OAuth2 credentials. See the [authentication guide](https://docs.acp-protocol.org/auth) for setup instructions.

## More Examples

For more advanced examples including:
- Real-time streaming communication
- Multi-agent collaboration
- Complex task workflows
- Production deployment patterns

Visit: [https://github.com/MoeinRoghani/acp-sdk-python/tree/main/examples](https://github.com/MoeinRoghani/acp-sdk-python/tree/main/examples) 