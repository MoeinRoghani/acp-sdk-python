# Response Management Documentation

## Overview

The **Response Management** schemas provide the final layer of the ACP (Agent Communication Protocol) communication framework, offering unified response formatting and comprehensive subscription management. These schemas ensure consistent client-side handling across all ACP operations while enabling robust webhook-based notification systems.

### Core Components

1. **MethodResult** - Unified response wrapper for all successful ACP method calls
2. **SubscriptionObject** - Webhook subscription management for task notifications

### Design Philosophy

The Response Management layer implements a **discriminated union pattern** for type-safe response handling and a **comprehensive subscription model** for event-driven communication, ensuring that clients can:

- Handle all ACP responses with a single, consistent pattern
- Receive real-time notifications about task lifecycle events
- Manage subscription lifecycles with full control
- Implement robust error handling and retry mechanisms

---

## Schema Definitions

### 1. MethodResult Schema

The **MethodResult** schema serves as the unified response wrapper for all successful ACP method calls, providing a consistent structure while accommodating different result types through a discriminated union pattern.

```yaml
MethodResult:
  type: object
  required: [type]
  properties:
    type:
      type: string
      enum: [task, stream, subscription, notification, success]
    task:
      $ref: '#/components/schemas/TaskObject'
    stream:  
      $ref: '#/components/schemas/StreamObject'
    subscription:
      $ref: '#/components/schemas/SubscriptionObject'
    message:
      type: string
      description: Success message for simple operations
  oneOf:
    - properties:
        type:
          enum: [task]
      required: [task]
    - properties:
        type:
          enum: [stream]
      required: [stream]
    - properties:
        type:
          enum: [subscription]
      required: [subscription]
    - properties:
        type:
          enum: [notification, success]
      required: [message]
```

#### Field Specifications

**`type`** (Required)
- **Type**: `string`
- **Values**: `task`, `stream`, `subscription`, `notification`, `success`
- **Purpose**: Discriminator field that determines which result field contains the actual data
- **Usage**: Clients use this to implement type-safe response handling

**`task`** (Conditional)
- **Type**: Reference to `TaskObject`
- **Required When**: `type === "task"`
- **Used For**: Responses from `tasks.create`, `tasks.get` methods
- **Contains**: Complete task information including status, messages, and artifacts

**`stream`** (Conditional)
- **Type**: Reference to `StreamObject`
- **Required When**: `type === "stream"`
- **Used For**: Responses from `stream.start` method
- **Contains**: Stream metadata including participants and status

**`subscription`** (Conditional)
- **Type**: Reference to `SubscriptionObject`
- **Required When**: `type === "subscription"`
- **Used For**: Responses from `tasks.subscribe` method
- **Contains**: Subscription details including webhook configuration

**`message`** (Conditional)
- **Type**: `string`
- **Required When**: `type === "notification"` or `type === "success"`
- **Used For**: Simple operation confirmations and notification acknowledgments
- **Contains**: Human-readable success message

#### Discriminated Union Logic

The `oneOf` constraint ensures exactly one result field is present based on the `type` field:

| Type | Required Field | Methods | Purpose |
|------|---------------|---------|---------|
| `task` | `task` | `tasks.create`, `tasks.get` | Return task data |
| `stream` | `stream` | `stream.start` | Return stream data |
| `subscription` | `subscription` | `tasks.subscribe` | Return subscription data |
| `notification` | `message` | Server notifications | Confirm notification delivery |
| `success` | `message` | Simple operations | Confirm operation success |

### 2. SubscriptionObject Schema

The **SubscriptionObject** schema represents a webhook subscription for task notifications, tracking all details needed to manage notification delivery throughout the subscription lifecycle.

```yaml
SubscriptionObject:
  type: object
  required: [subscriptionId, taskId, callbackUrl, events]
  properties:
    subscriptionId:
      type: string
    taskId:
      type: string
    callbackUrl:
      type: string
      format: uri
    events:
      type: array
      items:
        type: string
    createdAt:
      type: string
      format: date-time
    active:
      type: boolean
      default: true
```

#### Field Specifications

**`subscriptionId`** (Required)
- **Type**: `string`
- **Purpose**: Unique identifier for the subscription
- **Format**: Typically includes task reference for easy identification
- **Examples**: `"sub-task123-webhooks"`, `"subscription-abc-456"`
- **Usage**: Reference for subscription management operations

**`taskId`** (Required)
- **Type**: `string`
- **Purpose**: The task being monitored for events
- **Relationship**: One task can have multiple subscriptions
- **Usage**: Links subscription to specific task for event filtering

**`callbackUrl`** (Required)
- **Type**: `string` with `uri` format
- **Purpose**: Webhook endpoint URL for notification delivery
- **Requirements**: Must be accessible via HTTPS
- **Security**: Should validate SSL certificates
- **Examples**: `"https://myapp.com/webhooks/tasks"`

