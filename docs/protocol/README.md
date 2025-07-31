# ACP Agent Communication Protocol

## Overview

**ACP** (Agent Communication Protocol) is a comprehensive JSON-RPC 2.0-based protocol designed for sophisticated agent-to-agent communication. It provides both asynchronous task delegation and real-time streaming conversations, enabling AI agents to collaborate effectively while maintaining security, scalability, and reliability.

## 🚀 Key Features

- **JSON-RPC 2.0 Foundation**: Standardized request/response patterns with built-in error handling
- **Dual Communication Patterns**: Async tasks for long-running operations + real-time streams for collaboration
- **Multimodal Content**: Rich support for text, files, images, audio, and structured data
- **Enterprise Security**: OAuth 2.0 authentication with HTTPS-only transport
- **Webhook Notifications**: Real-time event delivery for task lifecycle management
- **Comprehensive Documentation**: Full OpenAPI 3.0 specification with examples

## 📁 Repository Structure

```
acp-schema/
├── acp-openapi3.yaml                     # Main OpenAPI 3.0 specification
├── ACP-JSON-RPC-Foundation.md           # Core JSON-RPC 2.0 implementation
├── ACP-Task-Management.md               # Async task delegation system
├── ACP-Stream-Management.md             # Real-time streaming communication
├── ACP-Shared-Communication.md          # Message, Part, and Artifact schemas
├── ACP-Response-Management.md           # Unified response handling
└── README.md                            # This file
```

## 🔧 Core Components

### 1. JSON-RPC Foundation
- Standardized request/response envelopes
- Comprehensive error handling with custom ACP codes
- OAuth 2.0 + HTTPS security requirements
- Correlation IDs for async operations

### 2. Task Management (Async)
- **Use Case**: Long-running operations (data analysis, report generation)
- **Pattern**: Fire-and-forget with lifecycle tracking
- **Features**: Status progression, conversation history, artifact generation
- **Methods**: `tasks.create`, `tasks.send`, `tasks.get`, `tasks.cancel`, `tasks.subscribe`

### 3. Stream Management (Real-time)
- **Use Case**: Interactive collaboration, live assistance
- **Pattern**: Bidirectional real-time communication
- **Features**: Multi-participant sessions, chunk-based delivery
- **Methods**: `stream.start`, `stream.message`, `stream.end`, `stream.chunk`

### 4. Shared Communication
- **Message**: Universal communication envelope (user/agent/system roles)
- **Part**: Multimodal content blocks (text, data, files, images, audio)
- **Artifact**: Structured deliverables with rich metadata

### 5. Response Management
- **MethodResult**: Unified response wrapper with type discrimination
- **SubscriptionObject**: Webhook management for notifications

## 🛡️ Security Model

### Authentication
- **OAuth 2.0**: Required for all operations
- **Client Credentials**: Machine-to-machine agent communication
- **Authorization Code**: User-delegated agent operations

### Required Scopes
```
acp:agent:identify       # Basic agent identification (required)
acp:tasks:read           # Read task information
acp:tasks:write          # Create and modify tasks
acp:tasks:cancel         # Cancel tasks
acp:streams:read         # Access stream information
acp:streams:write        # Create and participate in streams
acp:notifications:receive # Receive webhooks
```

### Transport Security
- **HTTPS Only**: All communications require TLS 1.2+
- **Certificate Validation**: Mandatory in production
- **Webhook Security**: Signature validation supported

## 🌐 Server Endpoints

```yaml
Production:  https://api.acp.example.com/rpc
Staging:     https://staging.acp.example.com/rpc
Development: https://localhost:8443/rpc

Auth Server: https://auth.acp.example.com/oauth2/
```

## 📝 Quick Start Example

### 1. Create a Task
```javascript
// Request
{
  "jsonrpc": "2.0",
  "method": "tasks.create",
  "params": {
    "initialMessage": {
      "role": "user",
      "parts": [
        {
          "type": "TextPart",
          "content": "Please analyze this customer data"
        }
      ]
    },
    "priority": "HIGH"
  },
  "id": "req-1"
}

// Response
{
  "jsonrpc": "2.0",
  "id": "req-1",
  "result": {
    "type": "task",
    "task": {
      "taskId": "task-abc123",
      "status": "SUBMITTED",
      "messages": [...],
      "artifacts": []
    }
  }
}
```

