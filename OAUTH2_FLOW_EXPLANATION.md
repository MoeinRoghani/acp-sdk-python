# 🔐 OAuth2 Authentication Flow - Complete Code Explanation

## 🎯 **YOUR UNDERSTANDING IS PERFECT!**

Yes, you understand it correctly:

```
1. CLIENT: Give Client ID + Secret to OAuth URL
2. OAUTH SERVER: Returns JWT Token
3. CLIENT: Send requests to ACP Server with Token
4. ACP SERVER: Validates Token and responds
```

---

## 🔄 **COMPLETE OAUTH2 FLOW DIAGRAM**

```mermaid
sequenceDiagram
    participant C as Client
    participant O as OAuth2 Provider
    participant S as ACP Server
    
    Note over C,S: 1. TOKEN ACQUISITION (Client Side)
    C->>O: POST /oauth/token<br/>client_id + client_secret
    O->>C: JWT Access Token
    
    Note over C,S: 2. API CALLS (With Authentication)
    C->>S: ACP Request + Bearer Token
    S->>O: Validate Token (JWKS)
    O->>S: Token Valid + Claims
    S->>C: API Response
```

---

## 💻 **CLIENT SIDE CODE BREAKDOWN**

### **1. Token Acquisition (`oauth2_client.py`)**

```python
class OAuth2ClientCredentials:
    def __init__(self, token_url, client_id, client_secret, scope=None):
        self.token_url = token_url        # OAuth2 provider token endpoint
        self.client_id = client_id        # Your client ID  
        self.client_secret = client_secret # Your client secret
        self.scope = scope                # Requested permissions
```

**Token Request Process:**

```python
async def get_token(self) -> OAuth2Token:
    # 1. Prepare OAuth2 request
    token_data = {
        "grant_type": "client_credentials",  # OAuth2 flow type
        "client_id": self.client_id,         # Who you are
        "client_secret": self.client_secret, # Prove it's you
        "scope": self.scope,                 # What permissions you want
        "audience": self.audience            # Which API you want to access
    }
    
    # 2. Send request to OAuth2 provider
    response = await self._http_client.post(
        self.token_url,
        data=token_data,  # Form-encoded data
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # 3. Get JWT token back
    token_response = response.json()
    return OAuth2Token(
        access_token=token_response["access_token"],  # The JWT token
        expires_in=token_response.get("expires_in", 3600),
        scope=token_response.get("scope", "")
    )
```

### **2. Using Token in Client (`basic_client.py`)**

```python
# Get OAuth2 token
oauth_client = OAuth2ClientCredentials(
    token_url="https://your-auth0.auth0.com/oauth/token",
    client_id="your-client-id",
    client_secret="your-secret",
    scope="acp:agent:identify acp:tasks:write acp:streams:write"
)

token = await oauth_client.get_token()
oauth_token = token.access_token  # This is the JWT

# Create ACP client with token
client = Client(
    base_url="http://localhost:8002",
    oauth_token=oauth_token,  # JWT goes here
    allow_http=True
)

# Make authenticated requests
response = await client.tasks_create(params)  # Token sent automatically
```

---

## 🖥️ **SERVER SIDE CODE BREAKDOWN**

### **1. Token Validation Setup (`jwt_validator.py`)**

```python
class JWTValidator:
    def __init__(self, jwks_url, issuer, audience=None):
        self.jwks_url = jwks_url    # Where to get public keys
        self.issuer = issuer        # Who issued the token  
        self.audience = audience    # Who the token is for
        
        # JWKS client fetches public keys from OAuth2 provider
        self.jwks_client = PyJWKClient(jwks_url, cache_ttl=300)
```

**Token Validation Process:**

```python
async def validate_token(self, token: str) -> Dict[str, Any]:
    # 1. Get public key from OAuth2 provider's JWKS endpoint
    signing_key = self.jwks_client.get_signing_key_from_jwt(token)
    
    # 2. Verify JWT signature and claims
    payload = jwt.decode(
        token,                    # The JWT token
        signing_key.key,         # Public key from OAuth2 provider
        algorithms=["RS256"],    # Encryption algorithm
        issuer=self.issuer,      # Must match expected issuer
        audience=self.audience   # Must match expected audience
    )
    
    # 3. Extract user info and scopes
    return {
        "sub": payload.get("sub"),           # User ID
        "scope": payload.get("scope", ""),   # Permissions
        "agent_id": payload.get("client_id") # Client ID
    }
```