**`events`** (Required)
- **Type**: Array of strings
- **Purpose**: List of events to receive notifications for
- **Values**: `STATUS_CHANGE`, `NEW_MESSAGE`, `NEW_ARTIFACT`, `COMPLETED`, `FAILED`
- **Filtering**: Only subscribed events trigger webhook calls
- **Default**: Typically `["STATUS_CHANGE", "COMPLETED", "FAILED"]`

**`createdAt`** (Optional)
- **Type**: `string` with `date-time` format
- **Purpose**: Timestamp of subscription creation
- **Usage**: Audit trails, subscription lifecycle tracking
- **Format**: ISO 8601 datetime string

**`active`** (Optional, Default: true)
- **Type**: `boolean`
- **Purpose**: Whether the subscription is currently active
- **Usage**: Pause/resume notifications without deleting subscription
- **Management**: Allows temporary suspension of notifications

---

## Response Patterns

### Unified Response Handling

All successful ACP method calls return responses following this pattern:

```javascript
{
  "jsonrpc": "2.0",
  "id": "<request-id>",
  "result": {
    "type": "<result-type>",
    // Conditional fields based on type
  }
}
```

This enables clients to implement a single response handler:

```javascript
const handleACPResponse = (response) => {
  if (response.error) {
    handleError(response.error);
    return;
  }
  
  const result = response.result;
  
  switch (result.type) {
    case 'task':
      handleTaskResult(result.task);
      break;
    case 'stream':
      handleStreamResult(result.stream);
      break;
    case 'subscription':
      handleSubscriptionResult(result.subscription);
      break;
    case 'success':
    case 'notification':
      handleSimpleResult(result.message);
      break;
    default:
      console.warn(`Unknown result type: ${result.type}`);
  }
};
```

### Method-to-Result Mapping

Each ACP method maps to a specific result type:

#### Task Methods
```javascript
// tasks.create → MethodResult{type: "task"}
{
  "result": {
    "type": "task",
    "task": {
      "taskId": "task-abc123",
      "status": "SUBMITTED",
      "createdAt": "2024-01-15T10:00:00Z",
      "messages": [...],
      "artifacts": []
    }
  }
}

// tasks.get → MethodResult{type: "task"}
{
  "result": {
    "type": "task",
    "task": {
      "taskId": "task-abc123",
      "status": "COMPLETED",
      "messages": [...],
      "artifacts": [...]
    }
  }
}

// tasks.send → MethodResult{type: "success"}
{
  "result": {
    "type": "success",
    "message": "Message sent to task task-abc123"
  }
}

// tasks.cancel → MethodResult{type: "success"}
{
  "result": {
    "type": "success",
    "message": "Task task-abc123 has been successfully cancelled"
  }
}

// tasks.subscribe → MethodResult{type: "subscription"}
{
  "result": {
    "type": "subscription",
    "subscription": {
      "subscriptionId": "sub-abc123-001",
      "taskId": "task-abc123",
      "callbackUrl": "https://myapp.com/webhooks",
      "events": ["COMPLETED", "FAILED"],
      "active": true
    }
  }
}
```

#### Stream Methods
```javascript
// stream.start → MethodResult{type: "stream"}
{
  "result": {
    "type": "stream",
    "stream": {
      "streamId": "stream-collab-xyz789",
      "status": "ACTIVE",
      "participants": ["agent-analyst", "agent-expert"],
      "createdAt": "2024-01-15T14:30:00Z"
    }
  }
}

// stream.message → MethodResult{type: "success"}
{
  "result": {
    "type": "success",
    "message": "Message sent to stream stream-collab-xyz789"
  }
}

// stream.end → MethodResult{type: "success"}
{
  "result": {
    "type": "success",
    "message": "Stream stream-collab-xyz789 has been closed"
  }
}
```

#### Notification Methods
```javascript
// task.notification → MethodResult{type: "notification"}
{
  "result": {
    "type": "notification",
    "message": "Task completion notification delivered to 3 subscribers"
  }
}

// stream.chunk → MethodResult{type: "notification"}
{
  "result": {
    "type": "notification",
    "message": "Stream chunk delivered to 2 participants"
  }
}
```

---

## Subscription Management

### Subscription Lifecycle

The subscription system follows a comprehensive lifecycle:

```
Create → Active → [Pause/Resume] → Cleanup
   ↓       ↓           ↓             ↓
  POST   WebHooks   Management    DELETE
```

#### 1. Subscription Creation

```javascript
// Create subscription
const response = await acpClient.call('tasks.subscribe', {
  taskId: 'task-analysis-abc123',
  callbackUrl: 'https://myapp.com/webhooks/tasks',
  events: ['STATUS_CHANGE', 'COMPLETED', 'FAILED']
});

// Extract subscription details
const subscription = response.result.subscription;
console.log(`Created subscription: ${subscription.subscriptionId}`);

// Store for management
subscriptions.set(subscription.subscriptionId, subscription);
```

#### 2. Webhook Delivery

When subscribed events occur, the ACP server sends `TaskNotificationParams` to the webhook URL:

```javascript
// Webhook endpoint handler
app.post('/webhooks/tasks', (req, res) => {
  const notification = req.body; // TaskNotificationParams
  
  // Validate notification
  if (!notification.taskId || !notification.event) {
    return res.status(400).send('Invalid notification');
  }
  
  // Process based on event type
  switch (notification.event) {
    case 'STATUS_CHANGE':
      handleStatusChange(notification.taskId, notification.data);
      break;
    case 'NEW_MESSAGE':
      handleNewMessage(notification.taskId, notification.data);
      break;
    case 'NEW_ARTIFACT':
      handleNewArtifact(notification.taskId, notification.data);
      break;
    case 'COMPLETED':
      handleTaskCompletion(notification.taskId, notification.data);
      break;
    case 'FAILED':
      handleTaskFailure(notification.taskId, notification.data);
      break;
  }
  
  // Acknowledge receipt
  res.status(200).send('OK');
});
```

#### 3. Subscription Management

```javascript
class SubscriptionManager {
  constructor() {
    this.subscriptions = new Map();
  }
  
  async createSubscription(taskId, callbackUrl, events = ['COMPLETED', 'FAILED']) {
    const response = await acpClient.call('tasks.subscribe', {
      taskId,
      callbackUrl,
      events
    });
    
    const subscription = response.result.subscription;
    this.subscriptions.set(subscription.subscriptionId, subscription);
    
    return subscription;
  }
  
  async pauseSubscription(subscriptionId) {
    const subscription = this.subscriptions.get(subscriptionId);
    if (subscription) {
      subscription.active = false;
      // Update on server (implementation specific)
      await this.updateSubscriptionOnServer(subscription);
    }
  }
  
  async resumeSubscription(subscriptionId) {
    const subscription = this.subscriptions.get(subscriptionId);
    if (subscription) {
      subscription.active = true;
      await this.updateSubscriptionOnServer(subscription);
    }
  }
  
  getActiveSubscriptions(taskId) {
    return Array.from(this.subscriptions.values())
      .filter(sub => sub.taskId === taskId && sub.active);
  }
  
  async cleanupCompletedTasks() {
    // Remove subscriptions for completed tasks
    for (const [id, subscription] of this.subscriptions) {
      const task = await this.getTaskStatus(subscription.taskId);
      if (task.status === 'COMPLETED' || task.status === 'FAILED') {
        await this.deleteSubscription(id);
      }
    }
  }
}
```

### Event Filtering and Management

#### Event Types and Usage

```javascript
const EventTypes = {
  STATUS_CHANGE: 'STATUS_CHANGE',     // Task status transitions
  NEW_MESSAGE: 'NEW_MESSAGE',         // New message added to task
  NEW_ARTIFACT: 'NEW_ARTIFACT',       // New artifact created
  COMPLETED: 'COMPLETED',             // Task completed successfully
  FAILED: 'FAILED'                    // Task failed with error
};

// Subscription strategies
const subscriptionStrategies = {
  // Minimal monitoring - just completion
  minimal: [EventTypes.COMPLETED, EventTypes.FAILED],
  
  // Progress monitoring - status changes and completion
  progress: [EventTypes.STATUS_CHANGE, EventTypes.COMPLETED, EventTypes.FAILED],
  
  // Full monitoring - all events
  complete: Object.values(EventTypes),
  
  // Output monitoring - artifacts and completion
  output: [EventTypes.NEW_ARTIFACT, EventTypes.COMPLETED, EventTypes.FAILED],
  
  // Communication monitoring - messages and completion
  communication: [EventTypes.NEW_MESSAGE, EventTypes.COMPLETED, EventTypes.FAILED]
};
```

#### Smart Subscription Management

```javascript
class SmartSubscriptionManager extends SubscriptionManager {
  async subscribeWithStrategy(taskId, strategy = 'minimal', callbackUrl) {
    const events = subscriptionStrategies[strategy] || subscriptionStrategies.minimal;
    return this.createSubscription(taskId, callbackUrl, events);
  }
  
  async batchSubscribe(taskIds, strategy, callbackUrl) {
    const subscriptions = [];
    
    for (const taskId of taskIds) {
      try {
        const subscription = await this.subscribeWithStrategy(taskId, strategy, callbackUrl);
        subscriptions.push(subscription);
      } catch (error) {
        console.error(`Failed to subscribe to task ${taskId}:`, error);
      }
    }
    
    return subscriptions;
  }
  
  async updateSubscriptionEvents(subscriptionId, newEvents) {
    const subscription = this.subscriptions.get(subscriptionId);
    if (!subscription) {
      throw new Error(`Subscription ${subscriptionId} not found`);
    }
    
    // Update events (implementation specific)
    subscription.events = newEvents;
    await this.updateSubscriptionOnServer(subscription);
    
    return subscription;
  }
}
```

---

## Best Practices

### Response Handling

#### 1. Type-Safe Response Processing

