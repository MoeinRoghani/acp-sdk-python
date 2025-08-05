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

#### OAuth2 Authentication

The examples demonstrate production-ready OAuth2 authentication using real OAuth2 providers:

**Supported OAuth2 Providers:**
- **Auth0**: Enterprise identity platform
- **Google OAuth2**: Google Cloud and workspace authentication
- **Azure AD**: Microsoft Azure Active Directory
- **Okta**: Enterprise identity management
- **Custom**: Any OAuth2 provider with JWKS endpoint

**OAuth2 Flow:**
- **Client Credentials Grant**: Machine-to-machine authentication
- **JWT Token Validation**: JWKS-based signature verification
- **Scope Enforcement**: Fine-grained permission control
- **Token Caching**: Automatic token refresh and management

**Required Scopes:**
- **All operations** require `acp:agent:identify` scope
- **`tasks.create`** & **`tasks.send`** require `acp:tasks:write`
- **`tasks.get`** requires `acp:tasks:read`  
- **`tasks.cancel`** requires `acp:tasks:cancel`
- **`tasks.subscribe`** requires `acp:notifications:receive`
- **Stream write operations** require `acp:streams:write`
- **Stream read operations** require `acp:streams:read`

**Setup Guide:**
```bash
# Configure your OAuth2 provider (example for Auth0)
export OAUTH_PROVIDER=auth0
export OAUTH_DOMAIN=your-domain.auth0.com
export OAUTH_CLIENT_ID=your-client-id
export OAUTH_CLIENT_SECRET=your-secret
export OAUTH_AUDIENCE=https://your-api.com

# Test the client
python client/basic_client.py
```

#### Intelligent Responses  
The local server provides context-aware mock responses:
- **"hello"** → Greeting message
- **"database"** → Database issue simulation  
- **"search"** → Knowledge base search simulation
- **"ticket"** → Ticket creation simulation
- **"help"** → Help menu
- **"test"** → Test confirmation

#### 🔒 Security Configuration

**Security Features:**
- 🔒 **OAuth2 Required**: All endpoints require valid OAuth2 authentication
- 🔑 **JWT Validation**: Proper token signature and expiration checking
- 📋 **Scope Enforcement**: Fine-grained permission control per operation
- 📝 **Audit Logging**: All authentication decisions logged for monitoring

#### Security Warnings ⚠️
- **HTTP**: Local examples use HTTP for simplicity (production requires HTTPS)
- **OAuth2 Required**: All operations require valid OAuth2 tokens
- **Development Only**: Never use `allow_http=True` in production
- **Token Security**: JWT tokens have expiration and proper validation

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