### 2. Start a Stream
```javascript
// Request
{
  "jsonrpc": "2.0",
  "method": "stream.start",
  "params": {
    "participants": ["agent-analyst", "agent-expert"],
    "metadata": {
      "purpose": "collaborative-analysis"
    }
  },
  "id": "req-2"
}

// Response
{
  "jsonrpc": "2.0",
  "id": "req-2",
  "result": {
    "type": "stream",
    "stream": {
      "streamId": "stream-xyz789",
      "status": "ACTIVE",
      "participants": ["agent-analyst", "agent-expert"]
    }
  }
}
```

## 🔄 Communication Patterns

### Async Task Pattern
1. **Create** task with initial requirements
2. **Subscribe** to notifications for progress updates
3. **Monitor** status changes via webhooks
4. **Retrieve** final results and artifacts

### Real-time Stream Pattern
1. **Start** stream with target participants
2. **Exchange** messages in real-time
3. **Collaborate** on problems with instant feedback
4. **End** stream when collaboration complete

## 🎯 Use Cases

### Task Management
- Data analysis and reporting
- Document processing
- Machine learning model training
- Batch data transformations
- Scheduled agent workflows

### Stream Management
- Real-time consultation between specialist agents
- Interactive customer support with agent handoffs
- Collaborative problem-solving sessions
- Live data exploration and analysis
- Emergency response coordination

## 📊 Schema Overview

The ACP protocol defines **20 comprehensive schemas** across 5 categories:

1. **Foundation** (3): JsonRpcRequest, JsonRpcResponse, RpcError
2. **Tasks** (7): TaskObject, TasksCreate/Send/Get/Cancel/Subscribe, TaskNotification
3. **Streams** (5): StreamObject, StreamStart/Message/End/Chunk
4. **Communication** (3): Message, Part, Artifact  
5. **Response** (2): MethodResult, SubscriptionObject

## 🛠️ Implementation Notes

### Client Libraries
The protocol is designed to work with standard JSON-RPC 2.0 client libraries, with ACP-specific method handling and OAuth 2.0 integration.

### Server Implementation
Servers should implement:
- JSON-RPC 2.0 endpoint at `/jsonrpc`
- OAuth 2.0 token validation
- Webhook delivery for notifications
- HTTPS-only transport

### Error Handling
- Standard JSON-RPC codes (-32xxx) for protocol errors
- ACP-specific codes (-40xxx) for business logic errors
- Comprehensive error context in `data` field

## 📖 Documentation

Each component has detailed documentation:

- **[JSON-RPC Foundation](ACP-JSON-RPC-Foundation.md)**: Core protocol mechanics
- **[Task Management](ACP-Task-Management.md)**: Async operation handling
- **[Stream Management](ACP-Stream-Management.md)**: Real-time communication
- **[Shared Communication](ACP-Shared-Communication.md)**: Message formats
- **[Response Management](ACP-Response-Management.md)**: Response handling

## 🏗️ Architecture

```
┌─────────────────┐    HTTPS/OAuth2     ┌─────────────────┐
│   Agent Client  │ ←────────────────── │   Agent Client  │
└─────────────────┘                     └─────────────────┘
         │                                       │
         │ JSON-RPC 2.0                         │
         ▼                                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 ACP Protocol Server                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Task Manager│  │Stream Manager│  │ Notification System │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Getting Started

1. **Review** the [OpenAPI specification](acp-openapi3.yaml)
2. **Understand** the [JSON-RPC foundation](ACP-JSON-RPC-Foundation.md)
3. **Choose** your communication pattern:
   - [Tasks](ACP-Task-Management.md) for async operations
   - [Streams](ACP-Stream-Management.md) for real-time collaboration
4. **Implement** OAuth 2.0 authentication
5. **Set up** webhook endpoints for notifications
6. **Test** with the provided examples

## 📄 License

This specification is provided as-is for implementation of ACP-compatible agent communication systems.

---

**ACP Protocol**: Enabling sophisticated agent-to-agent communication through standardized, secure, and scalable JSON-RPC 2.0 patterns. 🤖✨ 