```typescript
// TypeScript interfaces for type safety
interface MethodResult {
  type: 'task' | 'stream' | 'subscription' | 'notification' | 'success';
  task?: TaskObject;
  stream?: StreamObject;
  subscription?: SubscriptionObject;
  message?: string;
}

// Type guards for runtime validation
const isTaskResult = (result: MethodResult): result is MethodResult & { task: TaskObject } => {
  return result.type === 'task' && !!result.task;
};

const isStreamResult = (result: MethodResult): result is MethodResult & { stream: StreamObject } => {
  return result.type === 'stream' && !!result.stream;
};

// Type-safe processing
const processResult = (result: MethodResult) => {
  if (isTaskResult(result)) {
    // TypeScript knows result.task is defined
    console.log(`Task status: ${result.task.status}`);
    updateTaskUI(result.task);
  } else if (isStreamResult(result)) {
    // TypeScript knows result.stream is defined
    console.log(`Stream status: ${result.stream.status}`);
    updateStreamUI(result.stream);
  }
};
```

#### 2. Error Handling and Validation

```javascript
const validateAndProcessResponse = (response) => {
  // Validate JSON-RPC structure
  if (!response.jsonrpc || response.jsonrpc !== '2.0') {
    throw new Error('Invalid JSON-RPC response');
  }
  
  // Handle errors
  if (response.error) {
    handleACPError(response.error);
    return;
  }
  
  // Validate result structure
  if (!response.result || !response.result.type) {
    throw new Error('Invalid result structure');
  }
  
  // Validate discriminated union
  const result = response.result;
  switch (result.type) {
    case 'task':
      if (!result.task) {
        throw new Error('Task result missing task data');
      }
      break;
    case 'stream':
      if (!result.stream) {
        throw new Error('Stream result missing stream data');
      }
      break;
    case 'subscription':
      if (!result.subscription) {
        throw new Error('Subscription result missing subscription data');
      }
      break;
    case 'success':
    case 'notification':
      if (!result.message) {
        throw new Error('Message result missing message');
      }
      break;
    default:
      throw new Error(`Unknown result type: ${result.type}`);
  }
  
  // Process validated result
  handleACPResponse(response);
};
```

### Subscription Management

#### 1. Robust Webhook Handling

```javascript
// Webhook handler with comprehensive error handling
app.post('/webhooks/tasks', async (req, res) => {
  try {
    // Validate webhook signature (if implemented)
    if (!validateWebhookSignature(req)) {
      return res.status(401).send('Invalid signature');
    }
    
    const notification = req.body;
    
    // Validate notification structure
    if (!isValidTaskNotification(notification)) {
      return res.status(400).send('Invalid notification format');
    }
    
    // Check if subscription is still active
    const subscription = await getSubscriptionByTaskId(notification.taskId);
    if (!subscription || !subscription.active) {
      return res.status(200).send('Subscription inactive');
    }
    
    // Check if event is subscribed
    if (!subscription.events.includes(notification.event)) {
      return res.status(200).send('Event not subscribed');
    }
    
    // Process notification
    await processTaskNotification(notification);
    
    // Log successful processing
    console.log(`Processed ${notification.event} for task ${notification.taskId}`);
    
    res.status(200).send('OK');
    
  } catch (error) {
    console.error('Webhook processing error:', error);
    
    // Return error status for retry
    res.status(500).send('Processing error');
  }
});

// Notification validation
const isValidTaskNotification = (notification) => {
  return notification &&
         typeof notification.taskId === 'string' &&
         typeof notification.event === 'string' &&
         notification.timestamp &&
         notification.data;
};
```

#### 2. Subscription Cleanup and Maintenance

```javascript
class SubscriptionMaintenance {
  constructor(subscriptionManager) {
    this.subscriptionManager = subscriptionManager;
    this.cleanupInterval = null;
  }
  
  startMaintenance(intervalMinutes = 60) {
    this.cleanupInterval = setInterval(
      () => this.performMaintenance(),
      intervalMinutes * 60 * 1000
    );
  }
  
  stopMaintenance() {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
  }
  
  async performMaintenance() {
    console.log('Starting subscription maintenance...');
    
    try {
      // Clean up completed tasks
      await this.cleanupCompletedTasks();
      
      // Validate webhook endpoints
      await this.validateWebhookEndpoints();
      
      // Remove stale subscriptions
      await this.removeStaleSubscriptions();
      
      // Log maintenance results
      const activeCount = this.subscriptionManager.getActiveSubscriptionCount();
      console.log(`Maintenance complete. ${activeCount} active subscriptions.`);
      
    } catch (error) {
      console.error('Maintenance error:', error);
    }
  }
  
  async cleanupCompletedTasks() {
    const subscriptions = this.subscriptionManager.getAllSubscriptions();
    
    for (const subscription of subscriptions) {
      try {
        const task = await this.getTaskStatus(subscription.taskId);
        
        if (task.status === 'COMPLETED' || task.status === 'FAILED') {
          // Keep subscription for a grace period
          const completionTime = new Date(task.updatedAt);
          const gracePeriod = 24 * 60 * 60 * 1000; // 24 hours
          
          if (Date.now() - completionTime.getTime() > gracePeriod) {
            await this.subscriptionManager.deleteSubscription(subscription.subscriptionId);
            console.log(`Cleaned up subscription for completed task ${subscription.taskId}`);
          }
        }
      } catch (error) {
        console.error(`Error checking task ${subscription.taskId}:`, error);
      }
    }
  }
  
  async validateWebhookEndpoints() {
    const subscriptions = this.subscriptionManager.getAllSubscriptions();
    
    for (const subscription of subscriptions) {
      try {
        // Test webhook endpoint availability
        const response = await fetch(subscription.callbackUrl, {
          method: 'HEAD',
          timeout: 5000
        });
        
        if (!response.ok) {
          console.warn(`Webhook endpoint unreachable: ${subscription.callbackUrl}`);
          // Could pause subscription or notify owner
        }
      } catch (error) {
        console.warn(`Webhook endpoint error for ${subscription.subscriptionId}:`, error.message);
      }
    }
  }
}
```

