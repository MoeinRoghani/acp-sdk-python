# Stream Management Schemas for ACP Protocol

## Table of Contents
- [Overview](#overview)
- [Stream Lifecycle](#stream-lifecycle)
- [Schema Definitions](#schema-definitions)
  - [StreamObject Schema](#streamobject-schema)
  - [StreamStartParams Schema](#streamstartparams-schema)
  - [StreamMessageParams Schema](#streammessageparams-schema)
  - [StreamEndParams Schema](#streamendparams-schema)
  - [StreamChunkParams Schema](#streamchunkparams-schema)
- [Real-time Communication Patterns](#real-time-communication-patterns)
- [Multi-Agent Collaboration](#multi-agent-collaboration)
- [Chunk-Based Messaging](#chunk-based-messaging)
- [Best Practices](#best-practices)
- [Performance Considerations](#performance-considerations)
- [Security and Authentication](#security-and-authentication)
- [Examples](#examples)
- [Integration Patterns](#integration-patterns)

---

## Overview

The **Stream Management** system in ACP enables real-time, interactive communication between agents. Unlike the asynchronous Task Management system, streams provide immediate, bidirectional communication for collaborative problem-solving, interactive assistance, and real-time data processing.

### Core Concepts

- **Real-time Communication**: Immediate message exchange with minimal latency
- **Multi-participant Streams**: Support for multiple agents collaborating simultaneously
- **Chunk-based Delivery**: Progressive message delivery for large content
- **Interactive Sessions**: Live collaboration with immediate feedback
- **Ephemeral Nature**: Short-lived sessions focused on immediate interaction
- **Bidirectional Flow**: All participants can send and receive messages

### Stream vs Task Communication

| Aspect | Streams (Real-time) | Tasks (Async) |
|--------|-------------------|---------------|
| **Latency** | < 1 second | Minutes to hours |
| **Interaction** | Bidirectional, live | Request-response cycles |
| **Persistence** | Temporary session | Full lifecycle tracking |
| **Participants** | Multiple agents | Single assigned agent |
| **Use Cases** | Collaboration, consultation | Analysis, processing |
| **Data Flow** | Continuous exchange | Batch delivery |
| **Lifecycle** | ACTIVE → CLOSED | SUBMITTED → COMPLETED |

### Key Use Cases

#### 🤝 Collaborative Problem Solving
- Multiple agents working together on complex problems
- Real-time consultation between specialized agents
- Interactive debugging and troubleshooting sessions

#### 💬 Interactive Assistance  
- Live customer support with agent handoffs
- Real-time guidance and step-by-step assistance
- Interactive tutorials and training sessions

#### 📊 Live Data Processing
- Real-time data analysis with immediate feedback
- Interactive data exploration and visualization
- Collaborative report building with live updates

#### 🔄 Agent Coordination
- Resource allocation and task distribution
- Real-time status updates and coordination
- Emergency response and escalation handling

---

## Stream Lifecycle

### State Diagram

```
    ┌─────────────┐
    │   ACTIVE    │ ← Stream is open, participants can exchange messages
    └─────┬───────┘
          │
          ├─────────────────┬─────────────────┐
          ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │   PAUSED    │   │   CLOSED    │   │  [TIMEOUT]  │
    └─────┬───────┘   └─────────────┘   └─────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                           │
                    [Terminal State]
```

### State Definitions

#### 🟢 ACTIVE
- **Description**: Stream is open and operational
- **Participants**: Can send and receive messages
- **Duration**: Seconds to hours depending on use case
- **Operations**: `stream.message`, `stream.chunk` allowed
- **Next States**: `PAUSED`, `CLOSED`

#### 🟡 PAUSED
- **Description**: Stream temporarily suspended
- **Participants**: Cannot send new messages
- **Usage**: Technical issues, participant availability
- **Operations**: `stream.start` to resume, `stream.end` to close
- **Next States**: `ACTIVE`, `CLOSED`

#### 🔴 CLOSED
- **Description**: Stream permanently ended
- **Duration**: Terminal state
- **Cleanup**: Resources freed, message history archived
- **Operations**: No further operations allowed

### Lifecycle Events

- **STREAM_STARTED** - New stream created and activated
- **PARTICIPANT_JOINED** - Agent added to existing stream
- **PARTICIPANT_LEFT** - Agent removed from stream
- **MESSAGE_SENT** - New message in stream
- **CHUNK_RECEIVED** - Progressive message chunk delivered
- **STREAM_PAUSED** - Stream temporarily suspended
- **STREAM_RESUMED** - Stream reactivated after pause
- **STREAM_ENDED** - Stream permanently closed

---

## Schema Definitions

### StreamObject Schema

The **StreamObject** represents an active communication session between multiple agents, enabling real-time collaborative interaction.

#### Schema Structure
```yaml
StreamObject:
  type: object
  required: [streamId, status, participants]
  properties:
    streamId:
      type: string
      description: Unique identifier for the stream
    status:
      type: string
      enum: [ACTIVE, PAUSED, CLOSED]
    participants:
      type: array
      items:
        type: string
      description: Agent IDs participating in stream
    createdAt:
      type: string
      format: date-time
    closedAt:
      type: string
      format: date-time
    metadata:
      type: object
      additionalProperties: true
```

#### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `streamId` | ✅ | `string` | Unique stream identifier |
| `status` | ✅ | `enum` | Current stream state |
| `participants` | ✅ | `string[]` | Agent IDs in the stream |
| `createdAt` | ❌ | `datetime` | Stream creation timestamp |
| `closedAt` | ❌ | `datetime` | Stream closure timestamp |
| `metadata` | ❌ | `object` | Custom stream properties |

#### StreamObject Examples

**Two-Agent Collaboration:**
```json
{
  "streamId": "stream-collab-20240115-abc123",
  "status": "ACTIVE",
  "participants": [
    "agent-data-analyst-001",
    "agent-domain-expert-finance"
  ],
  "createdAt": "2024-01-15T14:30:00Z",
  "metadata": {
    "purpose": "financial_data_analysis",
    "initiatedBy": "agent-data-analyst-001",
    "priority": "HIGH",
    "expectedDuration": "30_minutes",
    "topic": "quarterly_revenue_discrepancy"
  }
}
```

**Multi-Agent Consultation:**
```json
{
  "streamId": "stream-emergency-response-xyz789",
  "status": "ACTIVE", 
  "participants": [
    "agent-incident-coordinator",
    "agent-security-specialist",
    "agent-compliance-officer",
    "agent-communications-lead"
  ],
  "createdAt": "2024-01-15T16:45:00Z",
  "metadata": {
    "purpose": "incident_response",
    "severity": "HIGH",
    "incidentId": "INC-2024-001",
    "escalationLevel": 2,
    "maxParticipants": 6
  }
}
```

**Customer Support Stream:**
```json
{
  "streamId": "stream-support-customer-789",
  "status": "ACTIVE",
  "participants": [
    "agent-support-tier1",
    "agent-support-tier2",
    "user-customer-12345"
  ],
  "createdAt": "2024-01-15T10:15:00Z",
  "metadata": {
    "purpose": "customer_support",
    "ticketId": "SUPP-2024-5678",
    "customerTier": "premium",
    "issueCategory": "technical",
    "handoffReason": "escalation_required"
  }
}
```

---

### StreamStartParams Schema

Parameters for the `stream.start` method to initiate real-time communication sessions.

#### Schema Structure
```yaml
StreamStartParams:
  type: object
  properties:
    participants:
      type: array
      items:
        type: string
      description: Agent IDs to include in stream
    metadata:
      type: object
      additionalProperties: true
```

#### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `participants` | ❌ | `string[]` | Initial participant agent IDs |
| `metadata` | ❌ | `object` | Stream configuration and context |

#### Usage Patterns

**Direct Agent Collaboration:**
```json
{
  "method": "stream.start",
  "params": {
    "participants": ["agent-analyst", "agent-expert"],
    "metadata": {
      "purpose": "data_validation",
      "topic": "customer_segmentation_model",
      "urgency": "NORMAL"
    }
  },
  "id": "req-start-collab-001"
}
```

**Open Stream for Dynamic Joining:**
```json
{
  "method": "stream.start", 
  "params": {
    "metadata": {
      "purpose": "open_consultation",
      "topic": "machine_learning_optimization",
      "allowDynamicJoin": true,
      "maxParticipants": 5,
      "expertiseRequired": ["machine_learning", "optimization"]
    }
  },
  "id": "req-start-open-001"
}
```

**Emergency Response Stream:**
```json
{
  "method": "stream.start",
  "params": {
    "participants": [
      "agent-incident-coordinator",
      "agent-security-lead",
      "agent-communications"
    ],
    "metadata": {
      "purpose": "incident_response",
      "incidentId": "INC-2024-001",
      "severity": "CRITICAL",
      "escalationPolicy": "auto_escalate_after_15min",
      "broadcastChannel": "incident_command"
    }
  },
  "id": "req-start-emergency-001"
}
```

---

### StreamMessageParams Schema

Parameters for the `stream.message` method to send messages within active streams.

#### Schema Structure
```yaml
StreamMessageParams:
  type: object
  required: [streamId, message]
  properties:
    streamId:
      type: string
    message:
      $ref: '#/components/schemas/Message'
```

#### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `streamId` | ✅ | `string` | Target stream identifier |
| `message` | ✅ | `Message` | Message to send to stream |

#### Message Examples

**Analysis Question:**
```json
{
  "method": "stream.message",
  "params": {
    "streamId": "stream-collab-abc123",
    "message": {
      "role": "agent",
      "parts": [
        {
          "type": "TextPart",
          "content": "I'm seeing an anomaly in the Q3 revenue data. The Western region shows a 40% spike in October that doesn't align with historical patterns. Could you review the underlying transaction data?",
          "encoding": "utf8"
        },
        {
          "type": "DataPart",
          "content": {
            "region": "Western",
            "period": "2023-Q3", 
            "anomaly_score": 0.85,
            "expected_range": [180000, 220000],
            "actual_value": 308000
          },
          "mimeType": "application/json"
        }
      ],
      "timestamp": "2024-01-15T14:32:00Z",
      "agentId": "agent-data-analyst-001"
    }
  },
  "id": "req-msg-question-001"
}
```

**Expert Response with Visualization:**
```json
{
  "method": "stream.message",
  "params": {
    "streamId": "stream-collab-abc123", 
    "message": {
      "role": "agent",
      "parts": [
        {
          "type": "TextPart",
          "content": "Good catch! I found the source of the anomaly. There was a large corporate acquisition that closed in October, bringing in $127K in one-time revenue. This explains the spike. I've created a breakdown chart showing the adjusted baseline.",
          "encoding": "utf8"
        },
        {
          "type": "ImagePart",
          "content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ...",
          "mimeType": "image/png",
          "filename": "revenue_breakdown_adjusted.png",
          "size": 345678,
          "encoding": "base64",
          "width": 800,
          "height": 600
        },
        {
          "type": "DataPart",
          "content": {
            "acquisition_revenue": 127000,
            "organic_revenue": 181000,
            "adjusted_growth": 0.05,
            "acquisition_details": {
              "company": "TechCorp Solutions",
              "close_date": "2023-10-15",
              "contract_value": 127000
            }
          },
          "mimeType": "application/json"
        }
      ],
      "timestamp": "2024-01-15T14:35:00Z",
      "agentId": "agent-domain-expert-finance"
    }
  },
  "id": "req-msg-response-001"
}
```

**Follow-up Analysis:**
```json
{
  "method": "stream.message",
  "params": {
    "streamId": "stream-collab-abc123",
    "message": {
      "role": "agent", 
      "parts": [
        {
          "type": "TextPart",
          "content": "Perfect! That makes sense. I'll update the model to exclude one-time acquisition revenue and recalculate the growth metrics. The organic growth of 5% aligns much better with our projections. Should I also look for similar acquisition impacts in other quarters?",
          "encoding": "utf8"
        }
      ],
      "timestamp": "2024-01-15T14:37:00Z",
      "agentId": "agent-data-analyst-001"
    }
  },
  "id": "req-msg-followup-001"
}
```

---

### StreamEndParams Schema

Parameters for the `stream.end` method to terminate stream sessions.

#### Schema Structure
```yaml
StreamEndParams:
  type: object
  required: [streamId]
  properties:
    streamId:
      type: string
    reason:
      type: string
      description: Reason for ending stream
```

#### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `streamId` | ✅ | `string` | Stream to terminate |
| `reason` | ❌ | `string` | Human-readable termination reason |

#### Termination Examples

**Natural Completion:**
```json
{
  "method": "stream.end",
  "params": {
    "streamId": "stream-collab-abc123",
    "reason": "Analysis complete - revenue anomaly identified and resolved"
  },
  "id": "req-end-complete-001"
}
```

**Timeout Termination:**
```json
{
  "method": "stream.end",
  "params": {
    "streamId": "stream-consultation-xyz789",
    "reason": "Session timeout - maximum duration of 2 hours exceeded"
  },
  "id": "req-end-timeout-001"
}
```

**Emergency Shutdown:**
```json
{
  "method": "stream.end",
  "params": {
    "streamId": "stream-incident-response-456",
    "reason": "Incident resolved - all systems restored to normal operation"
  },
  "id": "req-end-emergency-001"
}
```

---

### StreamChunkParams Schema

Parameters for the `stream.chunk` method to deliver progressive message content in real-time.

#### Schema Structure
```yaml
StreamChunkParams:
  type: object
  required: [streamId, chunk, sequence]
  properties:
    streamId:
      type: string
    chunk:
      $ref: '#/components/schemas/Message'
    sequence:
      type: integer
      description: Sequence number for ordering chunks
    isLast:
      type: boolean
      default: false
      description: Indicates if this is the final chunk
```

#### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `streamId` | ✅ | `string` | Target stream identifier |
| `chunk` | ✅ | `Message` | Partial message content |
| `sequence` | ✅ | `integer` | Ordering sequence number |
| `isLast` | ❌ | `boolean` | Final chunk indicator |

#### Chunked Delivery Examples

**Progressive Text Generation:**
```json
// Chunk 1
{
  "method": "stream.chunk",
  "params": {
    "streamId": "stream-analysis-abc123",
    "chunk": {
      "role": "agent",
      "parts": [
        {
          "type": "TextPart", 
          "content": "Based on my analysis of the customer data, I've identified several key patterns:",
          "encoding": "utf8"
        }
      ],
      "timestamp": "2024-01-15T15:00:00Z",
      "agentId": "agent-analyst"
    },
    "sequence": 1,
    "isLast": false
  }
}

// Chunk 2  
{
  "method": "stream.chunk",
  "params": {
    "streamId": "stream-analysis-abc123",
    "chunk": {
      "role": "agent",
      "parts": [
        {
          "type": "TextPart",
          "content": "\n\n1. **High-Value Customers**: 15% of customers generate 60% of revenue",
          "encoding": "utf8"
        }
      ],
      "timestamp": "2024-01-15T15:00:02Z", 
      "agentId": "agent-analyst"
    },
    "sequence": 2,
    "isLast": false
  }
}

// Final Chunk
{
  "method": "stream.chunk", 
  "params": {
    "streamId": "stream-analysis-abc123",
    "chunk": {
      "role": "agent",
      "parts": [
        {
          "type": "TextPart",
          "content": "\n\n5. **Recommendation**: Focus retention efforts on the 'At Risk High-Value' segment for maximum ROI",
          "encoding": "utf8"
        }
      ],
      "timestamp": "2024-01-15T15:00:10Z",
      "agentId": "agent-analyst"
    },
    "sequence": 5,
    "isLast": true
  }
}
```

**Large File Transfer:**
```json
// Chunk 1 - File metadata
{
  "method": "stream.chunk",
  "params": {
    "streamId": "stream-data-transfer-xyz",
    "chunk": {
      "role": "agent",
      "parts": [
        {
          "type": "DataPart",
          "content": {
            "file_info": {
              "name": "customer_analysis_results.csv",
              "total_size": 15728640,
              "chunks": 15,
              "chunk_size": 1048576
            }
          },
          "mimeType": "application/json"
        }
      ],
      "agentId": "agent-data-processor"
    },
    "sequence": 1,
    "isLast": false
  }
}

// Chunk 2 - First data chunk
{
  "method": "stream.chunk",
  "params": {
    "streamId": "stream-data-transfer-xyz",
    "chunk": {
      "role": "agent", 
      "parts": [
        {
          "type": "FilePart",
          "content": "Y3VzdG9tZXJfaWQsbmFtZSxlbWFpbCxzZWdtZW50LGNourn...",
          "mimeType": "text/csv",
          "filename": "customer_analysis_results.csv",
          "encoding": "base64",
          "size": 1048576
        }
      ],
      "agentId": "agent-data-processor"
    },
    "sequence": 2,
    "isLast": false
  }
}
```

---

## Real-time Communication Patterns

### Synchronous Request-Response

Quick consultation pattern where one agent asks another for immediate assistance.

```
Agent A ──→ stream.start()
       ←── StreamObject (streamId)
       
Agent A ──→ stream.message("Need help with X")
       ←── stream.chunk("Let me analyze...")
       ←── stream.chunk("Here's the solution...")
       ←── stream.chunk("Complete response", isLast=true)
       
Agent A ──→ stream.end("Thank you")
```

### Multi-Agent Collaboration

Multiple agents working together on a complex problem with parallel contributions.

```
Agent A ──→ stream.start(participants=[B, C])
       ←── StreamObject (streamId)

Agent A ──→ stream.message("Found data anomaly")
Agent B ──→ stream.message("I'll check the source")  
Agent C ──→ stream.message("Running validation")

Agent B ──→ stream.chunk("Source is...")
Agent C ──→ stream.chunk("Validation shows...")
Agent A ──→ stream.message("Thanks, issue resolved")

Agent A ──→ stream.end("Problem solved")
```

### Progressive Content Delivery

Large content delivered incrementally to provide immediate feedback.

```
Agent A ──→ stream.start()
Agent A ──→ stream.chunk(sequence=1, "Starting analysis...")
Agent A ──→ stream.chunk(sequence=2, "Processing data...")
Agent A ──→ stream.chunk(sequence=3, "Found pattern 1...")
Agent A ──→ stream.chunk(sequence=4, "Found pattern 2...")
Agent A ──→ stream.chunk(sequence=5, "Summary...", isLast=true)
Agent A ──→ stream.end("Analysis complete")
```

### Interactive Problem Solving

Back-and-forth collaboration with real-time feedback and course correction.

```
Agent A ──→ "I'm seeing performance issues"
Agent B ──→ "What's the CPU usage?"
Agent A ──→ "85% average, spiking to 95%"
Agent B ──→ "Check memory allocation"
Agent A ──→ "Memory looks normal, 60% usage"
Agent B ──→ "Look at database connection pool"
Agent A ──→ "Found it! Pool exhausted"
Agent B ──→ "Increase pool size to 50"
Agent A ──→ "Applied fix, performance restored"
```

---

## Multi-Agent Collaboration

### Dynamic Participant Management

#### Adding Participants
```javascript
// Invite expert to ongoing stream
const inviteExpert = async (streamId, expertId, reason) => {
  await streamAPI.message(streamId, {
    role: 'system',
    parts: [{
      type: 'TextPart',
      content: `@${expertId} has been invited to join for: ${reason}`
    }]
  });
  
  // Agent joins stream (implementation specific)
  await notifyAgent(expertId, {
    type: 'stream_invitation',
    streamId: streamId,
    reason: reason,
    currentParticipants: await getStreamParticipants(streamId)
  });
};
```

#### Participant Coordination
```javascript
class StreamCoordinator {
  constructor(streamId) {
    this.streamId = streamId;
    this.participants = new Map();
    this.messageQueue = [];
  }
  
  async broadcastToAll(message, excludeAgentId = null) {
    const participants = await this.getActiveParticipants();
    
    for (const agentId of participants) {
      if (agentId !== excludeAgentId) {
        await this.sendDirectMessage(agentId, message);
      }
    }
  }
  
  async moderateDiscussion() {
    // Implement turn-taking, conflict resolution
    const currentSpeaker = await this.getCurrentSpeaker();
    const waitingQueue = await this.getWaitingQueue();
    
    if (waitingQueue.length > 0) {
      await this.notifyNextSpeaker(waitingQueue[0]);
    }
  }
}
```

### Role-Based Participation

```javascript
const roleBasedStream = {
  streamId: "stream-incident-response-001",
  participants: [
    {
      agentId: "agent-incident-commander",
      role: "coordinator",
      permissions: ["moderate", "invite", "end_stream"]
    },
    {
      agentId: "agent-security-specialist", 
      role: "expert",
      permissions: ["respond", "suggest"]
    },
    {
      agentId: "agent-communications",
      role: "support",
      permissions: ["broadcast", "document"]
    }
  ],
  rules: {
    coordinatorRequired: true,
    maxExperts: 3,
    requirePermissionToSpeak: false
  }
};
```

### Consensus Building

```javascript
class ConsensusManager {
  async proposeDecision(streamId, proposal) {
    await streamAPI.message(streamId, {
      role: 'system',
      parts: [{
        type: 'TextPart',
        content: `🗳️ **PROPOSAL**: ${proposal}\n\nPlease respond with: ✅ Agree, ❌ Disagree, or 🤔 Need Discussion`
      }]
    });
    
    this.trackVoting(streamId, proposal);
  }
  
  async trackVoting(streamId, proposal) {
    const votes = new Map();
    const participants = await getStreamParticipants(streamId);
    
    // Listen for responses and track votes
    const votePattern = /[✅❌🤔]/;
    // Implementation would listen to stream messages
    // and track votes until consensus reached
  }
}
```

---

## Chunk-Based Messaging

### Progressive Text Generation

```javascript
class ProgressiveTextGenerator {
  constructor(streamId, agentId) {
    this.streamId = streamId;
    this.agentId = agentId;
    this.sequence = 0;
    this.buffer = '';
  }
  
  async sendChunk(text, isComplete = false) {
    this.sequence++;
    
    await streamAPI.chunk(this.streamId, {
      chunk: {
        role: 'agent',
        parts: [{
          type: 'TextPart',
          content: text,
          encoding: 'utf8'
        }],
        agentId: this.agentId,
        timestamp: new Date().toISOString()
      },
      sequence: this.sequence,
      isLast: isComplete
    });
  }
  
  async generateAnalysis(data) {
    await this.sendChunk("🔍 Starting analysis...\n\n");
    
    // Simulate progressive analysis
    await this.sendChunk("📊 Processing data points: ");
    for (let i = 0; i <= 100; i += 10) {
      await this.sendChunk(`${i}%... `);
      await new Promise(resolve => setTimeout(resolve, 200));
    }
    
    await this.sendChunk("\n\n✅ Analysis complete!\n\n");
    await this.sendChunk("**Key Findings:**\n");
    await this.sendChunk("1. Revenue increased 15% YoY\n");
    await this.sendChunk("2. Customer retention improved to 94%\n");
    await this.sendChunk("3. New market segments identified\n\n", true);
  }
}
```

### Large Content Streaming

```javascript
class ContentStreamer {
  async streamLargeFile(streamId, filePath, chunkSize = 1024 * 1024) {
    const fileStats = await fs.stat(filePath);
    const totalChunks = Math.ceil(fileStats.size / chunkSize);
    
    // Send metadata first
    await streamAPI.chunk(streamId, {
      chunk: {
        role: 'agent',
        parts: [{
          type: 'DataPart',
          content: {
            fileInfo: {
              name: path.basename(filePath),
              size: fileStats.size,
              totalChunks: totalChunks,
              chunkSize: chunkSize
            }
          },
          mimeType: 'application/json'
        }]
      },
      sequence: 1,
      isLast: false
    });
    
    // Stream file chunks
    const fileStream = fs.createReadStream(filePath, { 
      highWaterMark: chunkSize 
    });
    
    let sequence = 2;
    for await (const chunk of fileStream) {
      const base64Chunk = chunk.toString('base64');
      const isLastChunk = sequence === totalChunks + 1;
      
      await streamAPI.chunk(streamId, {
        chunk: {
          role: 'agent',
          parts: [{
            type: 'FilePart',
            content: base64Chunk,
            encoding: 'base64',
            size: chunk.length
          }]
        },
        sequence: sequence,
        isLast: isLastChunk
      });
      
      sequence++;
    }
  }
}
```

### Chunk Reassembly

```javascript
class ChunkReassembler {
  constructor() {
    this.streams = new Map();
  }
  
  processChunk(streamId, chunkParams) {
    if (!this.streams.has(streamId)) {
      this.streams.set(streamId, {
        chunks: new Map(),
        expectedSequence: 1,
        isComplete: false
      });
    }
    
    const streamData = this.streams.get(streamId);
    const { chunk, sequence, isLast } = chunkParams;
    
    // Store chunk
    streamData.chunks.set(sequence, chunk);
    
    // Check for complete message
    if (isLast) {
      streamData.isComplete = true;
    }
    
    // Try to reassemble if we have consecutive chunks
    return this.tryReassemble(streamId);
  }
  
  tryReassemble(streamId) {
    const streamData = this.streams.get(streamId);
    const reassembled = [];
    
    // Get consecutive chunks starting from expected sequence
    let currentSequence = streamData.expectedSequence;
    
    while (streamData.chunks.has(currentSequence)) {
      reassembled.push(streamData.chunks.get(currentSequence));
      streamData.chunks.delete(currentSequence);
      currentSequence++;
    }
    
    streamData.expectedSequence = currentSequence;
    
    // If complete and all chunks processed, clean up
    if (streamData.isComplete && streamData.chunks.size === 0) {
      this.streams.delete(streamId);
    }
    
    return reassembled;
  }
}
```

---

## Best Practices

### Stream Design Principles

#### 1. Keep Sessions Focused
```javascript
// Good: Specific purpose and scope
const analysisStream = await streamAPI.start({
  metadata: {
    purpose: "validate_ml_model_accuracy",
    scope: "customer_churn_prediction", 
    expectedDuration: "15_minutes",
    participants: ["agent-ml-expert", "agent-data-validator"]
  }
});

// Avoid: Vague or overly broad scope
const broadStream = await streamAPI.start({
  metadata: {
    purpose: "general_discussion", // Too vague
    scope: "everything_ml_related" // Too broad
  }
});
```

#### 2. Manage Participant Flow
```javascript
class StreamManager {
  async optimizeParticipation(streamId) {
    const participants = await this.getActiveParticipants(streamId);
    const activity = await this.getRecentActivity(streamId, '5m');
    
    // Remove inactive participants
    for (const participant of participants) {
      const lastActivity = activity.get(participant);
      if (!lastActivity || this.isInactive(lastActivity)) {
        await this.requestParticipantRemoval(streamId, participant);
      }
    }
    
    // Invite relevant experts if needed
    const currentTopic = await this.analyzeTopic(streamId);
    const suggestedExperts = await this.findExperts(currentTopic);
    
    if (suggestedExperts.length > 0) {
      await this.suggestParticipants(streamId, suggestedExperts);
    }
  }
}
```

#### 3. Handle Concurrent Messages
```javascript
class MessageCoordinator {
  constructor(streamId) {
    this.streamId = streamId;
    this.messageQueue = [];
    this.isProcessing = false;
  }
  
  async sendMessage(message) {
    return new Promise((resolve, reject) => {
      this.messageQueue.push({ message, resolve, reject });
      this.processQueue();
    });
  }
  
  async processQueue() {
    if (this.isProcessing) return;
    this.isProcessing = true;
    
    while (this.messageQueue.length > 0) {
      const { message, resolve, reject } = this.messageQueue.shift();
      
      try {
        // Add small delay to prevent message collision
        await new Promise(r => setTimeout(r, 50));
        const result = await streamAPI.message(this.streamId, message);
        resolve(result);
      } catch (error) {
        reject(error);
      }
    }
    
    this.isProcessing = false;
  }
}
```

### Performance Optimization

#### 1. Connection Management
```javascript
class StreamConnection {
  constructor(streamId) {
    this.streamId = streamId;
    this.connection = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }
  
  async connect() {
    try {
      this.connection = await this.establishConnection();
      this.reconnectAttempts = 0;
      
      this.connection.on('disconnect', this.handleDisconnect.bind(this));
      this.connection.on('error', this.handleError.bind(this));
      
    } catch (error) {
      await this.handleConnectionFailure(error);
    }
  }
  
  async handleDisconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000;
      
      console.log(`Reconnecting to stream ${this.streamId} in ${delay}ms (attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => this.connect(), delay);
    } else {
      console.error(`Failed to reconnect to stream ${this.streamId} after ${this.maxReconnectAttempts} attempts`);
      await this.fallbackToPolling();
    }
  }
}
```

#### 2. Message Batching
```javascript
class MessageBatcher {
  constructor(streamId, batchSize = 10, flushInterval = 1000) {
    this.streamId = streamId;
    this.batchSize = batchSize;
    this.flushInterval = flushInterval;
    this.batch = [];
    this.timer = null;
  }
  
  addMessage(message) {
    this.batch.push(message);
    
    if (this.batch.length >= this.batchSize) {
      this.flush();
    } else if (!this.timer) {
      this.timer = setTimeout(() => this.flush(), this.flushInterval);
    }
  }
  
  async flush() {
    if (this.batch.length === 0) return;
    
    const messages = [...this.batch];
    this.batch = [];
    
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    
    try {
      await streamAPI.sendBatch(this.streamId, messages);
    } catch (error) {
      console.error('Batch send failed:', error);
      // Re-queue messages or handle error
    }
  }
}
```

#### 3. Memory Management
```javascript
class StreamMemoryManager {
  constructor(maxHistorySize = 1000) {
    this.maxHistorySize = maxHistorySize;
    this.messageHistory = new Map();
  }
  
  addMessage(streamId, message) {
    if (!this.messageHistory.has(streamId)) {
      this.messageHistory.set(streamId, []);
    }
    
    const history = this.messageHistory.get(streamId);
    history.push(message);
    
    // Trim history if too large
    if (history.length > this.maxHistorySize) {
      const excess = history.length - this.maxHistorySize;
      history.splice(0, excess);
    }
  }
  
  cleanupClosedStreams() {
    for (const [streamId, history] of this.messageHistory) {
      // Check if stream is still active
      if (this.isStreamClosed(streamId)) {
        // Archive important messages before cleanup
        this.archiveMessages(streamId, history);
        this.messageHistory.delete(streamId);
      }
    }
  }
}
```

---

## Security and Authentication

### Stream Access Control

```javascript
class StreamAccessControl {
  async validateStreamAccess(streamId, agentId, operation) {
    const stream = await this.getStream(streamId);
    const agent = await this.getAgent(agentId);
    
    // Check basic stream membership
    if (operation === 'join' || operation === 'message') {
      if (!stream.participants.includes(agentId)) {
        const canJoin = await this.checkJoinPermissions(stream, agent);
        if (!canJoin) {
          throw new SecurityError('Agent not authorized to join stream');
        }
      }
    }
    
    // Check operation-specific permissions
    switch (operation) {
      case 'end':
        return this.canEndStream(stream, agent);
      case 'invite':
        return this.canInviteParticipants(stream, agent);
      case 'moderate':
        return this.canModerateStream(stream, agent);
      default:
        return true;
    }
  }
  
  async checkJoinPermissions(stream, agent) {
    // Check if stream allows dynamic joining
    if (!stream.metadata.allowDynamicJoin) {
      return false;
    }
    
    // Check agent capabilities vs required expertise
    const requiredExpertise = stream.metadata.expertiseRequired || [];
    const agentCapabilities = agent.capabilities || [];
    
    return requiredExpertise.some(skill => 
      agentCapabilities.includes(skill)
    );
  }
}
```

### Message Encryption

```javascript
class SecureStreamMessaging {
  constructor(encryptionKey) {
    this.encryptionKey = encryptionKey;
  }
  
  async encryptMessage(message, streamId) {
    const streamKey = await this.deriveStreamKey(streamId);
    
    // Encrypt sensitive parts
    const encryptedParts = await Promise.all(
      message.parts.map(async part => {
        if (this.shouldEncrypt(part)) {
          return {
            ...part,
            content: await this.encrypt(part.content, streamKey),
            encrypted: true
          };
        }
        return part;
      })
    );
    
    return {
      ...message,
      parts: encryptedParts
    };
  }
  
  async decryptMessage(message, streamId) {
    const streamKey = await this.deriveStreamKey(streamId);
    
    const decryptedParts = await Promise.all(
      message.parts.map(async part => {
        if (part.encrypted) {
          return {
            ...part,
            content: await this.decrypt(part.content, streamKey),
            encrypted: false
          };
        }
        return part;
      })
    );
    
    return {
      ...message,
      parts: decryptedParts
    };
  }
}
```

### Audit Logging

```javascript
class StreamAuditLogger {
  async logStreamEvent(event) {
    const auditEntry = {
      timestamp: new Date().toISOString(),
      streamId: event.streamId,
      eventType: event.type,
      agentId: event.agentId,
      details: event.details,
      ipAddress: event.ipAddress,
      userAgent: event.userAgent
    };
    
    // Store in secure audit log
    await this.storeAuditEntry(auditEntry);
    
    // Check for suspicious patterns
    await this.analyzeForAnomalies(auditEntry);
  }
  
  async analyzeForAnomalies(entry) {
    // Check for rapid-fire messages (potential spam)
    const recentMessages = await this.getRecentMessages(
      entry.agentId, 
      '1m'
    );
    
    if (recentMessages.length > 50) {
      await this.flagSuspiciousActivity(entry, 'HIGH_MESSAGE_RATE');
    }
    
    // Check for unauthorized access attempts
    if (entry.eventType === 'STREAM_JOIN_DENIED') {
      const denials = await this.getRecentDenials(entry.agentId, '5m');
      if (denials.length > 3) {
        await this.flagSuspiciousActivity(entry, 'REPEATED_ACCESS_DENIED');
      }
    }
  }
}
```

---

## Examples

### Complete Real-time Analysis Session

This example demonstrates a comprehensive collaborative analysis session using all Stream Management schemas.

#### 1. Stream Initiation
```json
{
  "jsonrpc": "2.0",
  "method": "stream.start",
  "params": {
    "participants": ["agent-data-scientist", "agent-domain-expert"],
    "metadata": {
      "purpose": "anomaly_investigation",
      "urgency": "HIGH",
      "topic": "unusual_traffic_patterns",
      "expectedDuration": "45_minutes",
      "requiresExpertise": ["network_analysis", "security"]
    }
  },
  "id": "req-start-investigation-001"
}
```

#### 2. Stream Created
```json
{
  "jsonrpc": "2.0",
  "id": "req-start-investigation-001",
  "result": {
    "type": "stream",
    "stream": {
      "streamId": "stream-investigation-20240115-urgent-001",
      "status": "ACTIVE",
      "participants": ["agent-data-scientist", "agent-domain-expert"],
      "createdAt": "2024-01-15T16:30:00Z",
      "metadata": {
        "purpose": "anomaly_investigation",
        "urgency": "HIGH",
        "topic": "unusual_traffic_patterns"
      }
    }
  }
}
```

#### 3. Initial Problem Description
```json
{
  "jsonrpc": "2.0",
  "method": "stream.message",
  "params": {
    "streamId": "stream-investigation-20240115-urgent-001",
    "message": {
      "role": "agent",
      "parts": [
        {
          "type": "TextPart",
          "content": "🚨 **URGENT ANOMALY DETECTED**\n\nI've identified unusual traffic patterns in our network that need immediate investigation:\n\n📊 **Anomaly Details:**\n- Traffic volume: 340% above baseline\n- Source: Multiple distributed IPs\n- Pattern: Consistent 30-second intervals\n- Duration: Started 2 hours ago\n\nThis could indicate a coordinated attack or system malfunction. Need your security expertise to analyze the pattern.",
          "encoding": "utf8"
        },
        {
          "type": "DataPart",
          "content": {
            "anomaly_metrics": {
              "baseline_rps": 1250,
              "current_rps": 4250,
              "increase_percentage": 3.4,
              "duration_minutes": 127,
              "source_ips": 847,
              "geographic_distribution": {
                "us_east": 0.35,
                "eu_west": 0.28,
                "asia_pacific": 0.37
              },
              "pattern_confidence": 0.94
            }
          },
          "mimeType": "application/json"
        }
      ],
      "timestamp": "2024-01-15T16:30:15Z",
      "agentId": "agent-data-scientist"
    }
  },
  "id": "req-msg-initial-001"
}
```

#### 4. Expert Analysis with Progressive Delivery
```json
// Chunk 1 - Initial assessment
{
  "jsonrpc": "2.0",
  "method": "stream.chunk",
  "params": {
    "streamId": "stream-investigation-20240115-urgent-001",
    "chunk": {
      "role": "agent",
      "parts": [
        {
          "type": "TextPart",
          "content": "🔍 **SECURITY ANALYSIS STARTING**\n\nReviewing the traffic patterns... This distribution and timing suggests coordinated activity. Let me check our threat intelligence feeds.",
          "encoding": "utf8"
        }
      ],
      "timestamp": "2024-01-15T16:31:00Z",
      "agentId": "agent-domain-expert"
    },
    "sequence": 1,
    "isLast": false
  }
}

// Chunk 2 - Threat intelligence results
{
  "jsonrpc": "2.0", 
  "method": "stream.chunk",
  "params": {
    "streamId": "stream-investigation-20240115-urgent-001",
    "chunk": {
      "role": "agent",
      "parts": [
        {
          "type": "TextPart",
          "content": "\n\n✅ **THREAT INTELLIGENCE CHECK COMPLETE**\n\n- 67% of source IPs match known botnet infrastructure\n- Pattern matches 'Distributed Stress Test' signature\n- NOT a DDoS attack - appears to be load testing behavior",
          "encoding": "utf8"
        },
        {
          "type": "DataPart",
          "content": {
            "threat_analysis": {
              "botnet_match_percentage": 0.67,
              "attack_signature": "distributed_stress_test",
              "threat_level": "MEDIUM",
              "likely_intent": "system_reconnaissance",
              "recommended_action": "monitor_and_rate_limit"
            }
          },
          "mimeType": "application/json"
        }
      ],
      "timestamp": "2024-01-15T16:32:30Z",
      "agentId": "agent-domain-expert"
    },
    "sequence": 2,
    "isLast": false
  }
}

// Chunk 3 - Final recommendations
{
  "jsonrpc": "2.0",
  "method": "stream.chunk", 
  "params": {
    "streamId": "stream-investigation-20240115-urgent-001",
    "chunk": {
      "role": "agent",
      "parts": [
        {
          "type": "TextPart",
          "content": "\n\n🎯 **RECOMMENDATIONS**\n\n1. **Immediate**: Implement rate limiting (max 10 req/sec per IP)\n2. **Short-term**: Block known botnet IPs (list attached)\n3. **Monitor**: Watch for pattern changes over next 24 hours\n4. **Alert**: Notify if traffic exceeds 500% baseline\n\n**Assessment**: Low-risk reconnaissance, not an active attack. Standard mitigation measures sufficient.",
          "encoding": "utf8"
        }
      ],
      "timestamp": "2024-01-15T16:33:45Z",
      "agentId": "agent-domain-expert"
    },
    "sequence": 3,
    "isLast": true
  }
}
```

#### 5. Implementation Confirmation
```json
{
  "jsonrpc": "2.0",
  "method": "stream.message",
  "params": {
    "streamId": "stream-investigation-20240115-urgent-001",
    "message": {
      "role": "agent",
      "parts": [
        {
          "type": "TextPart",
          "content": "✅ **MITIGATION IMPLEMENTED**\n\nThanks for the rapid analysis! I've implemented your recommendations:\n\n- Rate limiting: Active (10 req/sec per IP)\n- Blocked IPs: 847 botnet IPs now blocked\n- Monitoring: Enhanced alerting configured\n- Traffic: Already dropping to 180% baseline\n\n**Result**: Anomaly contained, normal operations resuming. Excellent collaboration!",
          "encoding": "utf8"
        },
        {
          "type": "DataPart",
          "content": {
            "mitigation_results": {
              "rate_limiting_active": true,
              "blocked_ips": 847,
              "current_traffic_percentage": 1.8,
              "estimated_normalization": "15_minutes",
              "false_positive_rate": 0.02
            }
          },
          "mimeType": "application/json"
        }
      ],
      "timestamp": "2024-01-15T16:35:00Z",
      "agentId": "agent-data-scientist"
    }
  },
  "id": "req-msg-confirmation-001"
}
```

#### 6. Stream Closure
```json
{
  "jsonrpc": "2.0",
  "method": "stream.end",
  "params": {
    "streamId": "stream-investigation-20240115-urgent-001",
    "reason": "Anomaly successfully investigated and mitigated - threat contained"
  },
  "id": "req-end-investigation-001"
}
```

---

## Integration Patterns

### WebSocket Integration

```javascript
class StreamWebSocketManager {
  constructor(authToken) {
    this.authToken = authToken;
    this.connections = new Map();
    this.messageHandlers = new Map();
  }
  
  async connectToStream(streamId) {
    const ws = new WebSocket(`wss://api.example.com/streams/${streamId}`, {
      headers: {
        'Authorization': `Bearer ${this.authToken}`
      }
    });
    
    ws.on('open', () => {
      console.log(`Connected to stream ${streamId}`);
      this.connections.set(streamId, ws);
    });
    
    ws.on('message', (data) => {
      const message = JSON.parse(data);
      this.handleStreamMessage(streamId, message);
    });
    
    ws.on('close', () => {
      console.log(`Disconnected from stream ${streamId}`);
      this.connections.delete(streamId);
    });
    
    return ws;
  }
  
  async sendMessage(streamId, message) {
    const ws = this.connections.get(streamId);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'stream.message',
        streamId: streamId,
        message: message
      }));
    } else {
      throw new Error(`No active connection to stream ${streamId}`);
    }
  }
  
  handleStreamMessage(streamId, message) {
    const handlers = this.messageHandlers.get(streamId) || [];
    handlers.forEach(handler => handler(message));
  }
}
```

### Event-Driven Architecture

```javascript
class StreamEventBus {
  constructor() {
    this.subscribers = new Map();
    this.activeStreams = new Set();
  }
  
  subscribe(eventType, handler) {
    if (!this.subscribers.has(eventType)) {
      this.subscribers.set(eventType, []);
    }
    this.subscribers.get(eventType).push(handler);
  }
  
  async emit(eventType, data) {
    const handlers = this.subscribers.get(eventType) || [];
    await Promise.all(handlers.map(handler => 
      this.safeHandlerCall(handler, data)
    ));
  }
  
  async safeHandlerCall(handler, data) {
    try {
      await handler(data);
    } catch (error) {
      console.error('Event handler failed:', error);
    }
  }
  
  // Stream-specific events
  async onStreamStarted(streamData) {
    this.activeStreams.add(streamData.streamId);
    await this.emit('stream.started', streamData);
  }
  
  async onStreamMessage(messageData) {
    await this.emit('stream.message', messageData);
    await this.emit(`stream.${messageData.streamId}.message`, messageData);
  }
  
  async onStreamEnded(streamData) {
    this.activeStreams.delete(streamData.streamId);
    await this.emit('stream.ended', streamData);
  }
}
```

### Microservices Coordination

```javascript
class StreamOrchestrator {
  constructor(serviceRegistry) {
    this.serviceRegistry = serviceRegistry;
    this.activeStreams = new Map();
  }
  
  async orchestrateAnalysisStream(analysisRequest) {
    // Start collaborative stream
    const stream = await this.startStream({
      participants: [
        'agent-data-preprocessor',
        'agent-ml-analyst', 
        'agent-visualization-expert'
      ],
      metadata: {
        purpose: 'collaborative_analysis',
        analysisType: analysisRequest.type,
        priority: analysisRequest.priority
      }
    });
    
    // Coordinate the analysis workflow
    const workflow = new AnalysisWorkflow(stream.streamId);
    
    // Step 1: Data preprocessing
    await workflow.delegateToAgent('agent-data-preprocessor', {
      task: 'preprocess_data',
      data: analysisRequest.rawData
    });
    
    // Step 2: Analysis (waits for preprocessor)
    workflow.onAgentComplete('agent-data-preprocessor', async (results) => {
      await workflow.delegateToAgent('agent-ml-analyst', {
        task: 'analyze_patterns',
        data: results.cleanedData
      });
    });
    
    // Step 3: Visualization (waits for analysis)
    workflow.onAgentComplete('agent-ml-analyst', async (results) => {
      await workflow.delegateToAgent('agent-visualization-expert', {
        task: 'create_visualizations',
        data: results.analysisResults
      });
    });
    
    return stream.streamId;
  }
}

class AnalysisWorkflow {
  constructor(streamId) {
    this.streamId = streamId;
    this.completionHandlers = new Map();
    this.results = new Map();
  }
  
  async delegateToAgent(agentId, task) {
    await streamAPI.message(this.streamId, {
      role: 'system',
      parts: [{
        type: 'DataPart',
        content: {
          type: 'task_delegation',
          agentId: agentId,
          task: task
        },
        mimeType: 'application/json'
      }]
    });
  }
  
  onAgentComplete(agentId, handler) {
    this.completionHandlers.set(agentId, handler);
  }
  
  async processCompletion(agentId, results) {
    this.results.set(agentId, results);
    
    const handler = this.completionHandlers.get(agentId);
    if (handler) {
      await handler(results);
    }
  }
}
```

---

## Conclusion

The Stream Management system provides a comprehensive framework for real-time, interactive communication in the ACP protocol. The five schemas work together to enable:

- **Real-time Collaboration**: Immediate message exchange between multiple agents
- **Progressive Content Delivery**: Chunk-based streaming for large content and live updates
- **Multi-participant Sessions**: Support for complex collaborative scenarios
- **Flexible Communication**: Both structured and free-form interaction patterns
- **Performance Optimization**: Efficient handling of high-frequency, low-latency communication
- **Enterprise Security**: Access control, encryption, and audit capabilities

The system is designed to complement the asynchronous Task Management system, providing organizations with a complete communication framework that spans from long-running analytical tasks to real-time collaborative problem-solving.

By implementing these patterns and best practices, you can build sophisticated agent collaboration systems that enable immediate, interactive cooperation while maintaining the reliability, security, and scalability required for enterprise environments.

The Stream Management schemas integrate seamlessly with the Shared Communication and JSON-RPC Foundation to provide a complete real-time communication framework for your ACP agent ecosystem. 