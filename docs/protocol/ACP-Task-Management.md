# Task Management Schemas for ACP Protocol

## Table of Contents
- [Overview](#overview)
- [Task Lifecycle](#task-lifecycle)
- [Schema Definitions](#schema-definitions)
  - [TaskObject Schema](#taskobject-schema)
  - [TasksCreateParams Schema](#taskscreateParams-schema)
  - [TasksSendParams Schema](#taskssendparams-schema)
  - [TasksGetParams Schema](#tasksgetparams-schema)
  - [TasksCancelParams Schema](#taskscancelparams-schema)
  - [TasksSubscribeParams Schema](#taskssubscribeparams-schema)
  - [TaskNotificationParams Schema](#tasknotificationparams-schema)
- [Task Operations](#task-operations)
- [Notification System](#notification-system)
- [Best Practices](#best-practices)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Integration Patterns](#integration-patterns)

---

## Overview

The **Task Management** system in ACP provides asynchronous, non-blocking communication between agents. Tasks represent units of work that can be created, tracked, updated, and completed over time, allowing agents to handle complex, long-running operations while maintaining clear communication and progress tracking.

### Core Concepts

- **Asynchronous Processing**: Tasks run independently, allowing agents to work on multiple requests simultaneously
- **Lifecycle Management**: Clear status progression from creation to completion
- **Rich Communication**: Full conversation history with multimodal content support
- **Deliverable Tracking**: Structured artifacts generated during task execution
- **Notification System**: Real-time updates via webhooks for task events
- **Metadata Support**: Extensible properties for custom task management

### Task vs Stream Communication

| Aspect | Tasks (Async) | Streams (Real-time) |
|--------|---------------|-------------------|
| **Duration** | Long-running (minutes to hours) | Short-lived (seconds to minutes) |
| **Interaction** | Non-blocking, fire-and-forget | Interactive, real-time |
| **Use Case** | Data analysis, report generation | Collaborative problem solving |
| **Communication** | Message history + final artifacts | Real-time message exchange |
| **Status** | Lifecycle states (SUBMITTED → COMPLETED) | Active/Paused/Closed |

---

## Task Lifecycle

### State Diagram

```
    ┌─────────────┐
    │  SUBMITTED  │ ← Task created, queued for processing
    └─────┬───────┘
          │
          ▼
    ┌─────────────┐
    │   WORKING   │ ← Agent actively processing
    └─────┬───────┘
          │
          ├─────────────────┬─────────────────┬─────────────────┐
          ▼                 ▼                 ▼                 ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │ INPUT_REQ'D │   │  COMPLETED  │   │   FAILED    │   │  CANCELED   │
    └─────┬───────┘   └─────────────┘   └─────────────┘   └─────────────┘
          │                 │                 │                 │
          └─────────────────┼─────────────────┼─────────────────┤
                           │                 │                 │
                      [Terminal States]  [Terminal States] [Terminal States]
```

### State Definitions

#### 🔵 SUBMITTED
- **Description**: Task has been created and is queued for processing
- **Duration**: Typically seconds to minutes
- **Next States**: `WORKING`, `CANCELED`
- **Agent Action**: Task assignment and initial validation
- **User Action**: Can cancel if needed

#### 🟡 WORKING  
- **Description**: Agent is actively processing the task
- **Duration**: Minutes to hours depending on complexity
- **Next States**: `INPUT_REQUIRED`, `COMPLETED`, `FAILED`, `CANCELED`
- **Agent Action**: Processing data, generating results, providing updates
- **User Action**: Can send additional messages or cancel

#### 🟠 INPUT_REQUIRED
- **Description**: Agent needs additional input or clarification
- **Duration**: Depends on user response time
- **Next States**: `WORKING`, `CANCELED`
- **Agent Action**: Waiting for user response
- **User Action**: Provide requested information via `tasks.send`

#### 🟢 COMPLETED
- **Description**: Task finished successfully with results
- **Duration**: Permanent (terminal state)
- **Next States**: None
- **Agent Action**: Final artifacts and summary provided
- **User Action**: Review results and artifacts

#### 🔴 FAILED
- **Description**: Task encountered unrecoverable error
- **Duration**: Permanent (terminal state)
- **Next States**: None
- **Agent Action**: Error details and diagnostic information provided
- **User Action**: Review error and potentially create new task

#### ⚫ CANCELED
- **Description**: Task was cancelled by user, agent, or system
- **Duration**: Permanent (terminal state)
- **Next States**: None
- **Agent Action**: Cleanup and cancellation confirmation
- **User Action**: Task is terminated

### Lifecycle Events

Each state transition triggers notifications to subscribed endpoints:

- `STATUS_CHANGE` - Task moved between states
- `NEW_MESSAGE` - Agent or user added message to task
- `NEW_ARTIFACT` - Agent generated new deliverable
- `COMPLETED` - Task finished successfully
- `FAILED` - Task failed with error

---

## Schema Definitions

### TaskObject Schema

The **TaskObject** is the core entity representing a unit of work in the ACP system. It contains the complete state, history, and results of a task.

#### Schema Structure
```yaml
TaskObject:
  type: object
  required: [taskId, status, createdAt]
  properties:
    taskId:
      type: string
      description: Unique identifier for the task
    status:
      type: string
      enum: [SUBMITTED, WORKING, INPUT_REQUIRED, COMPLETED, FAILED, CANCELED]
    createdAt:
      type: string
      format: date-time
    updatedAt:
      type: string
      format: date-time
    assignedAgent:
      type: string
      description: ID of agent processing this task
    messages:
      type: array
      items:
        $ref: '#/components/schemas/Message'
      description: Conversation history for this task
    artifacts:
      type: array
      items:
        $ref: '#/components/schemas/Artifact'
      description: Files, data, or outputs generated during task execution
    metadata:
      type: object
      additionalProperties: true
      description: Custom task metadata
```

#### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `taskId` | ✅ | `string` | Unique identifier for tracking and referencing |
| `status` | ✅ | `enum` | Current lifecycle state |
| `createdAt` | ✅ | `datetime` | Task creation timestamp |
| `updatedAt` | ❌ | `datetime` | Last modification timestamp |
| `assignedAgent` | ❌ | `string` | Agent ID responsible for processing |
| `messages` | ❌ | `Message[]` | Complete conversation history |
| `artifacts` | ❌ | `Artifact[]` | Generated deliverables and outputs |
| `metadata` | ❌ | `object` | Custom properties and processing context |

#### TaskObject Examples

**Data Analysis Task - Completed:**
```json
{
  "taskId": "task-customer-analysis-20240115-abc123",
  "status": "COMPLETED",
  "createdAt": "2024-01-15T09:00:00Z",
  "updatedAt": "2024-01-15T11:30:00Z",
  "assignedAgent": "agent-data-scientist-001",
  "messages": [
    {
      "role": "user",
      "parts": [
        {
          "type": "TextPart",
          "content": "Please analyze customer churn patterns in our Q4 data and provide actionable insights."
        },
        {
          "type": "FilePart",
          "content": "...",
          "mimeType": "text/csv",
          "filename": "customer_data_q4.csv",
          "size": 5242880
        }
      ],
      "timestamp": "2024-01-15T09:00:00Z"
    },
    {
      "role": "agent",
      "parts": [
        {
          "type": "TextPart",
          "content": "I've completed the customer churn analysis. Key findings include a 23% churn rate among customers with <6 month tenure and strong correlation between support ticket volume and churn probability."
        }
      ],
      "timestamp": "2024-01-15T11:30:00Z",
      "agentId": "agent-data-scientist-001"
    }
  ],
  "artifacts": [
    {
      "artifactId": "churn-analysis-report-001",
      "name": "Customer Churn Analysis Report",
      "description": "Comprehensive analysis of Q4 customer churn patterns with predictive insights and recommendations",
      "parts": [
        {
          "type": "FilePart",
          "content": "...",
          "mimeType": "application/pdf",
          "filename": "churn_analysis_report.pdf",
          "size": 2097152
        },
        {
          "type": "DataPart",
          "content": {
            "churn_rate": 0.23,
            "high_risk_segments": ["new_customers", "high_support_volume"],
            "retention_recommendations": [
              "implement_onboarding_program",
              "proactive_customer_success",
              "support_quality_improvement"
            ]
          },
          "mimeType": "application/json"
        }
      ],
      "createdAt": "2024-01-15T11:30:00Z",
      "createdBy": "agent-data-scientist-001",
      "version": "1.0"
    }
  ],
  "metadata": {
    "priority": "HIGH",
    "category": "customer_analytics",
    "deadline": "2024-01-16T17:00:00Z",
    "estimatedHours": 3.0,
    "actualHours": 2.5,
    "dataQualityScore": 0.94,
    "confidenceLevel": 0.87,
    "businessImpact": "high",
    "tags": ["churn", "analytics", "retention", "q4"]
  }
}
```

**Task Requiring Input:**
```json
{
  "taskId": "task-report-generation-def456",
  "status": "INPUT_REQUIRED",
  "createdAt": "2024-01-15T14:00:00Z",
  "updatedAt": "2024-01-15T14:30:00Z",
  "assignedAgent": "agent-report-builder",
  "messages": [
    {
      "role": "user",
      "parts": [
        {
          "type": "TextPart",
          "content": "Create a comprehensive monthly business review report for the executive team."
        }
      ],
      "timestamp": "2024-01-15T14:00:00Z"
    },
    {
      "role": "agent",
      "parts": [
        {
          "type": "TextPart",
          "content": "I can create the monthly business review report. However, I need clarification on several points to ensure the report meets your specific needs:\n\n1. Which departments should be included? (Sales, Marketing, Operations, Finance, etc.)\n2. What metrics are most important for this audience?\n3. Should I include year-over-year comparisons?\n4. What format do you prefer? (PowerPoint, PDF, interactive dashboard)\n5. Are there any specific KPIs or goals I should highlight?\n\nOnce you provide these details, I can generate a comprehensive report within 45 minutes."
        }
      ],
      "timestamp": "2024-01-15T14:30:00Z",
      "agentId": "agent-report-builder"
    }
  ],
  "artifacts": [],
  "metadata": {
    "priority": "HIGH",
    "category": "executive_reporting",
    "waitingFor": "user_specifications",
    "estimatedCompletionAfterInput": "45_minutes",
    "requiredClarifications": [
      "department_scope",
      "metric_selection",
      "comparison_timeframe",
      "output_format",
      "kpi_priorities"
    ]
  }
}
```

---

### TasksCreateParams Schema

Parameters for the `tasks.create` method to initiate new task processing.

#### Schema Structure
```yaml
TasksCreateParams:
  type: object
  required: [initialMessage]
  properties:
    initialMessage:
      $ref: '#/components/schemas/Message'
    assignTo:
      type: string
      description: Specific agent ID to assign task to
    priority:
      type: string
      enum: [LOW, NORMAL, HIGH, URGENT]
      default: NORMAL
    metadata:
      type: object
      additionalProperties: true
```

#### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `initialMessage` | ✅ | `Message` | Starting message defining the task requirements |
| `assignTo` | ❌ | `string` | Specific agent ID for direct assignment |
| `priority` | ❌ | `enum` | Task urgency level for queue management |
| `metadata` | ❌ | `object` | Custom properties for task categorization |

#### Priority Levels

- **LOW**: Non-urgent tasks, processed when resources available
- **NORMAL**: Standard priority, processed in order (default)
- **HIGH**: Important tasks, elevated queue position
- **URGENT**: Critical tasks, immediate processing required

#### Usage Examples

**Basic Task Creation:**
```json
{
  "method": "tasks.create",
  "params": {
    "initialMessage": {
      "role": "user",
      "parts": [
        {
          "type": "TextPart",
          "content": "Analyze the sales performance data and identify top-performing products for Q4."
        }
      ],
      "timestamp": "2024-01-15T10:00:00Z"
    },
    "priority": "HIGH"
  },
  "id": "req-create-analysis-001"
}
```

**Task with Specific Agent Assignment:**
```json
{
  "method": "tasks.create",
  "params": {
    "initialMessage": {
      "role": "user",
      "parts": [
        {
          "type": "TextPart",
          "content": "Generate a financial compliance report for the audit committee."
        }
      ],
      "timestamp": "2024-01-15T10:00:00Z"
    },
    "assignTo": "agent-compliance-specialist",
    "priority": "URGENT",
    "metadata": {
      "deadline": "2024-01-16T09:00:00Z",
      "category": "compliance",
      "stakeholder": "audit_committee",
      "confidentiality": "high"
    }
  },
  "id": "req-create-compliance-001"
}
```

**Task with File Upload:**
```json
{
  "method": "tasks.create",
  "params": {
    "initialMessage": {
      "role": "user",
      "parts": [
        {
          "type": "TextPart",
          "content": "Please clean and validate this customer dataset. Remove duplicates and standardize the format."
        },
        {
          "type": "FilePart",
          "content": "dXNlcklkLG5hbWUsZW1haWwscGhvbmUNCjEsIkpvaG4gRG9l...",
          "mimeType": "text/csv",
          "filename": "raw_customer_data.csv",
          "size": 1048576,
          "encoding": "base64"
        }
      ],
      "timestamp": "2024-01-15T10:00:00Z"
    },
    "metadata": {
      "dataProcessing": true,
      "expectedRecords": 15000,
      "outputFormat": "csv"
    }
  },
  "id": "req-create-dataclean-001"
}
```

---

### TasksSendParams Schema

Parameters for the `tasks.send` method to add messages to existing tasks.

#### Schema Structure
```yaml
TasksSendParams:
  type: object
  required: [taskId, message]
  properties:
    taskId:
      type: string
    message:
      $ref: '#/components/schemas/Message'
```

#### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `taskId` | ✅ | `string` | Target task identifier |
| `message` | ✅ | `Message` | New message to add to conversation |

#### Usage Examples

**Providing Additional Context:**
```json
{
  "method": "tasks.send",
  "params": {
    "taskId": "task-analysis-abc123",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "TextPart",
          "content": "Please also include regional breakdown in your analysis. Focus particularly on the West Coast market performance."
        }
      ],
      "timestamp": "2024-01-15T10:30:00Z"
    }
  },
  "id": "req-send-context-001"
}
```

**Responding to Agent Question:**
```json
{
  "method": "tasks.send",
  "params": {
    "taskId": "task-report-def456",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "TextPart",
          "content": "For the monthly report:\n1. Include Sales, Marketing, and Customer Success departments\n2. Focus on conversion rates, CAC, and customer satisfaction scores\n3. Yes, include year-over-year comparisons\n4. Please create a PowerPoint presentation\n5. Highlight our Q4 customer acquisition goal achievement"
        }
      ],
      "timestamp": "2024-01-15T14:45:00Z"
    }
  },
  "id": "req-send-clarification-001"
}
```

**Adding Supporting Files:**
```json
{
  "method": "tasks.send",
  "params": {
    "taskId": "task-analysis-abc123",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "TextPart",
          "content": "I found additional data that might be relevant to your analysis."
        },
        {
          "type": "FilePart",
          "content": "...",
          "mimeType": "application/vnd.ms-excel",
          "filename": "supplementary_data.xlsx",
          "size": 524288,
          "encoding": "base64"
        }
      ],
      "timestamp": "2024-01-15T11:00:00Z"
    }
  },
  "id": "req-send-files-001"
}
```

---

### TasksGetParams Schema

Parameters for the `tasks.get` method to retrieve task information and status.

#### Schema Structure
```yaml
TasksGetParams:
  type: object
  required: [taskId]
  properties:
    taskId:
      type: string
    includeMessages:
      type: boolean
      default: true
    includeArtifacts:
      type: boolean  
      default: true
```

#### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `taskId` | ✅ | `string` | Task identifier to retrieve |
| `includeMessages` | ❌ | `boolean` | Include conversation history (default: true) |
| `includeArtifacts` | ❌ | `boolean` | Include generated artifacts (default: true) |

#### Usage Examples

**Full Task Retrieval:**
```json
{
  "method": "tasks.get",
  "params": {
    "taskId": "task-analysis-abc123"
  },
  "id": "req-get-full-001"
}
```

**Status Check Only:**
```json
{
  "method": "tasks.get",
  "params": {
    "taskId": "task-analysis-abc123",
    "includeMessages": false,
    "includeArtifacts": false
  },
  "id": "req-get-status-001"
}
```

**Response Example:**
```json
{
  "jsonrpc": "2.0",
  "id": "req-get-full-001",
  "result": {
    "type": "task",
    "task": {
      "taskId": "task-analysis-abc123",
      "status": "COMPLETED",
      "createdAt": "2024-01-15T10:00:00Z",
      "updatedAt": "2024-01-15T12:30:00Z",
      "assignedAgent": "agent-data-analyst-001",
      "messages": [...],
      "artifacts": [...],
      "metadata": {...}
    }
  }
}
```

---

### TasksCancelParams Schema

Parameters for the `tasks.cancel` method to terminate task processing.

#### Schema Structure
```yaml
TasksCancelParams:
  type: object
  required: [taskId]
  properties:
    taskId:
      type: string
    reason:
      type: string
      description: Reason for cancellation
```

#### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `taskId` | ✅ | `string` | Task identifier to cancel |
| `reason` | ❌ | `string` | Human-readable cancellation reason |

#### Usage Examples

**Basic Cancellation:**
```json
{
  "method": "tasks.cancel",
  "params": {
    "taskId": "task-analysis-abc123"
  },
  "id": "req-cancel-001"
}
```

**Cancellation with Reason:**
```json
{
  "method": "tasks.cancel",
  "params": {
    "taskId": "task-analysis-abc123",
    "reason": "Requirements changed - analysis no longer needed"
  },
  "id": "req-cancel-with-reason-001"
}
```

#### Cancellation Behavior

- **SUBMITTED/WORKING**: Task immediately moves to CANCELED state
- **INPUT_REQUIRED**: Task cancellation confirmed, no further processing
- **COMPLETED/FAILED**: Cannot cancel terminal states (returns error)
- **Already CANCELED**: Idempotent operation (no error)

---

### TasksSubscribeParams Schema

Parameters for the `tasks.subscribe` method to set up webhook notifications for task events.

#### Schema Structure
```yaml
TasksSubscribeParams:
  type: object
  required: [taskId, callbackUrl]
  properties:
    taskId:
      type: string
    callbackUrl:
      type: string
      format: uri
      description: Webhook URL for task notifications
    events:
      type: array
      items:
        type: string
        enum: [STATUS_CHANGE, NEW_MESSAGE, NEW_ARTIFACT, COMPLETED, FAILED]
      default: [STATUS_CHANGE, COMPLETED, FAILED]
```

#### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `taskId` | ✅ | `string` | Task to subscribe to |
| `callbackUrl` | ✅ | `uri` | Webhook endpoint URL |
| `events` | ❌ | `string[]` | Events to receive notifications for |

#### Event Types

- **STATUS_CHANGE**: Task moved between lifecycle states
- **NEW_MESSAGE**: Agent or user added message to task
- **NEW_ARTIFACT**: Agent generated new deliverable
- **COMPLETED**: Task finished successfully (includes STATUS_CHANGE)
- **FAILED**: Task failed with error (includes STATUS_CHANGE)

#### Usage Examples

**Default Subscription:**
```json
{
  "method": "tasks.subscribe",
  "params": {
    "taskId": "task-analysis-abc123",
    "callbackUrl": "https://myapp.example.com/webhooks/tasks"
  },
  "id": "req-subscribe-001"
}
```

**Custom Event Subscription:**
```json
{
  "method": "tasks.subscribe",
  "params": {
    "taskId": "task-analysis-abc123",
    "callbackUrl": "https://myapp.example.com/webhooks/tasks",
    "events": ["NEW_MESSAGE", "NEW_ARTIFACT", "COMPLETED", "FAILED"]
  },
  "id": "req-subscribe-custom-001"
}
```

#### Webhook Requirements

Your webhook endpoint must:
- Accept POST requests
- Return HTTP 200-299 status codes for successful receipt
- Handle JSON payload with `TaskNotificationParams` structure
- Implement authentication/security as needed
- Handle duplicate notifications gracefully (idempotent processing)

---

### TaskNotificationParams Schema

Parameters for the `task.notification` method - the webhook payload sent to subscribed endpoints.

#### Schema Structure
```yaml
TaskNotificationParams:
  type: object
  required: [taskId, event, timestamp]
  properties:
    taskId:
      type: string
    event:
      type: string
      enum: [STATUS_CHANGE, NEW_MESSAGE, NEW_ARTIFACT, COMPLETED, FAILED]
    timestamp:
      type: string
      format: date-time
    data:
      oneOf:
        - $ref: '#/components/schemas/TaskObject'
        - $ref: '#/components/schemas/Message'
        - $ref: '#/components/schemas/Artifact'
```

#### Field Reference

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `taskId` | ✅ | `string` | Task that triggered the notification |
| `event` | ✅ | `enum` | Type of event that occurred |
| `timestamp` | ✅ | `datetime` | When the event occurred |
| `data` | ✅ | `object` | Relevant data based on event type |

#### Data Content by Event Type

| Event | Data Type | Content |
|-------|-----------|---------|
| `STATUS_CHANGE` | `TaskObject` | Complete updated task |
| `NEW_MESSAGE` | `Message` | New message that was added |
| `NEW_ARTIFACT` | `Artifact` | New artifact that was generated |
| `COMPLETED` | `TaskObject` | Final task state with all results |
| `FAILED` | `TaskObject` | Task state with error information |

#### Notification Examples

**Task Completion Notification:**
```json
{
  "taskId": "task-analysis-abc123",
  "event": "COMPLETED",
  "timestamp": "2024-01-15T12:30:00Z",
  "data": {
    "taskId": "task-analysis-abc123",
    "status": "COMPLETED",
    "createdAt": "2024-01-15T10:00:00Z",
    "updatedAt": "2024-01-15T12:30:00Z",
    "assignedAgent": "agent-data-analyst-001",
    "messages": [...],
    "artifacts": [
      {
        "artifactId": "analysis-report-001",
        "name": "Sales Analysis Report",
        "description": "Q4 sales performance analysis with insights",
        "parts": [...],
        "createdAt": "2024-01-15T12:30:00Z",
        "createdBy": "agent-data-analyst-001"
      }
    ],
    "metadata": {...}
  }
}
```

**New Message Notification:**
```json
{
  "taskId": "task-analysis-abc123",
  "event": "NEW_MESSAGE",
  "timestamp": "2024-01-15T11:15:00Z",
  "data": {
    "role": "agent",
    "parts": [
      {
        "type": "TextPart",
        "content": "I've completed the initial data processing. The dataset contains 15,000 customer records. Starting trend analysis now."
      }
    ],
    "timestamp": "2024-01-15T11:15:00Z",
    "agentId": "agent-data-analyst-001"
  }
}
```

**New Artifact Notification:**
```json
{
  "taskId": "task-analysis-abc123",
  "event": "NEW_ARTIFACT",
  "timestamp": "2024-01-15T11:45:00Z",
  "data": {
    "artifactId": "intermediate-viz-001",
    "name": "Preliminary Data Visualization",
    "description": "Initial charts showing data distribution and key trends",
    "parts": [
      {
        "type": "ImagePart",
        "content": "...",
        "mimeType": "image/png",
        "filename": "data_distribution.png",
        "size": 234567,
        "encoding": "base64"
      }
    ],
    "createdAt": "2024-01-15T11:45:00Z",
    "createdBy": "agent-data-analyst-001",
    "version": "1.0"
  }
}
```

---

## Task Operations

### Complete Task Flow

#### 1. Task Creation
```javascript
// Client creates a new task
const createResponse = await fetch('/jsonrpc', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + accessToken
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tasks.create',
    params: {
      initialMessage: {
        role: 'user',
        parts: [
          {
            type: 'TextPart',
            content: 'Analyze customer satisfaction survey results'
          }
        ],
        timestamp: new Date().toISOString()
      },
      priority: 'HIGH',
      metadata: {
        deadline: '2024-01-16T17:00:00Z',
        category: 'customer_analytics'
      }
    },
    id: 'req-create-' + Date.now()
  })
});

const task = await createResponse.json();
const taskId = task.result.task.taskId;
```

#### 2. Subscription Setup
```javascript
// Subscribe to task notifications
await fetch('/jsonrpc', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + accessToken
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tasks.subscribe',
    params: {
      taskId: taskId,
      callbackUrl: 'https://myapp.example.com/webhooks/tasks',
      events: ['STATUS_CHANGE', 'NEW_ARTIFACT', 'COMPLETED', 'FAILED']
    },
    id: 'req-subscribe-' + Date.now()
  })
});
```

#### 3. Webhook Handler
```javascript
// Express.js webhook endpoint
app.post('/webhooks/tasks', (req, res) => {
  const notification = req.body;
  
  switch (notification.event) {
    case 'STATUS_CHANGE':
      console.log(`Task ${notification.taskId} status: ${notification.data.status}`);
      updateTaskStatus(notification.taskId, notification.data.status);
      break;
      
    case 'NEW_ARTIFACT':
      console.log(`New artifact: ${notification.data.name}`);
      processArtifact(notification.taskId, notification.data);
      break;
      
    case 'COMPLETED':
      console.log(`Task ${notification.taskId} completed`);
      handleTaskCompletion(notification.data);
      break;
      
    case 'FAILED':
      console.log(`Task ${notification.taskId} failed`);
      handleTaskFailure(notification.data);
      break;
  }
  
  res.status(200).send('OK');
});
```

#### 4. Status Monitoring
```javascript
// Periodic status check (if webhooks unavailable)
const checkTaskStatus = async (taskId) => {
  const response = await fetch('/jsonrpc', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + accessToken
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'tasks.get',
      params: {
        taskId: taskId,
        includeMessages: false,
        includeArtifacts: false
      },
      id: 'req-status-' + Date.now()
    })
  });
  
  const result = await response.json();
  return result.result.task.status;
};

// Poll every 30 seconds until completion
const pollTask = async (taskId) => {
  const interval = setInterval(async () => {
    const status = await checkTaskStatus(taskId);
    
    if (['COMPLETED', 'FAILED', 'CANCELED'].includes(status)) {
      clearInterval(interval);
      console.log(`Task ${taskId} finished with status: ${status}`);
    }
  }, 30000);
};
```

### Task Interaction Patterns

#### Request-Response Pattern
```javascript
// Fire-and-forget task creation
const taskId = await createTask(params);
// ... continue with other work ...
// Check results later via webhook or polling
```

#### Interactive Pattern
```javascript
// Create task
const taskId = await createTask(params);

// Subscribe to notifications
await subscribeToTask(taskId);

// Wait for INPUT_REQUIRED status
webhook.on('STATUS_CHANGE', (notification) => {
  if (notification.data.status === 'INPUT_REQUIRED') {
    // Send additional information
    sendTaskMessage(taskId, clarificationMessage);
  }
});
```

#### Batch Processing Pattern
```javascript
// Create multiple related tasks
const taskIds = await Promise.all([
  createTask(analysisParams1),
  createTask(analysisParams2),
  createTask(analysisParams3)
]);

// Monitor all tasks collectively
taskIds.forEach(taskId => subscribeToTask(taskId));

// Coordinate results when all complete
let completedCount = 0;
webhook.on('COMPLETED', (notification) => {
  completedCount++;
  if (completedCount === taskIds.length) {
    // All tasks complete - process combined results
    consolidateResults(taskIds);
  }
});
```

---

## Notification System

### Webhook Architecture

```
┌─────────────────┐    Task Events     ┌─────────────────┐
│   ACP Server     │ ──────────────────▶ │  Your Webhook   │
│                 │                     │   Endpoint      │
│ - Task Processing│                     │                 │
│ - Event Generation│                    │ - Event Handler │
│ - Webhook Delivery│                    │ - Business Logic│
└─────────────────┘                     └─────────────────┘
```

### Webhook Security

#### 1. Signature Verification
```javascript
const crypto = require('crypto');

const verifyWebhookSignature = (payload, signature, secret) => {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
    
  return crypto.timingSafeEqual(
    Buffer.from(signature, 'hex'),
    Buffer.from(expectedSignature, 'hex')
  );
};

app.post('/webhooks/tasks', (req, res) => {
  const signature = req.headers['x-acp-signature'];
  const payload = JSON.stringify(req.body);
  
  if (!verifyWebhookSignature(payload, signature, WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid signature');
  }
  
  // Process webhook...
});
```

#### 2. Idempotency Handling
```javascript
const processedNotifications = new Set();

app.post('/webhooks/tasks', (req, res) => {
  const notification = req.body;
  const notificationId = `${notification.taskId}-${notification.event}-${notification.timestamp}`;
  
  if (processedNotifications.has(notificationId)) {
    // Already processed - return success
    return res.status(200).send('Already processed');
  }
  
  try {
    processNotification(notification);
    processedNotifications.add(notificationId);
    res.status(200).send('OK');
  } catch (error) {
    console.error('Webhook processing failed:', error);
    res.status(500).send('Processing failed');
  }
});
```

#### 3. Retry Logic
```javascript
const handleWebhookFailure = async (notification, attempt = 1) => {
  const maxAttempts = 5;
  const backoffMs = Math.pow(2, attempt) * 1000; // Exponential backoff
  
  if (attempt > maxAttempts) {
    console.error(`Webhook delivery failed after ${maxAttempts} attempts`);
    // Store in dead letter queue or alert operations
    return;
  }
  
  try {
    await deliverWebhook(notification);
  } catch (error) {
    console.log(`Webhook delivery attempt ${attempt} failed, retrying in ${backoffMs}ms`);
    setTimeout(() => {
      handleWebhookFailure(notification, attempt + 1);
    }, backoffMs);
  }
};
```

### Event Filtering

#### Subscription Management
```javascript
class TaskSubscriptionManager {
  constructor() {
    this.subscriptions = new Map();
  }
  
  subscribe(taskId, callbackUrl, events = ['STATUS_CHANGE', 'COMPLETED', 'FAILED']) {
    this.subscriptions.set(taskId, {
      callbackUrl,
      events,
      createdAt: new Date(),
      active: true
    });
  }
  
  shouldNotify(taskId, event) {
    const subscription = this.subscriptions.get(taskId);
    return subscription && subscription.active && subscription.events.includes(event);
  }
  
  unsubscribe(taskId) {
    this.subscriptions.delete(taskId);
  }
}
```

---

## Best Practices

### Task Design

#### 1. Granular Task Scope
```javascript
// Good: Single responsibility tasks
const tasks = [
  createTask({ type: 'data_validation', dataset: 'customers.csv' }),
  createTask({ type: 'churn_analysis', dataset: 'validated_customers.csv' }),
  createTask({ type: 'report_generation', analysis: 'churn_results.json' })
];

// Avoid: Monolithic tasks
const task = createTask({
  type: 'complete_customer_analysis', // Too broad
  steps: ['validate', 'analyze', 'report', 'email', 'archive']
});
```

#### 2. Clear Requirements
```javascript
// Good: Specific, actionable requirements
const analysisTask = {
  initialMessage: {
    role: 'user',
    parts: [
      {
        type: 'TextPart',
        content: `Analyze Q4 customer churn data with the following requirements:
        
        1. Calculate monthly churn rates for Oct, Nov, Dec
        2. Identify top 3 churn risk factors
        3. Segment customers by tenure (<6mo, 6-24mo, >24mo)
        4. Provide actionable retention recommendations
        5. Generate executive summary (max 1 page)
        
        Output: PDF report + CSV data + PowerPoint summary`
      }
    ]
  },
  metadata: {
    outputFormats: ['pdf', 'csv', 'pptx'],
    analysisDepth: 'detailed',
    audience: 'executive'
  }
};

// Avoid: Vague requirements
const vaguTask = {
  initialMessage: {
    role: 'user',
    parts: [
      {
        type: 'TextPart',
        content: 'Look at the customer data and tell me something interesting'
      }
    ]
  }
};
```

#### 3. Metadata Usage
```javascript
// Comprehensive metadata for task management
const taskMetadata = {
  // Business context
  priority: 'HIGH',
  deadline: '2024-01-16T17:00:00Z',
  stakeholder: 'executive_team',
  
  // Processing hints
  estimatedDuration: '2-3 hours',
  resourceRequirements: ['gpu', 'large_memory'],
  
  // Categorization
  category: 'analytics',
  subcategory: 'customer_insights',
  tags: ['churn', 'retention', 'q4', 'executive'],
  
  // Custom business logic
  approvalRequired: false,
  confidentialityLevel: 'internal',
  costCenter: 'marketing',
  
  // Technical parameters
  outputFormats: ['pdf', 'csv'],
  dataRetentionDays: 90,
  cacheResults: true
};
```

### Error Handling

#### 1. Graceful Degradation
```javascript
const handleTaskFailure = (taskNotification) => {
  const task = taskNotification.data;
  
  // Extract error information from messages
  const errorMessages = task.messages.filter(msg => 
    msg.role === 'system' && msg.parts.some(part => 
      part.content.includes('error') || part.content.includes('failed')
    )
  );
  
  // Determine if retry is appropriate
  const isRetryable = task.metadata?.retryable !== false;
  const errorType = task.metadata?.errorCode;
  
  switch (errorType) {
    case 'DATA_VALIDATION_FAILED':
      // User action required - notify and provide guidance
      notifyUser(`Task failed due to data issues. Please review and resubmit with corrected data.`);
      break;
      
    case 'AGENT_UNAVAILABLE':
      if (isRetryable) {
        // Temporary issue - retry with delay
        setTimeout(() => retryTask(task), 5 * 60 * 1000); // 5 minutes
      }
      break;
      
    case 'RESOURCE_LIMIT_EXCEEDED':
      // Try with lower priority or different agent
      retryTaskWithFallback(task);
      break;
      
    default:
      // Log for investigation
      logTaskFailure(task);
      notifyUser('Task failed due to unexpected error. Support has been notified.');
  }
};
```

#### 2. Input Validation
```javascript
const validateTaskCreation = (params) => {
  const errors = [];
  
  // Validate initial message
  if (!params.initialMessage) {
    errors.push('initialMessage is required');
  } else {
    if (!params.initialMessage.role || !['user', 'agent', 'system'].includes(params.initialMessage.role)) {
      errors.push('initialMessage.role must be user, agent, or system');
    }
    
    if (!params.initialMessage.parts || params.initialMessage.parts.length === 0) {
      errors.push('initialMessage.parts must contain at least one part');
    }
  }
  
  // Validate priority
  if (params.priority && !['LOW', 'NORMAL', 'HIGH', 'URGENT'].includes(params.priority)) {
    errors.push('priority must be LOW, NORMAL, HIGH, or URGENT');
  }
  
  // Validate agent assignment
  if (params.assignTo && typeof params.assignTo !== 'string') {
    errors.push('assignTo must be a string');
  }
  
  if (errors.length > 0) {
    throw new ValidationError('Task creation validation failed', errors);
  }
};
```

### Performance Optimization

#### 1. Efficient Status Polling
```javascript
class TaskPoller {
  constructor() {
    this.pollIntervals = new Map();
  }
  
  startPolling(taskId, callback, options = {}) {
    const {
      initialInterval = 5000,    // Start with 5 seconds
      maxInterval = 60000,       // Max 1 minute
      backoffMultiplier = 1.5    // Increase interval by 50% each time
    } = options;
    
    let currentInterval = initialInterval;
    
    const poll = async () => {
      try {
        const status = await this.getTaskStatus(taskId);
        
        if (['COMPLETED', 'FAILED', 'CANCELED'].includes(status)) {
          this.stopPolling(taskId);
          callback({ taskId, status, completed: true });
          return;
        }
        
        callback({ taskId, status, completed: false });
        
        // Increase polling interval (exponential backoff)
        currentInterval = Math.min(currentInterval * backoffMultiplier, maxInterval);
        
        const timeoutId = setTimeout(poll, currentInterval);
        this.pollIntervals.set(taskId, timeoutId);
        
      } catch (error) {
        console.error(`Polling failed for task ${taskId}:`, error);
        callback({ taskId, error, completed: false });
      }
    };
    
    poll();
  }
  
  stopPolling(taskId) {
    const timeoutId = this.pollIntervals.get(taskId);
    if (timeoutId) {
      clearTimeout(timeoutId);
      this.pollIntervals.delete(taskId);
    }
  }
}
```

#### 2. Batch Operations
```javascript
// Batch task status checks
const batchGetTaskStatus = async (taskIds) => {
  const batchRequest = {
    jsonrpc: '2.0',
    method: 'tasks.getBatch',
    params: {
      taskIds: taskIds,
      includeMessages: false,
      includeArtifacts: false
    },
    id: 'batch-status-' + Date.now()
  };
  
  const response = await fetch('/jsonrpc', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + accessToken
    },
    body: JSON.stringify(batchRequest)
  });
  
  return response.json();
};

// Use batch operations for efficiency
const monitorMultipleTasks = async (taskIds) => {
  const statusMap = {};
  
  const checkAllStatuses = async () => {
    const results = await batchGetTaskStatus(taskIds);
    
    results.forEach(task => {
      statusMap[task.taskId] = task.status;
    });
    
    const pendingTasks = taskIds.filter(id => 
      !['COMPLETED', 'FAILED', 'CANCELED'].includes(statusMap[id])
    );
    
    if (pendingTasks.length > 0) {
      setTimeout(checkAllStatuses, 30000); // Check again in 30 seconds
    }
  };
  
  checkAllStatuses();
};
```

### Security Considerations

#### 1. Access Control
```javascript
const validateTaskAccess = (taskId, userId, operation) => {
  const task = getTask(taskId);
  
  // Check if user has permission for this operation
  const permissions = getUserPermissions(userId);
  
  switch (operation) {
    case 'read':
      return permissions.canRead(task) || task.createdBy === userId;
      
    case 'update':
      return permissions.canUpdate(task) || task.createdBy === userId;
      
    case 'cancel':
      return permissions.canCancel(task) || task.createdBy === userId;
      
    case 'subscribe':
      return permissions.canSubscribe(task) || task.createdBy === userId;
      
    default:
      return false;
  }
};
```

#### 2. Sensitive Data Handling
```javascript
const sanitizeTaskForUser = (task, userId) => {
  // Remove sensitive information based on user permissions
  const sanitized = { ...task };
  
  if (!hasAdminAccess(userId)) {
    // Remove internal processing details
    delete sanitized.metadata.internalProcessingNotes;
    delete sanitized.metadata.agentPerformanceMetrics;
    
    // Filter messages to exclude system debugging info
    sanitized.messages = sanitized.messages.filter(msg => 
      msg.role !== 'system' || !msg.parts.some(part => 
        part.content.includes('DEBUG') || part.content.includes('INTERNAL')
      )
    );
  }
  
  return sanitized;
};
```

---

## Error Handling

### Common Error Scenarios

#### 1. Task Not Found
```json
{
  "jsonrpc": "2.0",
  "id": "req-123",
  "error": {
    "code": -40001,
    "message": "Task not found",
    "data": {
      "taskId": "task-nonexistent",
      "suggestion": "Check if the taskId is correct or if the task has been deleted",
      "availableTasks": ["task-abc123", "task-def456"]
    }
  }
}
```

#### 2. Invalid Task State
```json
{
  "jsonrpc": "2.0", 
  "id": "req-124",
  "error": {
    "code": -40002,
    "message": "Task already completed",
    "data": {
      "taskId": "task-abc123",
      "currentStatus": "COMPLETED",
      "completedAt": "2024-01-15T12:30:00Z",
      "suggestion": "Cannot modify completed tasks. Create a new task if needed."
    }
  }
}
```

#### 3. Authentication Errors
```json
{
  "jsonrpc": "2.0",
  "id": "req-125", 
  "error": {
    "code": -40008,
    "message": "Insufficient OAuth2 scope",
    "data": {
      "requiredScopes": ["acp:tasks:write"],
        "providedScopes": ["acp:tasks:read"],
      "tokenUrl": "https://auth.example.com/oauth2/token"
    }
  }
}
```

### Error Recovery Patterns

#### 1. Automatic Retry with Backoff
```javascript
class TaskManager {
  async createTaskWithRetry(params, maxRetries = 3) {
    let lastError;
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await this.createTask(params);
      } catch (error) {
        lastError = error;
        
        // Don't retry on client errors
        if (error.code >= -32699 && error.code <= -32600) {
          throw error;
        }
        
        // Don't retry on business logic errors
        if (error.code >= -40099 && error.code <= -40000) {
          throw error;
        }
        
        // Exponential backoff for server errors
        const delay = Math.pow(2, attempt) * 1000;
        console.log(`Task creation attempt ${attempt} failed, retrying in ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    throw lastError;
  }
}
```

#### 2. Circuit Breaker Pattern
```javascript
class ACPCircuitBreaker {
  constructor(threshold = 5, timeout = 60000) {
    this.failureCount = 0;
    this.threshold = threshold;
    this.timeout = timeout;
    this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    this.nextAttempt = Date.now();
  }
  
  async execute(operation) {
    if (this.state === 'OPEN') {
      if (Date.now() < this.nextAttempt) {
        throw new Error('Circuit breaker is OPEN');
      }
      this.state = 'HALF_OPEN';
    }
    
    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  onSuccess() {
    this.failureCount = 0;
    this.state = 'CLOSED';
  }
  
  onFailure() {
    this.failureCount++;
    if (this.failureCount >= this.threshold) {
      this.state = 'OPEN';
      this.nextAttempt = Date.now() + this.timeout;
    }
  }
}
```

---

## Examples

### Complete Customer Analysis Workflow

This example demonstrates a comprehensive customer analysis task that showcases all Task Management schemas in action.

#### 1. Initial Task Creation
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.create",
  "params": {
    "initialMessage": {
      "role": "user",
      "parts": [
        {
          "type": "TextPart",
          "content": "I need a comprehensive analysis of our customer base to understand churn patterns and identify growth opportunities. Please analyze the attached customer data and provide actionable insights.",
          "encoding": "utf8"
        },
        {
          "type": "FilePart",
          "content": "dXNlcklkLG5hbWUsZW1haWwscGhvbmUsam9pbkRhdGUsY2h1cm5EYXRlLG1vbnRobHlTcGVuZCxzdXBwb3J0VGlja2V0cw0KMSwiSm9obiBEb2UiLCJqb2huQGV4YW1wbGUuY29tIiwiKzEtNTU1LTAxMjMiLCIyMDIzLTA1LTE1IiwiIiwxNTAuNTAsM...",
          "mimeType": "text/csv",
          "filename": "customer_data_q4_2023.csv",
          "size": 5242880,
          "encoding": "base64"
        }
      ],
      "timestamp": "2024-01-15T09:00:00Z"
    },
    "priority": "HIGH",
    "metadata": {
      "deadline": "2024-01-16T17:00:00Z",
      "category": "customer_analytics",
      "subcategory": "churn_analysis",
      "businessUnit": "marketing",
      "requestedBy": "sarah.johnson@company.com",
      "outputRequirements": {
        "formats": ["pdf", "powerpoint", "csv"],
        "audience": "executive_team",
        "maxDuration": "30_minutes_presentation"
      },
      "analysisScope": {
        "timeframe": "2023-Q4",
        "segments": ["new_customers", "existing_customers", "at_risk"],
        "metrics": ["churn_rate", "ltv", "acquisition_cost", "satisfaction"]
      }
    }
  },
  "id": "req-create-customer-analysis-001"
}
```

#### 2. Task Creation Response
```json
{
  "jsonrpc": "2.0",
  "id": "req-create-customer-analysis-001",
  "result": {
    "type": "task",
    "task": {
      "taskId": "task-customer-analysis-20240115-x7k2m9",
      "status": "SUBMITTED",
      "createdAt": "2024-01-15T09:00:00Z",
      "updatedAt": "2024-01-15T09:00:00Z",
      "messages": [
        {
          "role": "user",
          "parts": [...], // Initial message
          "timestamp": "2024-01-15T09:00:00Z"
        }
      ],
      "artifacts": [],
      "metadata": {
        "priority": "HIGH",
        "category": "customer_analytics",
        // ... other metadata
      }
    }
  }
}
```

#### 3. Subscription Setup
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.subscribe",
  "params": {
    "taskId": "task-customer-analysis-20240115-x7k2m9",
    "callbackUrl": "https://dashboard.company.com/webhooks/tasks",
    "events": ["STATUS_CHANGE", "NEW_MESSAGE", "NEW_ARTIFACT", "COMPLETED", "FAILED"]
  },
  "id": "req-subscribe-001"
}
```

#### 4. Initial Processing Notification
```json
{
  "taskId": "task-customer-analysis-20240115-x7k2m9",
  "event": "STATUS_CHANGE",
  "timestamp": "2024-01-15T09:05:00Z",
  "data": {
    "taskId": "task-customer-analysis-20240115-x7k2m9",
    "status": "WORKING",
    "assignedAgent": "agent-customer-analyst-specialist",
    "updatedAt": "2024-01-15T09:05:00Z",
    // ... rest of task object
  }
}
```

#### 5. Agent Progress Update
```json
{
  "taskId": "task-customer-analysis-20240115-x7k2m9",
  "event": "NEW_MESSAGE",
  "timestamp": "2024-01-15T09:30:00Z",
  "data": {
    "role": "agent",
    "parts": [
      {
        "type": "TextPart",
        "content": "I've successfully processed your customer dataset. Here's my initial assessment:\n\n📊 **Dataset Overview:**\n- Total records: 15,847 customers\n- Data quality score: 94.2%\n- Time period: Jan 1 - Dec 31, 2023\n\n🔍 **Initial Findings:**\n- Overall churn rate: 18.7%\n- Highest churn in first 90 days: 31.2%\n- Revenue impact: $2.3M annually\n\n⏳ **Next Steps:**\nI'm now performing detailed segmentation analysis and building predictive models. This will take approximately 45 minutes. I'll provide interim visualizations as they become available.",
        "encoding": "utf8"
      }
    ],
    "timestamp": "2024-01-15T09:30:00Z",
    "agentId": "agent-customer-analyst-specialist"
  }
}
```

#### 6. Intermediate Artifact Creation
```json
{
  "taskId": "task-customer-analysis-20240115-x7k2m9",
  "event": "NEW_ARTIFACT",
  "timestamp": "2024-01-15T10:15:00Z",
  "data": {
    "artifactId": "customer-segmentation-viz-001",
    "name": "Customer Segmentation Visualization",
    "description": "Interactive charts showing customer segments by behavior, tenure, and value",
    "parts": [
      {
        "type": "ImagePart",
        "content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "mimeType": "image/png",
        "filename": "customer_segments_overview.png",
        "size": 567890,
        "encoding": "base64",
        "width": 1200,
        "height": 800,
        "alt": "Customer segmentation chart showing 5 distinct segments based on behavior and value"
      },
      {
        "type": "DataPart",
        "content": {
          "segments": [
            {
              "name": "Champions",
              "size": 1847,
              "characteristics": ["high_value", "high_engagement", "long_tenure"],
              "churn_risk": 0.05,
              "avg_ltv": 2850.50
            },
            {
              "name": "At Risk",
              "size": 2341,
              "characteristics": ["declining_engagement", "support_tickets", "price_sensitive"],
              "churn_risk": 0.68,
              "avg_ltv": 890.25
            }
          ],
          "visualization_config": {
            "chart_type": "scatter_plot",
            "x_axis": "customer_value",
            "y_axis": "engagement_score",
            "color_by": "segment",
            "interactive": true
          }
        },
        "mimeType": "application/json",
        "encoding": "utf8"
      }
    ],
    "createdAt": "2024-01-15T10:15:00Z",
    "createdBy": "agent-customer-analyst-specialist",
    "version": "1.0",
    "metadata": {
      "artifact_type": "visualization",
      "analysis_stage": "segmentation",
      "confidence_score": 0.91,
      "data_points": 15847
    }
  }
}
```

#### 7. Clarification Request
```json
{
  "taskId": "task-customer-analysis-20240115-x7k2m9",
  "event": "STATUS_CHANGE",
  "timestamp": "2024-01-15T10:45:00Z",
  "data": {
    "taskId": "task-customer-analysis-20240115-x7k2m9",
    "status": "INPUT_REQUIRED",
    "updatedAt": "2024-01-15T10:45:00Z",
    "messages": [
      // ... previous messages
      {
        "role": "agent",
        "parts": [
          {
            "type": "TextPart",
            "content": "I've identified several high-impact insights and am ready to build predictive models. To ensure the analysis meets your specific needs, I need clarification on a few points:\n\n❓ **Questions:**\n\n1. **Intervention Budget**: What's your available budget for customer retention initiatives? This will help me prioritize recommendations.\n\n2. **Segment Focus**: Which customer segments are most strategically important to your business right now?\n\n3. **Prediction Timeframe**: How far into the future should the churn predictions extend? (30, 60, 90 days?)\n\n4. **Action Capability**: What retention tools do you currently have available? (email campaigns, phone outreach, discount programs, etc.)\n\n5. **Success Metrics**: How do you currently measure retention success?\n\nThese details will help me tailor the recommendations and predictive models to be immediately actionable for your team.",
            "encoding": "utf8"
          }
        ],
        "timestamp": "2024-01-15T10:45:00Z",
        "agentId": "agent-customer-analyst-specialist"
      }
    ]
  }
}
```

#### 8. User Response
```json
{
  "jsonrpc": "2.0",
  "method": "tasks.send",
  "params": {
    "taskId": "task-customer-analysis-20240115-x7k2m9",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "TextPart",
          "content": "Thanks for the detailed analysis so far! Here are the answers to your questions:\n\n1. **Budget**: $50,000 quarterly for retention initiatives\n2. **Segment Focus**: Prioritize 'At Risk' high-value customers first, then 'Champions' retention\n3. **Prediction Timeframe**: 60-day churn probability predictions\n4. **Available Tools**: Email campaigns, phone outreach, 10% discount program, premium support escalation\n5. **Success Metrics**: Month-over-month churn reduction, customer lifetime value improvement\n\nPlease proceed with the predictive modeling and provide specific action plans for each segment.",
          "encoding": "utf8"
        }
      ],
      "timestamp": "2024-01-15T11:00:00Z"
    }
  },
  "id": "req-send-clarification-001"
}
```

#### 9. Final Completion
```json
{
  "taskId": "task-customer-analysis-20240115-x7k2m9",
  "event": "COMPLETED",
  "timestamp": "2024-01-15T12:30:00Z",
  "data": {
    "taskId": "task-customer-analysis-20240115-x7k2m9",
    "status": "COMPLETED",
    "createdAt": "2024-01-15T09:00:00Z",
    "updatedAt": "2024-01-15T12:30:00Z",
    "assignedAgent": "agent-customer-analyst-specialist",
    "messages": [
      // ... all previous messages
      {
        "role": "agent",
        "parts": [
          {
            "type": "TextPart",
            "content": "🎯 **Customer Analysis Complete!**\n\nI've completed your comprehensive customer analysis with predictive modeling and actionable recommendations. The analysis reveals significant opportunities for retention improvement and revenue growth.\n\n📈 **Key Outcomes:**\n- Identified 2,341 at-risk customers (potential $2.1M revenue impact)\n- Built 87% accurate churn prediction model\n- Developed targeted intervention strategies for each segment\n- ROI projection: 3.2x return on $50K investment\n\n📦 **Deliverables Created:**\n1. Executive Summary Report (PDF)\n2. Interactive Analytics Dashboard (PowerPoint)\n3. Customer Segmentation Data (CSV)\n4. Predictive Model Results (CSV)\n5. Action Plan Template (PDF)\n\nAll artifacts include detailed implementation guidance and expected impact metrics. The recommendations are prioritized by ROI and feasibility within your budget constraints.",
            "encoding": "utf8"
          }
        ],
        "timestamp": "2024-01-15T12:30:00Z",
        "agentId": "agent-customer-analyst-specialist"
      }
    ],
    "artifacts": [
      {
        "artifactId": "customer-analysis-executive-report",
        "name": "Customer Analysis Executive Report",
        "description": "Comprehensive 15-page executive report with analysis findings, predictions, and strategic recommendations",
        "parts": [
          {
            "type": "FilePart",
            "content": "JVBERi0xLjQKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZw0KL1BhZ2VzIDIgMCBSDQo+Pg0K...",
            "mimeType": "application/pdf",
            "filename": "Customer_Analysis_Executive_Report.pdf",
            "size": 3145728,
            "encoding": "base64"
          }
        ],
        "createdAt": "2024-01-15T12:30:00Z",
        "createdBy": "agent-customer-analyst-specialist",
        "version": "1.0"
      },
      {
        "artifactId": "interactive-dashboard-presentation",
        "name": "Interactive Customer Analytics Dashboard",
        "description": "PowerPoint presentation with embedded interactive charts for executive presentation",
        "parts": [
          {
            "type": "FilePart",
            "content": "UEsDBBQABgAIAAAAIQDfpNJsWgEAACAFAAATAAgCW0NvbnRlbnRfVHlwZXNdLnhtbCCiBAI...",
            "mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "filename": "Customer_Analytics_Dashboard.pptx",
            "size": 5242880,
            "encoding": "base64"
          }
        ],
        "createdAt": "2024-01-15T12:30:00Z",
        "createdBy": "agent-customer-analyst-specialist",
        "version": "1.0"
      },
      {
        "artifactId": "predictive-model-results",
        "name": "Customer Churn Predictions",
        "description": "60-day churn probability predictions for all customers with confidence scores",
        "parts": [
          {
            "type": "FilePart",
            "content": "customer_id,churn_probability_60d,confidence_score,risk_segment,recommended_action\n1,0.87,0.92,HIGH_RISK,immediate_intervention\n2,0.23,0.78,LOW_RISK,maintain_engagement...",
            "mimeType": "text/csv",
            "filename": "churn_predictions_60day.csv",
            "size": 1048576,
            "encoding": "utf8"
          }
        ],
        "createdAt": "2024-01-15T12:30:00Z",
        "createdBy": "agent-customer-analyst-specialist",
        "version": "1.0"
      }
    ],
    "metadata": {
      "priority": "HIGH",
      "category": "customer_analytics",
      "actualDuration": "3.5_hours",
      "confidenceScore": 0.93,
      "businessImpact": "high",
      "roiProjection": 3.2,
      "implementationComplexity": "medium",
      "completionQuality": "excellent"
    }
  }
}
```

---

## Integration Patterns

### Microservices Architecture

```javascript
// Task service integration
class CustomerAnalyticsService {
  constructor(acpClient) {
    this.acpClient = acpClient;
    this.taskQueue = new Map();
  }
  
  async requestAnalysis(customerId, analysisType) {
    // Create ACP task for analysis
    const task = await this.acpClient.createTask({
      initialMessage: {
        role: 'user',
        parts: [
          {
            type: 'TextPart',
            content: `Analyze customer ${customerId} for ${analysisType}`
          }
        ]
      },
      assignTo: 'agent-customer-analyst',
      metadata: {
        customerId,
        analysisType,
        service: 'customer-analytics'
      }
    });
    
    // Track task locally
    this.taskQueue.set(task.taskId, {
      customerId,
      analysisType,
      status: 'submitted',
      createdAt: new Date()
    });
    
    return task.taskId;
  }
  
  // Webhook handler for task completion
  async handleTaskCompletion(notification) {
    const taskId = notification.taskId;
    const localTask = this.taskQueue.get(taskId);
    
    if (!localTask) return;
    
    // Extract results and update local systems
    const task = notification.data;
    const results = this.extractAnalysisResults(task.artifacts);
    
    // Update customer record
    await this.updateCustomerAnalysis(localTask.customerId, results);
    
    // Trigger downstream processes
    await this.triggerActionPlans(localTask.customerId, results);
    
    // Clean up
    this.taskQueue.delete(taskId);
  }
}
```

### Event-Driven Architecture

```javascript
// Event bus integration
class ACPEventBridge {
  constructor(eventBus, acpClient) {
    this.eventBus = eventBus;
    this.acpClient = acpClient;
    this.setupEventHandlers();
  }
  
  setupEventHandlers() {
    // Listen for business events that should trigger ACP tasks
    this.eventBus.on('customer.churned', this.handleCustomerChurn.bind(this));
    this.eventBus.on('data.uploaded', this.handleDataUpload.bind(this));
    this.eventBus.on('report.requested', this.handleReportRequest.bind(this));
  }
  
  async handleCustomerChurn(event) {
    // Automatically analyze churn pattern
    await this.acpClient.createTask({
      initialMessage: {
        role: 'system',
        parts: [
          {
            type: 'TextPart',
            content: `Customer ${event.customerId} has churned. Analyze churn pattern and identify similar at-risk customers.`
          },
          {
            type: 'DataPart',
            content: event.customerData,
            mimeType: 'application/json'
          }
        ]
      },
      assignTo: 'agent-churn-analyst',
      priority: 'HIGH'
    });
  }
  
  async handleDataUpload(event) {
    // Process uploaded data automatically
    if (event.fileType === 'customer_data') {
      await this.acpClient.createTask({
        initialMessage: {
          role: 'system',
          parts: [
            {
              type: 'TextPart',
              content: 'New customer data uploaded. Please validate, clean, and perform quality assessment.'
            },
            {
              type: 'FilePart',
              content: event.fileContent,
              mimeType: event.mimeType,
              filename: event.filename
            }
          ]
        },
        assignTo: 'agent-data-processor',
        metadata: {
          uploadId: event.uploadId,
          autoProcess: true
        }
      });
    }
  }
}
```

### Workflow Orchestration

```javascript
// Complex multi-step workflow using tasks
class CustomerOnboardingWorkflow {
  constructor(acpClient) {
    this.acpClient = acpClient;
    this.workflows = new Map();
  }
  
  async startOnboarding(customerId, customerData) {
    const workflowId = `onboarding-${customerId}-${Date.now()}`;
    
    const workflow = {
      id: workflowId,
      customerId,
      steps: [
        'data_validation',
        'risk_assessment',
        'personalization',
        'welcome_package'
      ],
      currentStep: 0,
      tasks: [],
      results: {}
    };
    
    this.workflows.set(workflowId, workflow);
    
    // Start first step
    await this.executeNextStep(workflowId, customerData);
    
    return workflowId;
  }
  
  async executeNextStep(workflowId, input) {
    const workflow = this.workflows.get(workflowId);
    const stepName = workflow.steps[workflow.currentStep];
    
    let taskParams;
    
    switch (stepName) {
      case 'data_validation':
        taskParams = {
          initialMessage: {
            role: 'system',
            parts: [
              {
                type: 'TextPart',
                content: 'Validate customer data quality and completeness'
              },
              {
                type: 'DataPart',
                content: input,
                mimeType: 'application/json'
              }
            ]
          },
          assignTo: 'agent-data-validator'
        };
        break;
        
      case 'risk_assessment':
        taskParams = {
          initialMessage: {
            role: 'system',
            parts: [
              {
                type: 'TextPart',
                content: 'Assess customer risk profile for onboarding'
              },
              {
                type: 'DataPart',
                content: workflow.results.data_validation,
                mimeType: 'application/json'
              }
            ]
          },
          assignTo: 'agent-risk-assessor'
        };
        break;
        
      // ... other steps
    }
    
    const task = await this.acpClient.createTask(taskParams);
    workflow.tasks.push(task.taskId);
    
    // Subscribe to completion
    await this.acpClient.subscribeToTask(task.taskId, {
      callbackUrl: 'https://workflow.service.com/webhooks/tasks'
    });
  }
  
  async handleTaskCompletion(notification) {
    const taskId = notification.taskId;
    
    // Find workflow containing this task
    const workflow = Array.from(this.workflows.values())
      .find(w => w.tasks.includes(taskId));
    
    if (!workflow) return;
    
    const stepName = workflow.steps[workflow.currentStep];
    
    // Store step results
    workflow.results[stepName] = this.extractResults(notification.data);
    
    // Move to next step
    workflow.currentStep++;
    
    if (workflow.currentStep < workflow.steps.length) {
      // Continue workflow
      await this.executeNextStep(workflow.id, workflow.results[stepName]);
    } else {
      // Workflow complete
      await this.completeOnboarding(workflow);
      this.workflows.delete(workflow.id);
    }
  }
}
```

---

## Conclusion

The Task Management system provides a robust foundation for asynchronous agent-to-agent communication in the ACP protocol. The seven schemas work together to enable:

- **Complete Lifecycle Management**: From task creation through completion with clear state tracking
- **Rich Communication**: Multimodal message exchange with full conversation history
- **Deliverable Tracking**: Structured artifact management with metadata and versioning
- **Real-time Notifications**: Webhook-based event system for responsive applications
- **Flexible Operations**: Support for various interaction patterns and workflow types
- **Enterprise Features**: Priority handling, agent assignment, error recovery, and audit trails

The system is designed to handle complex, long-running tasks while maintaining clarity, reliability, and extensibility. By following the patterns and best practices outlined in this document, you can build sophisticated agent collaboration systems that scale from simple request-response operations to complex multi-step workflows.

The Task Management schemas integrate seamlessly with the Shared Communication schemas to provide a complete framework for professional agent-to-agent collaboration in enterprise environments. 