#### 3. Performance Optimization

```javascript
// Batched subscription operations
class BatchSubscriptionManager extends SubscriptionManager {
  async batchCreateSubscriptions(requests) {
    const results = [];
    const batchSize = 10; // Process in batches
    
    for (let i = 0; i < requests.length; i += batchSize) {
      const batch = requests.slice(i, i + batchSize);
      
      const batchPromises = batch.map(async (request) => {
        try {
          return await this.createSubscription(
            request.taskId,
            request.callbackUrl,
            request.events
          );
        } catch (error) {
          return { error: error.message, taskId: request.taskId };
        }
      });
      
      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);
      
      // Small delay between batches to avoid overwhelming the server
      if (i + batchSize < requests.length) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }
    
    return results;
  }
  
  // Efficient subscription lookup
  getSubscriptionsByTask(taskId) {
    // Use index for O(1) lookup instead of O(n) filtering
    return this.taskSubscriptionIndex.get(taskId) || [];
  }
  
  // Bulk status updates
  async bulkUpdateSubscriptionStatus(subscriptionIds, active) {
    const updatePromises = subscriptionIds.map(async (id) => {
      const subscription = this.subscriptions.get(id);
      if (subscription) {
        subscription.active = active;
        return this.updateSubscriptionOnServer(subscription);
      }
    });
    
    await Promise.all(updatePromises.filter(Boolean));
  }
}
```

---

## Integration Examples

### Complete Task Workflow with Response Management

```javascript
class TaskWorkflowManager {
  constructor(acpClient) {
    this.acpClient = acpClient;
    this.subscriptionManager = new SubscriptionManager();
  }
  
  async executeTaskWithMonitoring(initialMessage, assignTo, callbackUrl) {
    try {
      // 1. Create task
      const createResponse = await this.acpClient.call('tasks.create', {
        initialMessage,
        assignTo,
        priority: 'HIGH'
      });
      
      // Extract task from MethodResult
      if (createResponse.result.type !== 'task') {
        throw new Error('Expected task result from tasks.create');
      }
      
      const task = createResponse.result.task;
      console.log(`Created task: ${task.taskId}`);
      
      // 2. Set up monitoring subscription
      const subscribeResponse = await this.acpClient.call('tasks.subscribe', {
        taskId: task.taskId,
        callbackUrl,
        events: ['STATUS_CHANGE', 'COMPLETED', 'FAILED']
      });
      
      // Extract subscription from MethodResult
      if (subscribeResponse.result.type !== 'subscription') {
        throw new Error('Expected subscription result from tasks.subscribe');
      }
      
      const subscription = subscribeResponse.result.subscription;
      console.log(`Created subscription: ${subscription.subscriptionId}`);
      
      // 3. Store for management
      this.subscriptionManager.addSubscription(subscription);
      
      // 4. Return workflow tracking info
      return {
        taskId: task.taskId,
        subscriptionId: subscription.subscriptionId,
        status: task.status
      };
      
    } catch (error) {
      console.error('Task workflow error:', error);
      throw error;
    }
  }
  
  async checkTaskProgress(taskId) {
    const response = await this.acpClient.call('tasks.get', {
      taskId,
      includeMessages: true,
      includeArtifacts: true
    });
    
    if (response.result.type !== 'task') {
      throw new Error('Expected task result from tasks.get');
    }
    
    return response.result.task;
  }
  
  async sendTaskMessage(taskId, message) {
    const response = await this.acpClient.call('tasks.send', {
      taskId,
      message
    });
    
    if (response.result.type !== 'success') {
      throw new Error('Expected success result from tasks.send');
    }
    
    console.log(response.result.message);
    return true;
  }
}
```

### Stream Collaboration with Response Management

