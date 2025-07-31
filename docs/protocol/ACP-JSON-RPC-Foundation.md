# JSON-RPC Foundation for ACP Communication

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Schema Definitions](#schema-definitions)
  - [JsonRpcRequest](#jsonrpcrequest)
  - [JsonRpcResponse](#jsonrpcresponse)
  - [RpcError](#rpcerror)
- [Communication Patterns](#communication-patterns)
- [Security Requirements](#security-requirements)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Overview

The ACP (Agent Communication Protocol) is built on **JSON-RPC 2.0**, providing a standardized foundation for inter-agent communication. This document details the three core foundation schemas that enable reliable, structured communication between AI agents.

### Why JSON-RPC 2.0?

- **Single Endpoint**: All operations go through `/jsonrpc` - simplifies routing, security, and infrastructure
- **Standardized Envelope**: Consistent request/response structure with built-in error handling
- **Method Dispatch**: Function-like API with structured parameters and results
- **Correlation Support**: Request/response matching via ID field
- **Notification Support**: Fire-and-forget operations when no response needed

---

## Architecture

```
┌─────────────────┐    HTTP POST /jsonrpc    ┌─────────────────┐
│   Agent A       │ ────────────────────────▶ │   Agent B       │
│                 │                           │                 │
│ JSON-RPC Client │ ◀──────────────────────── │ JSON-RPC Server │
└─────────────────┘    JSON-RPC Response     └─────────────────┘
```

### Transport Layer
- **Protocol**: HTTPS only (required for security)
- **Method**: POST only
- **Endpoint**: `/jsonrpc`
- **Content-Type**: `application/json`
- **Authentication**: OAuth 2.0 Bearer token required
- **Security**: TLS 1.2+ encryption mandatory

### Message Layer
- **Envelope**: JSON-RPC 2.0 structure
- **Payload**: ACP-specific schemas in `params`/`result`
- **Correlation**: Optional ID for request/response matching

---

## Schema Definitions

### JsonRpcRequest

The **request envelope** that wraps all client-to-server communications.

#### Schema Structure
```yaml
JsonRpcRequest:
  type: object
  required: [jsonrpc, method]
  additionalProperties: false
  properties:
    jsonrpc:
      type: string
      enum: ["2.0"]
    method:
      oneOf: [10 ACP method types]
    params:
      oneOf: [10 parameter schemas]
    id:
      oneOf: [string, integer, null]
```

#### Field Details

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `jsonrpc` | ✅ | `"2.0"` | Protocol version identifier |
| `method` | ✅ | `string` | ACP operation to perform |
| `params` | ❌ | `object` | Method-specific parameters |
| `id` | ❌ | `string\|number\|null` | Request correlation ID |

#### Supported Methods

**Task Methods (Async Operations):**
- `tasks.create` - Create new task
- `tasks.send` - Send message to task
- `tasks.get` - Retrieve task status
- `tasks.cancel` - Cancel task execution
- `tasks.subscribe` - Subscribe to task notifications

**Stream Methods (Real-time Operations):**
- `stream.start` - Start streaming conversation
- `stream.message` - Send stream message
- `stream.end` - End streaming session

**Notification Methods (Server-initiated):**
- `task.notification` - Task status updates
- `stream.chunk` - Real-time stream chunks

#### Request Types

**1. Regular Request (with ID)**
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.create",
  "params": {...},
  "id": "req-123"
}
```
→ Expects response with same ID

**2. Notification (without ID)**
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.cancel",
  "params": {...}
}
```
→ No response expected (fire-and-forget)

---

### JsonRpcResponse

The **response envelope** that wraps all server-to-client communications.

#### Schema Structure
```yaml
JsonRpcResponse:
  type: object
  required: [jsonrpc, id]
  additionalProperties: false
  properties:
    jsonrpc:
      type: string
      enum: ["2.0"]
    id:
      oneOf: [string, integer, null]
    result:
      $ref: '#/components/schemas/MethodResult'
    error:
      $ref: '#/components/schemas/RpcError'
  oneOf:
    - required: [result]
    - required: [error]
```

#### Field Details

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `jsonrpc` | ✅ | `"2.0"` | Protocol version identifier |
| `id` | ✅ | `string\|number\|null` | Must match request ID |
| `result` | ⚖️ | `object` | Success result (XOR with error) |
| `error` | ⚖️ | `object` | Error details (XOR with result) |

#### Mutual Exclusion Logic
```yaml
oneOf:
  - required: [result]     # Success: has result, no error
    not: {required: [error]}
  - required: [error]      # Failure: has error, no result
    not: {required: [result]}
```

**Key Point**: Every response MUST have either `result` OR `error`, never both or neither.

#### Response Types

**1. Success Response**
```json
{
  "jsonrpc": "2.0",
  "id": "req-123",
  "result": {
    "type": "task",
    "task": {...}
  }
}
```

**2. Error Response**
```json
{
  "jsonrpc": "2.0",
  "id": "req-123", 
  "error": {
    "code": -40001,
    "message": "Task not found",
    "data": {...}
  }
}
```

---

### RpcError

The **error structure** used when operations fail, combining standard JSON-RPC codes with ACP-specific codes.

#### Schema Structure
```yaml
RpcError:
  type: object
  required: [code, message]
  additionalProperties: false
  properties:
    code:
      type: integer
    message:
      type: string
    data:
      nullable: true
      description: Additional error context
```

#### Error Code Categories

**Standard JSON-RPC 2.0 Codes (Protocol Errors):**
| Code | Name | Description |
|------|------|-------------|
| `-32700` | Parse Error | Invalid JSON received |
| `-32600` | Invalid Request | Request doesn't follow JSON-RPC format |
| `-32601` | Method Not Found | Method doesn't exist |
| `-32602` | Invalid Params | Invalid method parameters |
| `-32603` | Internal Error | Server-side internal error |

**ACP-Specific Codes (Business Logic Errors):**
| Code | Name | Description |
|------|------|-------------|
| `-40001` | Task Not Found | TaskId doesn't exist |
| `-40002` | Task Already Completed | Can't modify finished task |
| `-40003` | Stream Not Found | StreamId doesn't exist |
| `-40004` | Stream Already Closed | Can't use closed stream |
| `-40005` | Agent Not Available | Target agent unreachable |
| `-40006` | Permission Denied | Access/authorization failure |
| `-40007` | Authentication Failed | Invalid/missing OAuth2 token |
| `-40008` | Insufficient OAuth2 Scope | Token lacks required scopes |
| `-40009` | OAuth2 Token Expired | Access token has expired |

#### Error Structure Examples

**Protocol Error:**
```json
{
  "code": -32602,
  "message": "Invalid params",
  "data": {
    "expected": "taskId (string)",
    "received": "taskId (number)",
    "field": "params.taskId"
  }
}
```

**Business Logic Error:**
```json
{
  "code": -40001,
  "message": "Task not found",
  "data": {
    "taskId": "invalid-task-123",
    "suggestion": "Check if task was cancelled or completed"
  }
}
```

---

## Communication Patterns

### 1. Request-Response Pattern

**Used for**: Operations requiring confirmation/results

```
Client                     Server
  │                          │
  ├── POST /jsonrpc ─────────▶│
  │   (with id)               │
  │                          │
  │◀─────── Response ─────────┤
  │   (same id)               │
```

**Example Flow:**
```json
// Request
{
  "jsonrpc": "2.0",
  "method": "tasks.get",
  "params": {"taskId": "abc123"},
  "id": "req-456"
}

// Response  
{
  "jsonrpc": "2.0",
  "id": "req-456",
  "result": {
    "type": "task",
    "task": {
      "taskId": "abc123",
      "status": "COMPLETED",
      "messages": [...],
      "artifacts": [...]
    }
  }
}
```

### 2. Notification Pattern

**Used for**: Fire-and-forget operations, status updates

```
Client                     Server
  │                          │
  ├── POST /jsonrpc ─────────▶│
  │   (no id)                 │
  │                          │
  │     [no response]         │
```

**Example Flow:**
```json
// Notification (no response expected)
{
  "jsonrpc": "2.0",
  "method": "tasks.cancel",
  "params": {"taskId": "abc123"}
}
```

### 3. Correlation Pattern

**Used for**: Matching responses to requests in async environments

```json
// Multiple concurrent requests
{"jsonrpc": "2.0", "method": "tasks.get", "id": "req-1", ...}
{"jsonrpc": "2.0", "method": "stream.start", "id": "req-2", ...}
{"jsonrpc": "2.0", "method": "tasks.create", "id": "req-3", ...}

// Responses can arrive in any order
{"jsonrpc": "2.0", "id": "req-3", "result": {...}}  // task.create result
{"jsonrpc": "2.0", "id": "req-1", "result": {...}}  // tasks.get result  
{"jsonrpc": "2.0", "id": "req-2", "result": {...}}  // stream.start result
```

---

## Security Requirements

### Mandatory HTTPS Transport

**All ACP communications MUST use HTTPS** for the following security reasons:

#### 🔒 **Encryption Requirements**
- **TLS Version**: Minimum TLS 1.2, recommended TLS 1.3
- **Cipher Suites**: Strong encryption algorithms only
- **Certificate Validation**: Valid certificates required (no self-signed in production)

#### 🛡️ **Security Benefits**
- **Message Confidentiality**: Agent communications encrypted in transit
- **Data Integrity**: Protection against message tampering
- **Authentication**: Server identity verification
- **Man-in-the-Middle Protection**: Prevents intercepted communications

#### ⚠️ **HTTP is Prohibited**
```
❌ NEVER USE: http://api.example.com/rpc
✅ ALWAYS USE: https://api.example.com/rpc
```

#### 🏗️ **Implementation Notes**

**For Production Deployments:**
```yaml
servers:
  - url: https://api.example.com/rpc
    description: Production server with valid TLS certificate
```

**For Development:**
```yaml
servers:
  - url: https://localhost:8443/rpc
    description: Local development with self-signed certificate
```

**Client Configuration Example:**
```javascript
// Good: HTTPS with proper certificate validation
const client = new ACPClient({
  endpoint: 'https://api.example.com/rpc',
  validateCertificates: true,
  minTlsVersion: '1.2'
});

// Bad: Insecure HTTP (will be rejected)
const badClient = new ACPClient({
  endpoint: 'http://api.example.com/rpc'  // ❌ Not allowed
});
```

---

## OAuth 2.0 Authentication

### Mandatory OAuth 2.0 for All Requests

**All ACP API calls MUST include a valid OAuth 2.0 access token** in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Supported OAuth 2.0 Flows

#### 🤖 **Client Credentials Flow** (Recommended for ACP)

**Use Case**: Machine-to-machine communication between agents

**Flow Steps:**
```
1. Agent → POST /oauth2/token
     {
    "grant_type": "client_credentials",
    "client_id": "agent-analysis-001", 
    "client_secret": "secret123",
    "scope": "acp:tasks:write acp:streams:read"
  }

2. Auth Server → Response
     {
    "access_token": "eyJhbGc...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": "acp:tasks:write acp:streams:read"
  }

3. Agent → ACP API Call
   Authorization: Bearer eyJhbGc...
```

**Configuration Example:**
```javascript
// Client credentials authentication for agents
const oauth2Config = {
  tokenUrl: 'https://auth.example.com/oauth2/token',
  clientId: 'agent-analysis-001',
  clientSecret: process.env.AGENT_CLIENT_SECRET,
  scopes: ['acp:tasks:write', 'acp:streams:read', 'acp:agent:identify']
};

const token = await getClientCredentialsToken(oauth2Config);
```

#### 👤 **Authorization Code Flow** (User-Delegated Access)

**Use Case**: Agents acting on behalf of users

**Flow Steps:**
```
1. User → Authorization URL
   https://auth.example.com/oauth2/authorize?
     response_type=code&
     client_id=agent-assistant&
     scope=acp:tasks:write&
     redirect_uri=https://app.example.com/callback

2. User → Grants Permission → Agent receives authorization code

3. Agent → Exchange code for token
   POST /oauth2/token
   {
     "grant_type": "authorization_code",
     "code": "auth_code_123",
     "client_id": "agent-assistant", 
     "client_secret": "secret456",
     "redirect_uri": "https://app.example.com/callback"
   }
```

### Required Scopes

| Scope | Description | Methods |
|-------|-------------|---------|
| `acp:agent:identify` | **Required for all agents** - Basic identification | All methods |
| `acp:tasks:read` | Read task information and status | `tasks.get` |
| `acp:tasks:write` | Create tasks and send messages | `tasks.create`, `tasks.send` |
| `acp:tasks:cancel` | Cancel task execution | `tasks.cancel` |
| `acp:streams:read` | Access stream information | Stream viewing |
| `acp:streams:write` | Create and participate in streams | `stream.start`, `stream.message`, `stream.end` |
| `acp:notifications:receive` | Receive task and stream notifications | `tasks.subscribe`, `task.notification`, `stream.chunk` |

### Authentication Examples

#### Successful Request with OAuth2
```http
POST /jsonrpc HTTP/1.1
Host: api.example.com
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...

{
  "jsonrpc": "2.0",
  "method": "tasks.create",
  "params": {
    "initialMessage": {
      "role": "user",
      "parts": [{"type": "TextPart", "content": "Analyze sales data"}]
    }
  },
  "id": "req-123"
}
```

#### Authentication Error Response
```json
{
  "jsonrpc": "2.0",
  "id": "req-123",
  "error": {
    "code": -40007,
    "message": "Authentication failed",
    "data": {
      "error": "invalid_token",
      "error_description": "The access token is expired",
      "requiredScopes": ["acp:agent:identify", "acp:tasks:write"],
      "tokenUrl": "https://auth.example.com/oauth2/token"
    }
  }
}
```

#### Insufficient Scope Error
```json
{
  "jsonrpc": "2.0", 
  "id": "req-456",
  "error": {
    "code": -40008,
    "message": "Insufficient OAuth2 scope",
    "data": {
      "requiredScopes": ["acp:tasks:cancel"],
      "providedScopes": ["acp:tasks:read", "acp:tasks:write"],
      "suggestion": "Request additional scopes from authorization server"
    }
  }
}
```

### Token Management Best Practices

#### 🔄 **Token Refresh Strategy**
```javascript
class ACPClient {
  constructor(config) {
    this.tokenCache = new Map();
    this.refreshThreshold = 300; // Refresh 5 minutes before expiry
  }

  async getValidToken(scopes) {
    const cacheKey = scopes.sort().join(':');
    const cached = this.tokenCache.get(cacheKey);
    
    // Check if token needs refresh
    if (!cached || (cached.expiresAt - Date.now()) < this.refreshThreshold * 1000) {
      const newToken = await this.refreshToken(scopes);
      this.tokenCache.set(cacheKey, {
        token: newToken.access_token,
        expiresAt: Date.now() + (newToken.expires_in * 1000)
      });
      return newToken.access_token;
    }
    
    return cached.token;
  }
}
```

#### 🔒 **Secure Token Storage**
```javascript
// Good: Secure token handling
const tokenStorage = {
  store: (token) => {
    // Use secure storage (e.g., encrypted database, secure vault)
    secureVault.store('agent_token', encrypt(token));
  },
  retrieve: () => {
    // Retrieve and decrypt token
    const encrypted = secureVault.get('agent_token');
    return decrypt(encrypted);
  }
};

// Bad: Insecure token storage
localStorage.setItem('token', token); // ❌ Never store tokens in localStorage
console.log('Token:', token);        // ❌ Never log tokens
```

#### ⚡ **Scope Optimization**
```javascript
// Good: Request minimal scopes needed
const scopes = {
  readOnly: ['acp:agent:identify', 'acp:tasks:read'],
taskWorker: ['acp:agent:identify', 'acp:tasks:read', 'acp:tasks:write'],
fullAccess: ['acp:agent:identify', 'acp:tasks:write', 'acp:streams:write', 'acp:notifications:receive']
};

// Bad: Always requesting all scopes
const allScopes = ['acp:*']; // ❌ Over-privileged access
```

### Additional Security Considerations

#### 🔑 **Authentication & Authorization**
Beyond OAuth2, ACP implementations should also consider:
- Client certificate authentication for high-security environments
- API rate limiting per agent/token
- Token introspection for real-time validation
- Audit logging of all authenticated requests

#### 📝 **Audit & Logging**
- Log all agent communications (without sensitive data)
- Monitor for suspicious patterns
- Implement request tracing for debugging
- Maintain security event logs

#### 🚨 **Error Information Disclosure**
```json
// Good: Don't expose internal details in errors
{
  "code": -40006,
  "message": "Permission denied",
  "data": {
    "suggestion": "Contact system administrator"
  }
}

// Bad: Exposes internal system information
{
  "code": -40006, 
  "message": "Permission denied",
  "data": {
    "internalError": "Database connection failed on server db-prod-3",
    "stackTrace": "..."  // ❌ Security risk
  }
}
```

---

## Error Handling

### Error Categories and Handling Strategies

#### 1. Transport Errors (HTTP Level)
```
HTTP 404, 500, timeout, etc.
→ Handle at HTTP client level
→ Retry logic, circuit breakers
```

#### 2. Protocol Errors (JSON-RPC Level)
```
-32xxx codes
→ Client implementation bugs
→ Fix request format, validate before sending
```

#### 3. Business Logic Errors (ACP Level)
```
-40xxx codes  
→ Application-level issues
→ Handle gracefully, provide user feedback
```

### Error Handling Best Practices

```javascript
// Client-side error handling example
try {
  const response = await fetch('/jsonrpc', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'tasks.get',
      params: {taskId: 'abc123'},
      id: 'req-' + Date.now()
    })
  });
  
  const result = await response.json();
  
  if (result.error) {
    // Handle JSON-RPC errors
    switch (result.error.code) {
      case -40001: // Task not found
        showMessage('Task not found. It may have been deleted.');
        break;
      case -40005: // Agent not available  
        showMessage('Agent is offline. Try again later.');
        break;
      default:
        showMessage(`Error: ${result.error.message}`);
    }
  } else {
    // Handle success
    processResult(result.result);
  }
} catch (error) {
  // Handle transport errors
  showMessage('Network error. Please check your connection.');
}
```

---

## Best Practices

### 1. ID Generation
```javascript
// Good: Unique, traceable IDs
const id = `req-${agentId}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

// Avoid: Sequential numbers in distributed systems
const id = requestCounter++; // Can cause collisions
```

### 2. Error Data Structure
```json
// Good: Structured error data with actionable information
{
  "code": -40001,
  "message": "Task not found",
  "data": {
    "taskId": "invalid-id",
    "suggestion": "Check if task was cancelled",
    "retryAfter": 300,
    "supportedTaskIds": ["task-1", "task-2"]
  }
}

// Avoid: Vague error messages
{
  "code": -40001,
  "message": "Error occurred"
}
```

### 3. Method Naming Convention
```
Pattern: {resource}.{action}

✅ Good:
- tasks.create
- tasks.get  
- stream.start
- stream.message

❌ Avoid:
- createTask
- get_task
- StartStream
```

### 4. OAuth2 + HTTPS Configuration
```javascript
// Good: Complete ACP client configuration with OAuth2 and HTTPS
const acpClient = {
  endpoint: 'https://api.example.com/rpc',
  timeout: 30000,
  
  // OAuth2 configuration
  oauth2: {
    tokenUrl: 'https://auth.example.com/oauth2/token',
    clientId: 'agent-analysis-001',
    clientSecret: process.env.AGENT_CLIENT_SECRET,
    scopes: ['acp:agent:identify', 'acp:tasks:write', 'acp:streams:read'],
    cacheTokens: true,
    refreshThreshold: 300 // seconds
  },
  
  // HTTPS/TLS configuration
  tls: {
    minVersion: 'TLSv1.2',
    maxVersion: 'TLSv1.3', 
    rejectUnauthorized: true  // Validate certificates
  },
  
  // Standard headers
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'ACP-Agent/1.0'
  }
};

// Usage example
const client = new ACPClient(acpClient);
await client.authenticate(); // Gets OAuth2 token
const result = await client.call('tasks.create', {...}); // Automatically includes auth
```

### 5. Timeout Handling
```javascript
// Set appropriate timeouts for different operations
const timeouts = {
  'tasks.get': 5000,      // Quick status check
  'tasks.create': 30000,  // May involve setup
  'stream.start': 15000   // Connection establishment
};
```

### 6. Batch Operations
```json
// JSON-RPC 2.0 supports batch requests
[
  {"jsonrpc": "2.0", "method": "tasks.get", "params": {"taskId": "1"}, "id": "1"},
  {"jsonrpc": "2.0", "method": "tasks.get", "params": {"taskId": "2"}, "id": "2"},
  {"jsonrpc": "2.0", "method": "tasks.get", "params": {"taskId": "3"}, "id": "3"}
]

// Response will be array of results in any order
[
  {"jsonrpc": "2.0", "id": "2", "result": {...}},
  {"jsonrpc": "2.0", "id": "1", "result": {...}},
  {"jsonrpc": "2.0", "id": "3", "error": {...}}
]
```

---

## Examples

### Complete Request-Response Cycle

#### 1. Task Creation
```http
POST /jsonrpc HTTP/1.1
Host: api.example.com
Content-Type: application/json
Connection: keep-alive

{
  "jsonrpc": "2.0",
  "method": "tasks.create",
  "params": {
    "initialMessage": {
      "role": "user",
      "parts": [
        {
          "type": "TextPart",
          "content": "Please analyze the quarterly sales data and identify trends."
        }
      ]
    },
    "priority": "HIGH",
    "assignTo": "data-analysis-agent"
  },
  "id": "req-create-analysis-1642538400"
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "req-create-analysis-1642538400",
  "result": {
    "type": "task",
    "task": {
      "taskId": "task-analysis-abc123",
      "status": "SUBMITTED",
      "createdAt": "2024-01-15T10:30:00Z",
      "assignedAgent": "data-analysis-agent",
      "messages": [
        {
          "role": "user",
          "parts": [
            {
              "type": "TextPart", 
              "content": "Please analyze the quarterly sales data and identify trends."
            }
          ],
          "timestamp": "2024-01-15T10:30:00Z"
        }
      ],
      "artifacts": []
    }
  }
}
```

#### 2. Error Response Example
```http
POST /jsonrpc HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "tasks.get",
  "params": {
    "taskId": "nonexistent-task"
  },
  "id": "req-get-404"
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "req-get-404",
  "error": {
    "code": -40001,
    "message": "Task not found",
    "data": {
      "taskId": "nonexistent-task",
      "suggestion": "Check if the taskId is correct or if the task has been deleted",
      "availableTasks": ["task-abc123", "task-def456"],
      "timestamp": "2024-01-15T10:35:00Z"
    }
  }
}
```

#### 3. Notification Example (No Response)
```http
POST /jsonrpc HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "task.notification",
  "params": {
    "taskId": "task-abc123",
    "event": "STATUS_CHANGE",
    "timestamp": "2024-01-15T10:45:00Z",
    "data": {
      "taskId": "task-abc123",
      "status": "COMPLETED",
      "artifacts": [
        {
          "artifactId": "analysis-report-1",
          "name": "Q4 Sales Analysis Report",
          "description": "Comprehensive analysis of Q4 sales trends"
        }
      ]
    }
  }
}
```
*No HTTP response body - this is a notification*

---

## Conclusion

The JSON-RPC 2.0 foundation provides a robust, standardized base for ACP communication. These three schemas (`JsonRpcRequest`, `JsonRpcResponse`, `RpcError`) enable:

- **Reliable Transport**: Single endpoint with consistent structure
- **Error Handling**: Standardized error codes and detailed error context  
- **Correlation**: Request/response matching for async operations
- **Flexibility**: Support for both request-response and fire-and-forget patterns
- **Extensibility**: Framework for adding new ACP methods and parameters

This foundation supports the higher-level ACP schemas for task management, streaming communication, and rich media exchange while maintaining compatibility with standard JSON-RPC 2.0 tooling and libraries. 