### **2. Request Authentication (`middleware.py`)**

```python
async def extract_auth_context(request) -> JsonRpcContext:
    # 1. Extract Bearer token from Authorization header
    auth_header = request.headers.get("authorization", "")
    
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        # 2. Validate the JWT token
        user_info = await validate_oauth_token(token)
        
        # 3. Create authenticated context
        context = JsonRpcContext(
            user_id=user_info.get("sub"),                    # User ID
            agent_id=user_info.get("agent_id"),              # Client ID  
            scopes=user_info.get("scope", "").split(),       # Permissions list
            is_authenticated=True                             # Mark as authenticated
        )
    else:
        # No token = unauthenticated context
        context = JsonRpcContext(is_authenticated=False)
    
    return context
```

### **3. Scope Enforcement (`validation.py`)**

```python
async def _validate_business_rules(self, request, context):
    # 1. Require authentication for ALL operations
    if not context.is_authenticated:
        raise JsonRpcError("Authentication required")
    
    # 2. Require basic scope for ALL operations  
    if not context.has_scope('acp:agent:identify'):
        raise JsonRpcError("Missing acp:agent:identify scope")
    
    # 3. Method-specific scope checks
    if request.method == 'tasks.create':
        if not context.has_scope('acp:tasks:write'):
            raise JsonRpcError("Missing acp:tasks:write scope")
    
    elif request.method == 'stream.start':
        if not context.has_scope('acp:streams:write'):
            raise JsonRpcError("Missing acp:streams:write scope")
```

---

## 🔑 **JWT TOKEN STRUCTURE**

**What's in the JWT token:**

```json
{
  "header": {
    "alg": "RS256",           // Encryption algorithm
    "typ": "JWT",             // Token type
    "kid": "key-id"           // Key ID for verification
  },
  "payload": {
    "iss": "https://your-auth0.auth0.com/",  // Who issued it
    "sub": "client-123",                      // Subject (client ID)
    "aud": "https://your-api.com",            // Audience (your API)
    "iat": 1691234567,                        // Issued at timestamp
    "exp": 1691238167,                        // Expires at timestamp
    "scope": "acp:agent:identify acp:tasks:write", // Permissions
    "client_id": "your-client-id"             // OAuth2 client ID
  },
  "signature": "..."          // Cryptographic signature
}
```

---

## 🛡️ **SECURITY VALIDATION STEPS**

### **Server validates EVERY request:**

1. **📝 Token Present?** - Check Authorization header
2. **✍️ Signature Valid?** - Verify with OAuth2 provider's public key
3. **⏰ Not Expired?** - Check `exp` timestamp
4. **🏢 Right Issuer?** - Verify `iss` claim
5. **🎯 Right Audience?** - Verify `aud` claim  
6. **🔑 Has Required Scopes?** - Check permissions for specific operation

---

## 🚀 **REAL EXAMPLE FLOW**

### **Step 1: Client Gets Token**
```bash
# OAuth2 request (behind the scenes)
POST https://your-auth0.auth0.com/oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=abc123&
client_secret=xyz789&
scope=acp:agent:identify acp:tasks:write&
audience=https://your-acp-api.com
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "acp:agent:identify acp:tasks:write"
}
```

### **Step 2: Client Calls ACP Server**
```bash
POST http://localhost:8002/jsonrpc
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "tasks.create",
  "params": { ... },
  "id": 1
}
```

### **Step 3: Server Validates & Responds**
```bash
# Server validates token with OAuth2 provider
GET https://your-auth0.auth0.com/.well-known/jwks.json
# Gets public keys to verify signature

# If valid, processes request and responds
{
  "jsonrpc": "2.0",
  "result": { ... },
  "id": 1
}
```

---

## ✅ **SUMMARY**

**Your understanding is 100% correct!**

1. **🔑 Client credentials** → OAuth2 provider → **JWT token**
2. **JWT token** → ACP server requests → **Validated & authorized**  
3. **Server checks** signature, expiration, scopes → **API response**

The system is **production-ready** with proper **cryptographic security**, **token validation**, and **fine-grained permissions**! 🎉