```javascript
class StreamCollaborationManager {
  constructor(acpClient) {
    this.acpClient = acpClient;
    this.activeStreams = new Map();
  }
  
  async startCollaboration(participants, purpose) {
    try {
      // Start stream
      const response = await this.acpClient.call('stream.start', {
        participants,
        metadata: { purpose }
      });
      
      if (response.result.type !== 'stream') {
        throw new Error('Expected stream result from stream.start');
      }
      
      const stream = response.result.stream;
      this.activeStreams.set(stream.streamId, stream);
      
      console.log(`Started collaboration stream: ${stream.streamId}`);
      return stream;
      
    } catch (error) {
      console.error('Stream start error:', error);
      throw error;
    }
  }
  
  async sendStreamMessage(streamId, message) {
    try {
      const response = await this.acpClient.call('stream.message', {
        streamId,
        message
      });
      
      if (response.result.type !== 'success') {
        throw new Error('Expected success result from stream.message');
      }
      
      console.log(`Message sent to stream ${streamId}`);
      return true;
      
    } catch (error) {
      console.error('Stream message error:', error);
      throw error;
    }
  }
  
  async endCollaboration(streamId, reason) {
    try {
      const response = await this.acpClient.call('stream.end', {
        streamId,
        reason
      });
      
      if (response.result.type !== 'success') {
        throw new Error('Expected success result from stream.end');
      }
      
      // Clean up local tracking
      this.activeStreams.delete(streamId);
      
      console.log(`Ended collaboration stream: ${streamId}`);
      return true;
      
    } catch (error) {
      console.error('Stream end error:', error);
      throw error;
    }
  }
}
```

---

## Performance Considerations

### Response Processing Optimization

#### 1. Efficient Result Handling

```javascript
// Pre-compiled result handlers for performance
const ResultHandlers = {
  task: (taskData) => {
    // Optimized task processing
    updateTaskCache(taskData);
    notifyTaskSubscribers(taskData);
    updateUI('task', taskData);
  },
  
  stream: (streamData) => {
    // Optimized stream processing
    updateStreamCache(streamData);
    notifyStreamParticipants(streamData);
    updateUI('stream', streamData);
  },
  
  subscription: (subscriptionData) => {
    // Optimized subscription processing
    storeSubscription(subscriptionData);
    scheduleCleanup(subscriptionData);
    updateUI('subscription', subscriptionData);
  },
  
  success: (message) => {
    // Simple success processing
    logSuccess(message);
    updateUI('success', message);
  },
  
  notification: (message) => {
    // Notification processing
    logNotification(message);
    updateUI('notification', message);
  }
};

// Fast result dispatching
const processResult = (result) => {
  const handler = ResultHandlers[result.type];
  if (handler) {
    handler(result[result.type] || result.message);
  } else {
    console.warn(`No handler for result type: ${result.type}`);
  }
};
```

#### 2. Subscription Performance

```javascript
// Optimized subscription storage and lookup
class PerformantSubscriptionManager {
  constructor() {
    this.subscriptions = new Map();           // subscriptionId → SubscriptionObject
    this.taskIndex = new Map();               // taskId → Set<subscriptionId>
    this.urlIndex = new Map();                // callbackUrl → Set<subscriptionId>
    this.eventIndex = new Map();              // event → Set<subscriptionId>
  }
  
  addSubscription(subscription) {
    const id = subscription.subscriptionId;
    
    // Store subscription
    this.subscriptions.set(id, subscription);
    
    // Update task index
    if (!this.taskIndex.has(subscription.taskId)) {
      this.taskIndex.set(subscription.taskId, new Set());
    }
    this.taskIndex.get(subscription.taskId).add(id);
    
    // Update URL index
    if (!this.urlIndex.has(subscription.callbackUrl)) {
      this.urlIndex.set(subscription.callbackUrl, new Set());
    }
    this.urlIndex.get(subscription.callbackUrl).add(id);
    
    // Update event index
    for (const event of subscription.events) {
      if (!this.eventIndex.has(event)) {
        this.eventIndex.set(event, new Set());
      }
      this.eventIndex.get(event).add(id);
    }
  }
  
  // O(1) lookup by task
  getSubscriptionsByTask(taskId) {
    const subscriptionIds = this.taskIndex.get(taskId) || new Set();
    return Array.from(subscriptionIds).map(id => this.subscriptions.get(id));
  }
  
  // O(1) lookup by event
  getSubscriptionsByEvent(event) {
    const subscriptionIds = this.eventIndex.get(event) || new Set();
    return Array.from(subscriptionIds).map(id => this.subscriptions.get(id));
  }
}
```

### Memory Management

```javascript
// Automatic cleanup for large-scale deployments
class MemoryEfficientSubscriptionManager extends PerformantSubscriptionManager {
  constructor(maxSubscriptions = 10000) {
    super();
    this.maxSubscriptions = maxSubscriptions;
    this.accessTimes = new Map(); // Track access for LRU
  }
  
  addSubscription(subscription) {
    // Enforce memory limits
    if (this.subscriptions.size >= this.maxSubscriptions) {
      this.evictOldestSubscriptions(Math.floor(this.maxSubscriptions * 0.1));
    }
    
    super.addSubscription(subscription);
    this.accessTimes.set(subscription.subscriptionId, Date.now());
  }
  
  getSubscription(subscriptionId) {
    const subscription = this.subscriptions.get(subscriptionId);
    if (subscription) {
      this.accessTimes.set(subscriptionId, Date.now());
    }
    return subscription;
  }
  
  evictOldestSubscriptions(count) {
    // Sort by access time (LRU)
    const sortedByAccess = Array.from(this.accessTimes.entries())
      .sort((a, b) => a[1] - b[1])
      .slice(0, count);
    
    for (const [subscriptionId] of sortedByAccess) {
      this.removeSubscription(subscriptionId);
    }
  }
}
```

