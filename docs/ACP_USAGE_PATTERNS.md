# 🔄 ACP Communication Patterns Guide

## 📱 **STREAM Methods** (Synchronous/Real-time)

### **When to Use:**
- ✅ **Immediate response needed** - "I ask, I wait, I get answer"
- ✅ **Interactive conversations** - Back-and-forth dialog
- ✅ **Real-time collaboration** - Live document editing, chat
- ✅ **Streaming data** - Real-time updates, live feeds

### **Flow Pattern:**
```javascript
// Client initiates stream
await client.stream_start({
    participants: ["user-123", "agent-456"],
    initialMessage: "Hello, let's discuss this project"
});

// Real-time conversation
await client.stream_message({
    streamId: "stream-123",
    message: "What are the requirements?"
});

// Agent responds immediately via same stream
// Client receives response in real-time

// End when done
await client.stream_end({
    streamId: "stream-123",
    reason: "Conversation complete"
});
```

### **Use Cases:**
- 💬 **Chat conversations** - "Ask agent a question, get immediate answer"
- 🤝 **Interactive planning** - "Collaborate on a document in real-time"
- 📊 **Live data analysis** - "Stream data and get real-time insights"
- 🎮 **Interactive workflows** - "Step-by-step guided processes"

---

## 📬 **TASK Methods** (Asynchronous/Fire-and-forget)

### **When to Use:**
- ✅ **Long-running operations** - "Start work, check back later"
- ✅ **Background processing** - "Do this while I work on other things"
- ✅ **Batch operations** - "Process this dataset overnight"
- ✅ **Non-urgent requests** - "Get to this when you can"

### **Flow Pattern:**
```javascript
// Client creates task
const response = await client.tasks_create({
    initialMessage: "Analyze this large dataset",
    priority: "NORMAL"
});

const taskId = response.task.taskId;

// Client does other work...
// ...hours later...

// Check if task is complete
const status = await client.tasks_get({ taskId });

if (status.task.status === "COMPLETED") {
    // Process results
    console.log("Analysis complete:", status.task.result);
}
```

### **Use Cases:**
- 🔍 **Data analysis** - "Analyze this dataset and send results when done"
- 📝 **Document processing** - "Extract text from 1000 PDFs"
- 🔧 **System operations** - "Deploy this application"
- 📊 **Report generation** - "Create monthly analytics report"

---

## 🎯 **Decision Matrix**

| **Scenario** | **Method** | **Why** |
|--------------|------------|---------|
| "Ask agent a quick question" | **STREAM** | Need immediate answer |
| "Generate a 100-page report" | **TASK** | Long-running, can wait |
| "Live chat with agent" | **STREAM** | Real-time conversation |
| "Process overnight batch job" | **TASK** | Background operation |
| "Debug code together" | **STREAM** | Interactive collaboration |
| "Scan security vulnerabilities" | **TASK** | Long analysis, not urgent |
| "Real-time translation" | **STREAM** | Immediate results needed |
| "Monthly data backup" | **TASK** | Scheduled background work |

---

## 💡 **Practical Examples**

### **STREAM Example: Interactive Code Review**
```javascript
// Start code review session
await client.stream_start({
    participants: ["developer-123", "ai-reviewer"],
    metadata: { type: "code-review", language: "python" }
});

// Developer: "Please review this function"
await client.stream_message({ 
    streamId: id,
    message: "def calculate_total(items): ..." 
});

// AI responds immediately with feedback
// Developer can ask follow-up questions
// Real-time back-and-forth conversation

await client.stream_end({ streamId: id });
```

### **TASK Example: Large Dataset Analysis**
```javascript
// Submit analysis job
const task = await client.tasks_create({
    initialMessage: "Analyze customer behavior from 1M records",
    priority: "HIGH",
    metadata: { dataset: "customers-2024.csv" }
});

// Developer works on other features...
// 2 hours later...

// Check if analysis is done
const result = await client.tasks_get({ taskId: task.taskId });
if (result.status === "COMPLETED") {
    // Use the analysis results
}
```

---

## 🔧 **Technical Differences**

### **STREAMS:**
- 🔄 **Connection state** - Maintains session
- ⚡ **Low latency** - Immediate responses
- 🔀 **Bidirectional** - Both sides can send messages
- 📱 **Session-based** - start → messages → end

### **TASKS:**
- 🔥 **Fire-and-forget** - No maintained connection
- ⏳ **Higher latency** - Check status later
- ➡️ **Request-response** - Client requests, agent responds
- 📋 **Stateless** - Each request independent

---

## 🎯 **Summary**

**Use STREAMS when:**
- You need **immediate interaction**
- It's a **conversation or collaboration**
- **Real-time** responses are important
- You're **waiting for the response**

**Use TASKS when:**
- It's a **long-running operation**
- You can **do other work while waiting**
- Results are **not immediately needed**
- It's **background processing**

Both patterns are essential for different use cases in agent-to-agent communication!