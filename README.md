# Agent Communication Protocol (ACP) - Enterprise Agent Communication Protocol

[![PyPI version](https://badge.fury.io/py/acp-sdk-python.svg)](https://badge.fury.io/py/acp-sdk-python)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Downloads](https://pepy.tech/badge/acp-sdk-python)](https://pepy.tech/project/acp-sdk-python)
[![GitHub stars](https://img.shields.io/github/stars/venus-enterprise/acp-sdk-python.svg?style=social&label=Star)](https://github.com/venus-enterprise/acp-sdk-python)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🏢 **Enterprise-First Design**

> **Purpose-built for enterprise environments where security, governance, and scale matter most.**

**ACP (Agent Communication Protocol)** is the industry-standard protocol for **enterprise-grade** agent-to-agent communication. This Python implementation is specifically designed for large organizations deploying multiple AI agents across departments with centralized management and security controls.

### **Perfect For Enterprise Use Cases:**
- **🏛️ Multi-department AI deployments** (Sales, Legal, HR, Finance agents)
- **🔐 API Gateway integration** (Apigee, Kong, AWS API Gateway)
- **📊 Centralized agent discovery** and capability management
- **🛡️ Enterprise security** with OAuth 2.0, mTLS, and audit trails
- **📈 Production scale** with high-throughput, low-latency communication
- **🎯 Supervisor/Router patterns** with specialist agent orchestration

### **Architecture Highlights:**
```
Router Agent (Supervisor) → API Gateway → Specialist Agents (Servers)
     ↓                           ↓              ↓
Orchestrates workflows    Apigee OAuth2    Department-specific
Multi-agent coordination  Rate limiting    Domain expertise
Central task routing      Security policies Scalable processing
```

**ACP (Agent Communication Protocol)** is the industry-standard protocol for secure, scalable agent-to-agent communication. Built on JSON-RPC 2.0, ACP enables AI agents to discover, authenticate, and collaborate across any platform.

## 🚀 **Why ACP for Enterprise?**

- 🏛️ **Enterprise Standard**: Purpose-built for large-scale organizational deployments
- 🔒 **Production Security**: OAuth2, mTLS, API gateway integration, audit trails
- 🌐 **Multi-Cloud Ready**: Deploy across AWS, Azure, GCP with consistent protocols
- 📊 **Centralized Governance**: Agent discovery, capability management, SLA monitoring
- ⚡ **Enterprise Scale**: High-throughput, low-latency, multi-tenant architecture
- 🎯 **Proven Patterns**: Router/supervisor architecture with specialist agent coordination

> **🏢 [See Enterprise Deployment Guide](docs/ENTERPRISE.md)** for Apigee integration, security patterns, and production deployment.

## 📦 **Quick Start**

### Installation

```bash
pip install acp-sdk-python
```

### Basic Client Usage

```python
import acp
from acp.models import TasksCreateParams, Message, Part

# Connect to an agent
client = acp.Client("https://agent.example.com/jsonrpc")

# Send a task
response = await client.tasks.create(TasksCreateParams(
    initialMessage=Message(
        role="user",
        parts=[Part(type="TextPart", content="Search for recent tickets")]
    ),
    priority="HIGH"
))

print(f"Task created: {response.taskId}")
```

### Basic Server Usage

```python
import acp

# Create ACP server
server = acp.Server(
    title="My Agent",
    description="An intelligent assistant agent"
)

@server.method_handler("tasks.create")
async def handle_task(params, context):
    """Handle incoming task requests"""
    # Your agent logic here
    return {
        "type": "task",
        "task": {
            "taskId": "task-123",
            "status": "SUBMITTED",
            "createdAt": "2024-01-01T00:00:00Z"
        }
    }

# Run the server
server.run(host="0.0.0.0", port=8000)
```

## 🏗️ **Architecture**

ACP provides a complete stack for agent communication:

```
┌─────────────────────────────────────────────────────┐
│                    Your Application                 │
├─────────────────────────────────────────────────────┤
│  📱 ACP Client           🖥️  ACP Server            │
│  • Task Management      • Request Handling          │
│  • Streaming            • Authentication            │
│  • Discovery            • Validation                │
├─────────────────────────────────────────────────────┤
│             🌐 ACP Protocol Layer                   │
│  • JSON-RPC 2.0         • OAuth2 Security          │
│  • Agent Discovery      • Real-time Streaming       │
│  • Error Handling       • Webhook Notifications     │
├─────────────────────────────────────────────────────┤
│                🔧 Transport Layer                   │
│  • HTTPS/TLS            • WebSockets               │
│  • Load Balancing       • Rate Limiting            │
└─────────────────────────────────────────────────────┘
```

## 🔧 **Core Features**

### **1. Task Management**
- **Asynchronous Processing**: Submit tasks and receive results when ready
- **Priority Handling**: HIGH, MEDIUM, LOW priority levels
- **Progress Tracking**: Real-time status updates and notifications
- **Artifact Exchange**: Secure file and data transfer

### **2. Real-time Streaming**
- **Bidirectional Communication**: Interactive conversations between agents
- **Message Chunking**: Efficient handling of large data streams
- **Connection Management**: Automatic reconnection and error recovery

### **3. Agent Discovery**
- **Agent Cards**: Standardized capability discovery via `/.well-known/agent.json`
- **Skill Registry**: Declare and discover agent capabilities
- **Version Management**: Semantic versioning for protocol compatibility

### **4. Enterprise Security**
- **OAuth2 Authentication**: Industry-standard authentication flows
- **Scope-based Authorization**: Fine-grained permission control
- **HTTPS Everywhere**: Encrypted transport for all communications
- **Token Management**: Automatic token refresh and validation

## 🛠️ **CLI Tools**

ACP includes professional command-line tools:

```bash
# Protocol information
acp schema info              # Show protocol specification
acp schema methods           # List available methods

# Agent discovery
acp agent-card validate      # Validate agent card files
acp agent-card examples      # Show example configurations

# Development tools
acp server start             # Start development server
acp validate request.json    # Validate ACP requests
```

## 📚 **Documentation**

- 📖 **[Protocol Specification](https://acp-protocol.org/spec)** - Complete ACP protocol documentation
- 🚀 **[Quick Start Guide](https://docs.acp-protocol.org/quickstart)** - Get up and running in 5 minutes
- 📘 **[API Reference](https://docs.acp-protocol.org/api)** - Complete Python API documentation
- 💡 **[Examples](./examples/)** - Working examples and templates
- 🔧 **[Development Guide](https://docs.acp-protocol.org/development)** - Build your own ACP agents

## 🌟 **Examples**

| Example | Description | Link |
|---------|-------------|------|
| **Basic Client** | Simple task submission | [View](./examples/client/basic_client.py) |
| **Basic Server** | Handle incoming requests | [View](./examples/server/basic_server.py) |
| **Confluence Agent** | Enterprise search agent | [View](./examples/agent-cards/confluence-agent-card.json) |
| **Streaming Chat** | Real-time conversations | [View](./examples/streaming/) |

## 🏢 **Enterprise Features**

ACP is designed for production enterprise environments:

- **🎯 High Availability**: Load balancing and failover support
- **📊 Observability**: Structured logging and metrics collection
- **🔄 Scalability**: Horizontal scaling with connection pooling
- **🛡️ Security**: Enterprise-grade authentication and authorization
- **📈 Performance**: Optimized for high-throughput workloads

## 🤝 **Contributing**

ACP is an open protocol welcoming contributions:

1. **Protocol**: Propose enhancements to the core specification
2. **Implementation**: Improve the Python reference implementation
3. **Documentation**: Help make ACP more accessible
4. **Testing**: Add test cases and improve reliability

See our [Contributing Guide](https://github.com/acp-protocol/acp-python/blob/main/CONTRIBUTING.md) for details.

## 📄 **License**

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🔗 **Links**

- **🌐 Protocol Website**: [acp-protocol.org](https://acp-protocol.org)
- **📚 Documentation**: [docs.acp-protocol.org](https://docs.acp-protocol.org)
- **🐙 GitHub**: [github.com/acp-protocol](https://github.com/acp-protocol)
- **💬 Discussions**: [GitHub Discussions](https://github.com/acp-protocol/acp-python/discussions)
- **🐛 Issues**: [GitHub Issues](https://github.com/acp-protocol/acp-python/issues)

---

<div align="center">

**Agent Communication Protocol (ACP)**  
*The Standard for Agent-to-Agent Communication*

Made with ❤️ by the ACP community

</div>