---

## Security and Authentication

### Webhook Security

#### 1. Signature Validation

```javascript
const crypto = require('crypto');

// Webhook signature validation
const validateWebhookSignature = (req, secret) => {
  const signature = req.headers['x-webhook-signature'];
  if (!signature) {
    return false;
  }
  
  const body = JSON.stringify(req.body);
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(body)
    .digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(signature, 'hex'),
    Buffer.from(expectedSignature, 'hex')
  );
};

// Secure webhook handler
app.post('/webhooks/tasks', (req, res) => {
  // Validate signature
  if (!validateWebhookSignature(req, process.env.WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid signature');
  }
  
  // Process validated webhook
  processTaskNotification(req.body);
  res.status(200).send('OK');
});
```

#### 2. HTTPS Enforcement

```javascript
// Subscription validation with HTTPS requirement
const validateSubscriptionRequest = (params) => {
  const { callbackUrl, events, taskId } = params;
  
  // Validate callback URL
  try {
    const url = new URL(callbackUrl);
    
    if (url.protocol !== 'https:') {
      throw new Error('Callback URL must use HTTPS');
    }
    
    // Additional validation
    if (url.hostname === 'localhost' && process.env.NODE_ENV === 'production') {
      throw new Error('Localhost callbacks not allowed in production');
    }
    
  } catch (error) {
    throw new Error(`Invalid callback URL: ${error.message}`);
  }
  
  // Validate events
  const validEvents = ['STATUS_CHANGE', 'NEW_MESSAGE', 'NEW_ARTIFACT', 'COMPLETED', 'FAILED'];
  const invalidEvents = events.filter(event => !validEvents.includes(event));
  
  if (invalidEvents.length > 0) {
    throw new Error(`Invalid events: ${invalidEvents.join(', ')}`);
  }
  
  return true;
};
```

### OAuth 2.0 Integration

```javascript
// OAuth-aware subscription management
class SecureSubscriptionManager extends SubscriptionManager {
  constructor(oauthClient) {
    super();
    this.oauthClient = oauthClient;
  }
  
  async createSubscription(taskId, callbackUrl, events, accessToken) {
    // Validate OAuth token and scopes
    const tokenInfo = await this.oauthClient.validateToken(accessToken);
    
    if (!tokenInfo.scopes.includes('acp:notifications:receive')) {
      throw new Error('Insufficient OAuth2 scope for notifications');
    }
    
    // Validate task access
    if (!await this.hasTaskAccess(taskId, tokenInfo)) {
      throw new Error('No access to specified task');
    }
    
    // Create subscription with user context
    return super.createSubscription(taskId, callbackUrl, events, {
      userId: tokenInfo.userId,
      clientId: tokenInfo.clientId
    });
  }
  
  async hasTaskAccess(taskId, tokenInfo) {
    // Check if user/client has access to the task
    const response = await this.acpClient.call('tasks.get', {
      taskId
    }, {
      headers: {
        'Authorization': `Bearer ${tokenInfo.accessToken}`
      }
    });
    
    return response.result.type === 'task';
  }
}
```

---

## Testing and Debugging

### Response Validation Testing

