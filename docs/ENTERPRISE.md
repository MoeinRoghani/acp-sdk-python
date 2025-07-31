# Enterprise Deployment Guide for ACP

This guide covers deploying ACP (Agent Communication Protocol) in enterprise environments using industry-standard patterns with API gateways, centralized discovery, and OAuth 2.0 authentication.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Apigee Integration](#apigee-integration)
- [Agent Discovery Service](#agent-discovery-service)
- [Security Implementation](#security-implementation)
- [Deployment Patterns](#deployment-patterns)
- [Monitoring & Observability](#monitoring--observability)
- [Best Practices](#best-practices)

## Architecture Overview

### Enterprise ACP Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Enterprise ACP Ecosystem                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────────────────────┐   │
│  │   Router Agent  │    │        Agent Discovery          │   │
│  │  (Supervisor)   │◄──►│         Service                  │   │
│  │                 │    │    (Agent Card Registry)        │   │
│  └─────────────────┘    └──────────────────────────────────┘   │
│           │                                                    │
│           ▼                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 Apigee API Gateway                      │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐   │   │
│  │  │   OAuth 2.0 │ │    Rate     │ │    Security     │   │   │
│  │  │   Provider  │ │   Limiting  │ │   Policies      │   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                    │
│                           ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Agent Services Layer                       │   │
│  │                                                         │   │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐    │   │
│  │ │   Sales     │ │   Support   │ │   Analytics     │    │   │
│  │ │   Agent     │ │   Agent     │ │     Agent       │    │   │
│  │ │ (ACP Server)│ │ (ACP Server)│ │  (ACP Server)   │    │   │
│  │ └─────────────┘ └─────────────┘ └─────────────────┘    │   │
│  │                                                         │   │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐    │   │
│  │ │   Legal     │ │    HR       │ │   Finance       │    │   │
│  │ │   Agent     │ │   Agent     │ │    Agent        │    │   │
│  │ │ (ACP Server)│ │ (ACP Server)│ │  (ACP Server)   │    │   │
│  │ └─────────────┘ └─────────────┘ └─────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Communication Flow

1. **Discovery Phase**: Router Agent queries Agent Discovery Service for available agents
2. **Authentication**: Router Agent obtains OAuth 2.0 token from Apigee
3. **Routing**: Router Agent sends tasks to appropriate specialist agents via Apigee
4. **Processing**: Specialist agents process tasks and return results
5. **Coordination**: Router Agent orchestrates multi-agent workflows

## Core Components

### 1. Router Agent (Supervisor)

The Router Agent acts as the **central coordinator** for all agent communication:

```python
# enterprise/router_agent.py
from acp import ACPClient
from acp.models.generated import TasksCreateParams, Message, Part
from typing import Dict, List, Optional
import asyncio

class EnterpriseRouterAgent:
    """
    Central router agent for enterprise ACP deployment.
    
    Coordinates communication between multiple specialist agents,
    handles load balancing, and manages complex workflows.
    """
    
    def __init__(self, discovery_service_url: str, apigee_config: dict):
        self.discovery_service = AgentDiscoveryClient(discovery_service_url)
        self.apigee_config = apigee_config
        self.agent_clients: Dict[str, ACPClient] = {}
        self.load_balancer = AgentLoadBalancer()
    
    async def initialize(self):
        """Initialize router with available agents"""
        # Discover all available agents
        agents = await self.discovery_service.get_all_agents()
        
        # Create ACP clients for each agent
        for agent in agents:
            client = ACPClient(
                base_url=agent.url,
                oauth_config=self.apigee_config,
                timeout=30.0
            )
            self.agent_clients[agent.name] = client
    
    async def route_task(
        self, 
        task_type: str, 
        message: Message,
        preferred_agent: Optional[str] = None
    ) -> str:
        """
        Route a task to the most appropriate agent.
        
        Args:
            task_type: Type of task (e.g., 'sales_analysis', 'legal_review')
            message: Task message
            preferred_agent: Optional specific agent to use
            
        Returns:
            Task ID for tracking
        """
        # Determine target agent
        if preferred_agent:
            agent_name = preferred_agent
        else:
            agent_name = await self._select_best_agent(task_type)
        
        # Create task
        client = self.agent_clients[agent_name]
        result = await client.tasks_create(TasksCreateParams(
            initialMessage=message,
            metadata={
                "router_id": self.instance_id,
                "task_type": task_type,
                "target_agent": agent_name
            }
        ))
        
        return result.taskId
    
    async def orchestrate_workflow(self, workflow_spec: Dict) -> Dict:
        """
        Orchestrate complex multi-agent workflows.
        
        Example workflow:
        1. Legal agent reviews contract
        2. Finance agent calculates costs
        3. Sales agent prepares proposal
        """
        workflow_id = str(uuid.uuid4())
        results = {}
        
        for step in workflow_spec["steps"]:
            # Execute step
            if step["type"] == "parallel":
                # Execute multiple agents in parallel
                tasks = []
                for subtask in step["tasks"]:
                    task = self.route_task(
                        subtask["type"],
                        subtask["message"],
                        subtask.get("agent")
                    )
                    tasks.append(task)
                
                # Wait for all parallel tasks
                step_results = await asyncio.gather(*tasks)
                results[step["name"]] = step_results
                
            elif step["type"] == "sequential":
                # Execute tasks in sequence
                for subtask in step["tasks"]:
                    # Use results from previous steps in message
                    enhanced_message = self._enhance_message_with_context(
                        subtask["message"], 
                        results
                    )
                    
                    task_id = await self.route_task(
                        subtask["type"],
                        enhanced_message,
                        subtask.get("agent")
                    )
                    
                    # Wait for completion and get results
                    result = await self._wait_for_task_completion(task_id)
                    results[subtask["name"]] = result
        
        return {
            "workflow_id": workflow_id,
            "status": "COMPLETED",
            "results": results
        }
```

### 2. Agent Discovery Service

Centralized registry for agent capabilities and endpoints:

```python
# enterprise/discovery_service.py
from fastapi import FastAPI, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
import json

class AgentCard(BaseModel):
    """Enterprise agent card with additional metadata"""
    name: str
    description: str
    version: str
    capabilities: List[str]
    url: str
    health_check_url: str
    department: str
    cost_center: Optional[str]
    sla_tier: str  # "gold", "silver", "bronze"
    max_concurrent_tasks: int
    oauth_scopes: List[str]
    
class AgentDiscoveryService:
    """
    Centralized agent discovery and registry service.
    
    Provides service discovery, health monitoring, and
    capability-based routing for enterprise agent deployments.
    """
    
    def __init__(self):
        self.app = FastAPI(title="ACP Agent Discovery Service")
        self.agents: Dict[str, AgentCard] = {}
        self.health_status: Dict[str, Dict] = {}
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        @self.app.get("/agents", response_model=List[AgentCard])
        async def get_all_agents():
            """Get all registered agents"""
            return list(self.agents.values())
        
        @self.app.get("/agents/{agent_name}", response_model=AgentCard)
        async def get_agent(agent_name: str):
            """Get specific agent details"""
            if agent_name not in self.agents:
                raise HTTPException(status_code=404, detail="Agent not found")
            return self.agents[agent_name]
        
        @self.app.get("/agents/by-capability/{capability}")
        async def get_agents_by_capability(capability: str):
            """Find agents with specific capability"""
            matching_agents = [
                agent for agent in self.agents.values()
                if capability in agent.capabilities
            ]
            return matching_agents
        
        @self.app.post("/agents/register")
        async def register_agent(agent: AgentCard):
            """Register a new agent"""
            self.agents[agent.name] = agent
            await self._initialize_health_monitoring(agent)
            return {"status": "registered", "agent": agent.name}
        
        @self.app.delete("/agents/{agent_name}")
        async def deregister_agent(agent_name: str):
            """Deregister an agent"""
            if agent_name in self.agents:
                del self.agents[agent_name]
                del self.health_status[agent_name]
            return {"status": "deregistered", "agent": agent_name}
        
        @self.app.get("/health")
        async def get_health_status():
            """Get health status of all agents"""
            return self.health_status
```

### 3. Specialist Agent Template

Template for creating department-specific agents:

```python
# enterprise/specialist_agent.py
from acp import ACPServer
from acp.models.generated import Message, Part, TaskObject
from typing import Dict, Any
import logging

class SpecialistAgent:
    """
    Base class for department-specific agents.
    
    Each department (Sales, Legal, HR, etc.) extends this class
    to implement domain-specific functionality.
    """
    
    def __init__(self, department: str, capabilities: List[str]):
        self.department = department
        self.capabilities = capabilities
        self.server = ACPServer(
            agent_name=f"{department}-agent",
            enable_cors=True,
            enable_logging=True
        )
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup common ACP method handlers"""
        
        @self.server.method_handler("tasks.create")
        async def handle_task_create(params, context):
            """Handle incoming task creation"""
            task_id = str(uuid.uuid4())
            
            # Log task for audit trail
            logging.info(f"Task created: {task_id}", extra={
                "department": self.department,
                "user_id": context.user_id,
                "task_type": params.metadata.get("task_type"),
                "router_id": params.metadata.get("router_id")
            })
            
            # Process task based on department logic
            result = await self.process_department_task(params, context)
            
            return {
                "taskId": task_id,
                "status": "SUBMITTED",
                "estimatedCompletionTime": result.get("eta"),
                "assignedProcessor": self.department
            }
        
        @self.server.method_handler("tasks.get")
        async def handle_task_get(params, context):
            """Get task status and results"""
            return await self.get_task_status(params.taskId, context)
    
    async def process_department_task(self, params, context) -> Dict[str, Any]:
        """
        Override this method in department-specific implementations.
        
        Args:
            params: Task parameters
            context: Request context with authentication info
            
        Returns:
            Processing result with department-specific data
        """
        raise NotImplementedError("Department must implement process_department_task")

# Example: Sales Agent Implementation
class SalesAgent(SpecialistAgent):
    """Sales department agent for CRM integration and sales analysis"""
    
    def __init__(self):
        super().__init__("sales", [
            "lead_analysis",
            "proposal_generation",
            "crm_integration",
            "sales_forecasting"
        ])
        self.crm_client = SalesforceClient()
    
    async def process_department_task(self, params, context) -> Dict[str, Any]:
        """Process sales-specific tasks"""
        message = params.initialMessage
        task_type = params.metadata.get("task_type", "general")
        
        if task_type == "lead_analysis":
            return await self._analyze_lead(message, context)
        elif task_type == "proposal_generation":
            return await self._generate_proposal(message, context)
        elif task_type == "sales_forecasting":
            return await self._forecast_sales(message, context)
        else:
            return await self._handle_general_sales_query(message, context)
    
    async def _analyze_lead(self, message: Message, context) -> Dict[str, Any]:
        """Analyze lead quality and provide recommendations"""
        # Extract lead data from message
        lead_data = self._extract_lead_data(message)
        
        # Score lead using ML model
        score = await self.lead_scoring_model.predict(lead_data)
        
        # Get similar leads from CRM
        similar_leads = await self.crm_client.find_similar_leads(lead_data)
        
        return {
            "eta": "2 minutes",
            "lead_score": score,
            "recommendations": self._generate_lead_recommendations(score),
            "similar_leads": similar_leads,
            "next_actions": self._suggest_next_actions(score)
        }
```

## Apigee Integration

### Apigee Configuration

#### 1. API Product Configuration

```yaml
# apigee/api-products/acp-agents.yaml
name: "acp-agents"
displayName: "ACP Agent Communication"
description: "Enterprise agent-to-agent communication via ACP protocol"
environments: ["prod", "staging", "dev"]
scopes:
  - "acp:agent:identify"
  - "acp:tasks:read"
  - "acp:tasks:write"
  - "acp:tasks:cancel"
  - "acp:streams:read"
  - "acp:streams:write"
  - "acp:notifications:receive"
quotas:
  - name: "requests-per-minute"
    limit: 1000
    interval: 1
    timeUnit: "minute"
operations:
  - resource: "/agents/**"
    methods: ["GET", "POST", "PUT", "DELETE"]
```

#### 2. OAuth 2.0 Policy

```xml
<!-- apigee/policies/oauth-validation.xml -->
<OAuthV2 name="OAuth-Validate-Access-Token">
    <DisplayName>OAuth Validate Access Token</DisplayName>
    <Operation>VerifyAccessToken</Operation>
    <GenerateResponse enabled="true"/>
    <Tokens>
        <Token ref="request.header.authorization"/>
    </Tokens>
    <Scope>acp:agent:identify</Scope>
</OAuthV2>
```

#### 3. Rate Limiting Policy

```xml
<!-- apigee/policies/rate-limit.xml -->
<Quota name="Rate-Limit-Policy">
    <DisplayName>Rate Limit Policy</DisplayName>
    <Allow count="1000" countRef="request.header.x-quota-override"/>
    <Interval>1</Interval>
    <TimeUnit>minute</TimeUnit>
    <Identifier ref="client_id"/>
    <Distributed>true</Distributed>
    <Synchronous>true</Synchronous>
    <AsynchronousConfiguration>
        <SyncIntervalInSeconds>20</SyncIntervalInSeconds>
        <SyncMessageCount>5</SyncMessageCount>
    </AsynchronousConfiguration>
</Quota>
```

#### 4. Security Policy

```xml
<!-- apigee/policies/security-headers.xml -->
<AssignMessage name="Add-Security-Headers">
    <DisplayName>Add Security Headers</DisplayName>
    <AssignTo createNew="false" transport="http" type="response"/>
    <Set>
        <Headers>
            <Header name="X-Frame-Options">DENY</Header>
            <Header name="X-Content-Type-Options">nosniff</Header>
            <Header name="X-XSS-Protection">1; mode=block</Header>
            <Header name="Strict-Transport-Security">max-age=31536000; includeSubDomains</Header>
            <Header name="Content-Security-Policy">default-src 'self'</Header>
        </Headers>
    </Set>
</AssignMessage>
```

### Apigee Proxy Configuration

```xml
<!-- apigee/proxies/acp-agents-proxy.xml -->
<ProxyEndpoint name="default">
    <HTTPProxyConnection>
        <BasePath>/v1/acp</BasePath>
        <VirtualHost>secure</VirtualHost>
    </HTTPProxyConnection>
    
    <PreFlow>
        <Request>
            <Step>
                <Name>OAuth-Validate-Access-Token</Name>
            </Step>
            <Step>
                <Name>Rate-Limit-Policy</Name>
            </Step>
        </Request>
        <Response>
            <Step>
                <Name>Add-Security-Headers</Name>
            </Step>
        </Response>
    </PreFlow>
    
    <RouteRule name="agent-discovery">
        <Condition>(proxy.pathsuffix MatchesPath "/discovery/**")</Condition>
        <TargetEndpoint>discovery-service</TargetEndpoint>
    </RouteRule>
    
    <RouteRule name="sales-agent">
        <Condition>(proxy.pathsuffix MatchesPath "/agents/sales/**")</Condition>
        <TargetEndpoint>sales-agent</TargetEndpoint>
    </RouteRule>
    
    <RouteRule name="legal-agent">
        <Condition>(proxy.pathsuffix MatchesPath "/agents/legal/**")</Condition>
        <TargetEndpoint>legal-agent</TargetEndpoint>
    </RouteRule>
</ProxyEndpoint>
```

## Security Implementation

### 1. OAuth 2.0 Flow for Enterprise

```python
# enterprise/auth.py
from acp.client.auth import OAuth2Handler
import requests
from typing import Dict, Optional

class EnterpriseOAuth2Handler(OAuth2Handler):
    """
    Enterprise OAuth 2.0 handler with Apigee integration.
    
    Supports client credentials flow with certificate-based authentication
    and automatic token refresh with proper audit logging.
    """
    
    def __init__(self, apigee_config: Dict):
        super().__init__()
        self.client_id = apigee_config["client_id"]
        self.client_secret = apigee_config["client_secret"]
        self.token_url = apigee_config["token_url"]
        self.scopes = apigee_config["scopes"]
        self.certificate_path = apigee_config.get("certificate_path")
        
    async def get_access_token(self) -> str:
        """Get OAuth 2.0 access token from Apigee"""
        
        # Prepare client credentials request
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": " ".join(self.scopes)
        }
        
        # Use certificate for mTLS if configured
        cert = None
        if self.certificate_path:
            cert = (
                f"{self.certificate_path}/client.crt",
                f"{self.certificate_path}/client.key"
            )
        
        # Request token from Apigee
        response = requests.post(
            self.token_url,
            data=data,
            cert=cert,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "ACP-Enterprise-Client/1.0"
            },
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Token request failed: {response.text}")
        
        token_data = response.json()
        
        # Log token acquisition for audit
        logging.info("OAuth token acquired", extra={
            "client_id": self.client_id,
            "scopes": self.scopes,
            "expires_in": token_data.get("expires_in")
        })
        
        return token_data["access_token"]
```

### 2. Certificate Management

```python
# enterprise/certificates.py
import ssl
import certifi
from pathlib import Path

class CertificateManager:
    """
    Manages SSL certificates for enterprise ACP deployment.
    
    Handles certificate validation, rotation, and monitoring
    for secure agent-to-agent communication.
    """
    
    def __init__(self, cert_directory: Path):
        self.cert_directory = cert_directory
        self.ca_bundle = cert_directory / "ca-bundle.crt"
        
    def create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with enterprise certificates"""
        context = ssl.create_default_context()
        
        # Load custom CA bundle if available
        if self.ca_bundle.exists():
            context.load_verify_locations(str(self.ca_bundle))
        else:
            context.load_verify_locations(certifi.where())
        
        # Require certificate verification
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        
        return context
    
    def validate_certificate_chain(self, hostname: str, port: int = 443) -> bool:
        """Validate certificate chain for agent endpoint"""
        try:
            context = self.create_ssl_context()
            with ssl.create_connection((hostname, port)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    # Additional validation logic here
                    return True
        except Exception as e:
            logging.error(f"Certificate validation failed: {e}")
            return False
```

## Deployment Patterns

### 1. Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: acp-router-agent
  labels:
    app: acp-router-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: acp-router-agent
  template:
    metadata:
      labels:
        app: acp-router-agent
    spec:
      containers:
      - name: router-agent
        image: your-registry/acp-router-agent:1.0.0
        ports:
        - containerPort: 8080
        env:
        - name: DISCOVERY_SERVICE_URL
          value: "https://discovery.acp.internal"
        - name: APIGEE_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: apigee-credentials
              key: client-id
        - name: APIGEE_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: apigee-credentials
              key: client-secret
        volumeMounts:
        - name: certificates
          mountPath: /etc/ssl/certs
          readOnly: true
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: certificates
        secret:
          secretName: acp-certificates
---
apiVersion: v1
kind: Service
metadata:
  name: acp-router-agent-service
spec:
  selector:
    app: acp-router-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

### 2. Docker Compose for Development

```yaml
# docker-compose.yml
version: '3.8'

services:
  discovery-service:
    build: ./enterprise/discovery
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/discovery
    depends_on:
      - postgres
  
  router-agent:
    build: ./enterprise/router
    ports:
      - "8002:8000"
    environment:
      - DISCOVERY_SERVICE_URL=http://discovery-service:8000
      - APIGEE_TOKEN_URL=https://your-org-test.apigee.net/oauth/token
    depends_on:
      - discovery-service
  
  sales-agent:
    build: ./enterprise/agents/sales
    ports:
      - "8003:8000"
    environment:
      - AGENT_NAME=sales-agent
      - DISCOVERY_SERVICE_URL=http://discovery-service:8000
  
  legal-agent:
    build: ./enterprise/agents/legal
    ports:
      - "8004:8000"
    environment:
      - AGENT_NAME=legal-agent
      - DISCOVERY_SERVICE_URL=http://discovery-service:8000
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=discovery
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Monitoring & Observability

### 1. Metrics Collection

```python
# enterprise/monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import logging
import time

# Metrics
task_requests = Counter('acp_task_requests_total', 'Total task requests', ['agent', 'task_type'])
task_duration = Histogram('acp_task_duration_seconds', 'Task processing duration')
active_connections = Gauge('acp_active_connections', 'Active ACP connections')

class ACPMonitoring:
    """Enterprise monitoring for ACP deployment"""
    
    def __init__(self):
        self.logger = logging.getLogger('acp.monitoring')
    
    def record_task_request(self, agent: str, task_type: str):
        """Record a task request"""
        task_requests.labels(agent=agent, task_type=task_type).inc()
    
    def record_task_duration(self, duration: float):
        """Record task processing duration"""
        task_duration.observe(duration)
    
    def update_active_connections(self, count: int):
        """Update active connection count"""
        active_connections.set(count)
    
    def log_security_event(self, event_type: str, details: dict):
        """Log security-related events"""
        self.logger.warning(f"Security event: {event_type}", extra=details)
```

### 2. Distributed Tracing

```python
# enterprise/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_tracing():
    """Setup distributed tracing for ACP"""
    
    # Configure tracer
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger-agent",
        agent_port=6831,
    )
    
    # Configure span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    return tracer
```

## Best Practices

### 1. Security Best Practices

- **Always use HTTPS** for all ACP communication
- **Implement certificate pinning** for critical agent endpoints
- **Use short-lived tokens** (15-30 minutes) with automatic refresh
- **Log all security events** for audit and compliance
- **Implement proper RBAC** with least privilege principle
- **Use network segmentation** to isolate agent services

### 2. Scalability Best Practices

- **Implement circuit breakers** for agent communication
- **Use connection pooling** for HTTP clients
- **Implement proper retry logic** with exponential backoff
- **Monitor resource usage** and scale horizontally
- **Use async/await** patterns for non-blocking I/O
- **Implement proper caching** for discovery service

### 3. Operational Best Practices

- **Implement comprehensive health checks** for all services
- **Use structured logging** with correlation IDs
- **Monitor SLA compliance** and agent performance
- **Implement automated testing** for agent communication
- **Use blue-green deployments** for zero-downtime updates
- **Maintain proper documentation** and runbooks

### 4. Governance Best Practices

- **Establish clear agent ownership** by department
- **Implement change management** for agent updates
- **Define SLA tiers** based on business criticality
- **Implement cost tracking** per department/agent
- **Regular security audits** and penetration testing
- **Establish disaster recovery** procedures

---

This enterprise deployment guide provides a comprehensive foundation for deploying ACP in production environments with proper security, scalability, and governance controls. 