```javascript
// Comprehensive response validation
const validateMethodResult = (result) => {
  const errors = [];
  
  // Check required type field
  if (!result.type) {
    errors.push('Missing required field: type');
  }
  
  if (!['task', 'stream', 'subscription', 'notification', 'success'].includes(result.type)) {
    errors.push(`Invalid type: ${result.type}`);
  }
  
  // Validate discriminated union
  switch (result.type) {
    case 'task':
      if (!result.task) {
        errors.push('Task result missing task data');
      } else {
        errors.push(...validateTaskObject(result.task));
      }
      break;
      
    case 'stream':
      if (!result.stream) {
        errors.push('Stream result missing stream data');
      } else {
        errors.push(...validateStreamObject(result.stream));
      }
      break;
      
    case 'subscription':
      if (!result.subscription) {
        errors.push('Subscription result missing subscription data');
      } else {
        errors.push(...validateSubscriptionObject(result.subscription));
      }
      break;
      
    case 'success':
    case 'notification':
      if (!result.message || typeof result.message !== 'string') {
        errors.push('Message result missing or invalid message');
      }
      break;
  }
  
  // Check for unexpected fields
  const allowedFields = ['type', 'task', 'stream', 'subscription', 'message'];
  const extraFields = Object.keys(result).filter(key => !allowedFields.includes(key));
  if (extraFields.length > 0) {
    errors.push(`Unexpected fields: ${extraFields.join(', ')}`);
  }
  
  return errors;
};

// Test suite for response handling
describe('Response Management', () => {
  describe('MethodResult validation', () => {
    test('valid task result', () => {
      const result = {
        type: 'task',
        task: {
          taskId: 'task-123',
          status: 'COMPLETED',
          createdAt: '2024-01-15T10:00:00Z',
          messages: [],
          artifacts: []
        }
      };
      
      const errors = validateMethodResult(result);
      expect(errors).toHaveLength(0);
    });
    
    test('invalid type field', () => {
      const result = {
        type: 'invalid',
        message: 'test'
      };
      
      const errors = validateMethodResult(result);
      expect(errors).toContain('Invalid type: invalid');
    });
    
    test('missing required data field', () => {
      const result = {
        type: 'task'
        // missing task field
      };
      
      const errors = validateMethodResult(result);
      expect(errors).toContain('Task result missing task data');
    });
  });
  
  describe('Subscription handling', () => {
    test('webhook notification processing', async () => {
      const notification = {
        taskId: 'task-123',
        event: 'COMPLETED',
        timestamp: '2024-01-15T10:00:00Z',
        data: {
          taskId: 'task-123',
          status: 'COMPLETED'
        }
      };
      
      const result = await processTaskNotification(notification);
      expect(result).toBe(true);
    });
  });
});
```

### Debug Utilities

```javascript
// Response debugging utilities
class ResponseDebugger {
  static logResponse(response, context = '') {
    console.group(`ACP Response ${context}`);
    
    console.log('JSON-RPC Fields:');
    console.log(`  jsonrpc: ${response.jsonrpc}`);
    console.log(`  id: ${response.id}`);
    
    if (response.error) {
      console.log('Error:');
      console.log(`  code: ${response.error.code}`);
      console.log(`  message: ${response.error.message}`);
      if (response.error.data) {
        console.log(`  data:`, response.error.data);
      }
    } else if (response.result) {
      console.log('Result:');
      console.log(`  type: ${response.result.type}`);
      
      switch (response.result.type) {
        case 'task':
          console.log(`  task.taskId: ${response.result.task.taskId}`);
          console.log(`  task.status: ${response.result.task.status}`);
          break;
        case 'stream':
          console.log(`  stream.streamId: ${response.result.stream.streamId}`);
          console.log(`  stream.status: ${response.result.stream.status}`);
          break;
        case 'subscription':
          console.log(`  subscription.subscriptionId: ${response.result.subscription.subscriptionId}`);
          console.log(`  subscription.active: ${response.result.subscription.active}`);
          break;
        case 'success':
        case 'notification':
          console.log(`  message: ${response.result.message}`);
          break;
      }
    }
    
    console.groupEnd();
  }
  
  static validateResponseStructure(response) {
    const issues = [];
    
    // JSON-RPC validation
    if (!response.jsonrpc || response.jsonrpc !== '2.0') {
      issues.push('Invalid or missing jsonrpc field');
    }
    
    if (response.id === undefined) {
      issues.push('Missing id field');
    }
    
    // Result/Error validation
    const hasResult = !!response.result;
    const hasError = !!response.error;
    
    if (!hasResult && !hasError) {
      issues.push('Missing both result and error fields');
    }
    
    if (hasResult && hasError) {
      issues.push('Both result and error fields present');
    }
    
    // Result structure validation
    if (hasResult) {
      const resultIssues = validateMethodResult(response.result);
      issues.push(...resultIssues);
    }
    
    return issues;
  }
}
```

---

## Summary

The **Response Management** schemas complete the ACP communication framework by providing:

### Core Capabilities

✅ **Unified Response Structure** - Single pattern for handling all ACP method responses  
✅ **Type Discrimination** - Clear, type-safe indication of response content  
✅ **Subscription Management** - Complete webhook lifecycle for task notifications  
✅ **Error Consistency** - Standardized error handling across all operations  
✅ **Performance Optimization** - Efficient response processing and subscription management  

### Integration Benefits

✅ **Client Simplification** - One response handler for all ACP operations  
✅ **Type Safety** - Strong typing support for development tools  
✅ **Webhook Reliability** - Robust notification delivery with comprehensive management  
✅ **Scalability** - Optimized for high-volume agent communication  
✅ **Security** - HTTPS enforcement and OAuth 2.0 integration throughout  

### Development Experience

✅ **Consistent API** - Predictable response patterns across all methods  
✅ **Rich Debugging** - Comprehensive validation and debugging utilities  
✅ **Easy Testing** - Clear validation patterns for automated testing  
✅ **Production Ready** - Performance optimizations and memory management  

The Response Management layer ensures that ACP communication is not only functionally complete but also developer-friendly, performant, and production-ready. Combined with the other schema categories, it provides a comprehensive foundation for building sophisticated agent-to-agent communication systems.

**The ACP specification is now complete with all 20 schemas fully documented across 5 comprehensive categories! 🎉** 