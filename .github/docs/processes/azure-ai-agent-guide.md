# Azure AI Agent Development Guide

> **API-First on Azure**: Build CLI and UI agents with OpenAPI, APIM, Azure Functions, and Azure AI Foundry.

---

## Overview

This guide provides architectural patterns and implementation guidance for building AI-powered agents (CLI and web UI) on Azure with an **API-first** approach.

**Target architecture**:
- **Contract**: OpenAPI 3.1.1 specification (single source of truth)
- **Gateway**: Azure API Management (APIM)
- **Compute**: Azure Functions (serverless backend)
- **Clients**: Next.js (web UI) and CLI (thin wrappers over same API)
- **AI Platform**: Azure AI Foundry
- **Infrastructure**: Terraform (declarative, version-controlled)
- **Governance**: Azure Landing Zones / Azure AI Landing Zones

**Key principle**: **Contract-first, infrastructure-as-code, PaaS-first**

---

## Architecture Philosophy

### Contract-First Development

**OpenAPI 3.1.1 as the contract**:
- Single source of truth for all endpoints, schemas, auth
- Frontend and backend both implement the same contract
- Changes to API start with OpenAPI spec update
- Swagger UI provides human-readable documentation

**Workflow**:
1. Design API in OpenAPI specification
2. Review and validate spec
3. Implement backend (Azure Functions)
4. Implement clients (Next.js UI + CLI)
5. Deploy via Terraform

**Benefits**:
- ✅ No client/backend mismatch (contract enforced)
- ✅ API changes are explicit and reviewable
- ✅ Swagger UI auto-generates documentation
- ✅ Request/response validation at gateway (APIM)

---

### Infrastructure as Code

**Terraform-managed infrastructure**:
- All Azure resources defined in Terraform
- No "click-ops" in Azure Portal (except read-only troubleshooting)
- Changes applied via Terraform MCP pipelines
- Infrastructure state is declarative and version-controlled

**Benefits**:
- ✅ Reproducible environments (dev, staging, prod)
- ✅ Change history in version control
- ✅ Review process for infrastructure changes
- ✅ Disaster recovery (re-deploy from code)

---

### PaaS-First + Foundry-First

**Azure PaaS services**:
- Prefer managed services over IaaS (less operational overhead)
- Leverage Azure Landing Zone guardrails (networking, identity, policy)
- Use Azure AI Foundry for AI/ML capabilities

**Examples**:
- Azure API Management (not self-hosted API gateway)
- Azure Functions (not VMs running custom services)
- Azure AI Foundry (not self-managed ML infrastructure)

**Benefits**:
- ✅ Less operational burden (Azure manages patching, scaling)
- ✅ Built-in compliance (Landing Zone policies enforced)
- ✅ Cost-effective (pay for usage, not idle capacity)

---

## System Architecture

### High-Level Flow

```
┌─────────────┐
│   Next.js   │ (Web UI)
│   App Service│
└──────┬──────┘
       │
       │ HTTPS + Bearer Token
       ▼
┌─────────────────────────┐
│   Azure API Management  │ (Gateway)
│   - Auth enforcement    │
│   - Request validation  │
│   - Rate limiting       │
│   - Routing             │
└──────┬──────────────────┘
       │
       │ Backend call
       ▼
┌─────────────────────────┐
│   Azure Functions       │ (Backend)
│   - Business logic      │
│   - Data persistence    │
│   - Azure AI Foundry    │
└─────────────────────────┘

┌─────────────┐
│     CLI     │ (Thin wrapper)
└──────┬──────┘
       │
       │ HTTPS + Bearer Token
       └───────────────────────┐
                               │
                               ▼
                        (Same APIM endpoint)
```

**Key points**:
- CLI and web UI call the **same API endpoints**
- APIM enforces auth, validation, rate limits
- Functions implement business logic (stateless)
- Infrastructure provisioned via Terraform

---

## OpenAPI Contract: The Source of Truth

### Core Principle

**OpenAPI is the contract, not a suggestion.**

- **Do not invent** endpoints, fields, status codes, or headers
- If a capability is not in the OpenAPI contract: **update OpenAPI first, then implement**
- Backend and frontend must strictly conform to the contract

### OpenAPI 3.1.1 Structure

**Basic structure**:
```yaml
openapi: 3.1.1
info:
  title: My API
  version: 1.0.0
servers:
  - url: https://api.example.com/v1
paths:
  /resources:
    get:
      operationId: listResources
      summary: List all resources
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ResourceList'
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
  schemas:
    ResourceList:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Resource'
```

---

### Generating Compliant API Requests

**Workflow for every HTTP request** (in Next.js, CLI, tests, docs):

1. **Locate the operation** by `operationId` in OpenAPI
2. **Extract**:
   - Required/optional parameters
   - Security scheme(s)
   - Request body schema
   - Response schemas and status codes
3. **Produce request** matching this structure:

```http
<HTTP_METHOD> <BASE_PATH><PATH_TEMPLATE>?<QUERY> HTTP/1.1
Host: <APIM_GATEWAY_HOST>
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: <content-type-from-openapi>
Accept: <accept-from-openapi>
x-correlation-id: <uuid>

<REQUEST_BODY_IF_ANY>
```

4. **Validate conformance**:
   - Schema shape matches OpenAPI
   - Required fields present
   - Enum values valid
   - Date/time formats valid
   - Content-types match

---

### OpenAPI Validation in APIM

**Enable request/response validation** at the gateway:

```xml
<policies>
    <inbound>
        <validate-content 
            unspecified-content-type-action="prevent"
            max-size="102400"
            size-exceeded-action="detect"
            errors-variable-name="validationErrors">
            <content type="application/json" 
                     validate-as="json" 
                     action="prevent" />
        </validate-content>
    </inbound>
</policies>
```

**Benefits**:
- Invalid requests rejected at gateway (before reaching Functions)
- Response schema enforced (catches backend bugs)
- Automatic 400 Bad Request with validation errors

---

## Authentication & Authorization

### Web UI: Authorization Code + PKCE

**Azure AD B2C OAuth2 flow**:

**Setup**:
- Next.js app = public client (no client secret in browser)
- Use PKCE (Proof Key for Code Exchange)
- Acquire access token for API scope(s)

**Flow**:
1. User clicks "Login" in Next.js UI
2. Redirect to Azure AD B2C login page
3. User authenticates
4. Redirect back with authorization code
5. Exchange code for access token (PKCE verifier)
6. Attach token to API requests: `Authorization: Bearer <token>`

**Implementation** (Next.js with NextAuth.js):
```typescript
// pages/api/auth/[...nextauth].ts
import NextAuth from "next-auth";
import AzureADB2CProvider from "next-auth/providers/azure-ad-b2c";

export default NextAuth({
  providers: [
    AzureADB2CProvider({
      tenantId: process.env.AZURE_AD_B2C_TENANT_ID,
      clientId: process.env.AZURE_AD_B2C_CLIENT_ID,
      clientSecret: process.env.AZURE_AD_B2C_CLIENT_SECRET,
      primaryUserFlow: process.env.AZURE_AD_B2C_USER_FLOW,
      authorization: {
        params: {
          scope: `openid profile offline_access ${process.env.API_SCOPE}`,
        },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      return session;
    },
  },
});
```

**API call with token**:
```typescript
const response = await fetch('/api/resources', {
  headers: {
    'Authorization': `Bearer ${session.accessToken}`,
  },
});
```

**Security notes**:
- ✅ No client secret in browser (PKCE flow)
- ✅ Tokens stored server-side (NextAuth.js session)
- ✅ Refresh tokens for long sessions

---

### CLI: Authentication Options

**IMPORTANT**: Choose authentication method based on requirements.

#### Option 1: OAuth2 Device Code Flow (Recommended for user-facing CLIs)

**Use when**:
- CLI used by end users (not automation)
- Need per-user identity and audit logging
- Granular RBAC (different users, different permissions)
- Headless/SSH environments supported

**Flow**:
1. CLI initiates device code flow
2. Display code and URL to user in terminal
3. User opens browser on any device, enters code
4. User authenticates with Azure AD B2C
5. CLI polls for token
6. Attach token to requests: `Authorization: Bearer <token>`

**Implementation** (Python with msal):
```python
from msal import PublicClientApplication

app = PublicClientApplication(
    client_id="<cli-app-client-id>",
    authority="https://login.microsoftonline.com/<tenant-id>"
)

# Initiate device code flow
flow = app.initiate_device_flow(scopes=["api://<api-app-id>/.default"])
print(flow["message"])  # "To sign in, use a web browser to open..."

# Wait for user to authenticate
result = app.acquire_token_by_device_flow(flow)

if "access_token" in result:
    access_token = result["access_token"]
    # Use token in API requests
else:
    print(result.get("error_description"))
```

**Benefits**:
- ✅ Per-user identity (audit trail preserved)
- ✅ Granular RBAC (each user has own permissions)
- ✅ Works in headless environments (device code in terminal)
- ✅ Secure (no secrets in CLI)

**Tradeoffs**:
- ⚠️ Requires user interaction (typing device code)
- ⚠️ Token refresh needed for long sessions

---

#### Option 2: Client Credentials or API Keys (For automation/service scenarios)

**Use when**:
- CLI used for automation (CI/CD pipelines)
- Service accounts (not human users)
- Fully non-interactive required
- Locked-down environments

**Flow**:
1. CLI reads service principal credentials (client ID + secret)
2. Acquire token via client credentials flow
3. Attach token to requests: `Authorization: Bearer <token>`

**Implementation** (Python with msal):
```python
from msal import ConfidentialClientApplication

app = ConfidentialClientApplication(
    client_id="<service-principal-client-id>",
    client_credential="<service-principal-secret>",
    authority="https://login.microsoftonline.com/<tenant-id>"
)

result = app.acquire_token_for_client(scopes=["api://<api-app-id>/.default"])

if "access_token" in result:
    access_token = result["access_token"]
else:
    print(result.get("error_description"))
```

**Benefits**:
- ✅ Fully non-interactive (no user prompt)
- ✅ Simple for automation
- ✅ Works in locked-down environments

**Tradeoffs**:
- ❌ **No per-user identity** (all actions as service principal)
- ❌ **No per-user RBAC** (service principal permissions apply)
- ❌ **Limited audit logging** (cannot trace to individual humans)
- ⚠️ Requires secret management (rotation, secure storage)

---

#### Design Decision Checklist

**When implementing CLI authentication, clarify**:

- [ ] **Primary use case**: Human users OR automated services?
- [ ] **Audit requirements**: Need to trace actions to individual users?
- [ ] **RBAC requirements**: Different users have different permissions?
- [ ] **Environment**: Interactive terminals OR headless CI/CD?
- [ ] **Compliance**: Regulations requiring user attribution?

**Recommendation**:
- **Default**: Device Code Flow (maintains security/audit posture)
- **Exception**: Client Credentials only when strictly necessary for automation (document security/audit implications)

---

## Azure API Management (APIM)

### APIM Responsibilities

**APIM is the "edge"** - handles cross-cutting concerns:

1. **Authentication/Authorization enforcement**
   - Validate bearer tokens
   - Enforce RBAC policies
   - Rate limit per user/subscription

2. **Request/Response validation**
   - Validate against OpenAPI schema
   - Reject malformed requests early
   - Enforce content-type constraints

3. **Rate limiting and quotas**
   - Protect backend from abuse
   - Fair usage policies
   - Different tiers (free, paid, enterprise)

4. **Routing**
   - Route to appropriate backend (Functions)
   - Path rewrites if needed
   - Load balancing

5. **Observability**
   - Correlation IDs for tracing
   - Request/response logging
   - Integration with Application Insights

---

### APIM Policy Examples

**Validate JWT token** (inbound):
```xml
<policies>
    <inbound>
        <validate-jwt header-name="Authorization" 
                      failed-validation-httpcode="401" 
                      failed-validation-error-message="Unauthorized">
            <openid-config url="https://login.microsoftonline.com/{tenant-id}/v2.0/.well-known/openid-configuration" />
            <audiences>
                <audience>api://{api-app-id}</audience>
            </audiences>
            <issuers>
                <issuer>https://login.microsoftonline.com/{tenant-id}/v2.0</issuer>
            </issuers>
        </validate-jwt>
    </inbound>
</policies>
```

**Rate limiting** (inbound):
```xml
<rate-limit calls="100" renewal-period="60" 
            remaining-calls-variable-name="remainingCalls" />
<quota calls="10000" renewal-period="86400" />
```

**Add correlation ID** (inbound):
```xml
<set-variable name="correlationId" value="@(Guid.NewGuid().ToString())" />
<set-header name="x-correlation-id" exists-action="override">
    <value>@(context.Variables.GetValueOrDefault<string>("correlationId"))</value>
</set-header>
```

**Log to Application Insights** (outbound):
```xml
<log-to-eventhub logger-id="ai-logger">
    @{
        return new JObject(
            new JProperty("correlationId", context.Variables["correlationId"]),
            new JProperty("method", context.Request.Method),
            new JProperty("url", context.Request.Url.ToString()),
            new JProperty("statusCode", context.Response.StatusCode)
        ).ToString();
    }
</log-to-eventhub>
```

---

### Import OpenAPI into APIM

**Terraform configuration**:
```hcl
resource "azurerm_api_management_api" "my_api" {
  name                = "my-api"
  resource_group_name = azurerm_resource_group.rg.name
  api_management_name = azurerm_api_management.apim.name
  revision            = "1"
  display_name        = "My API"
  path                = "api/v1"
  protocols           = ["https"]

  import {
    content_format = "openapi+json"
    content_value  = file("${path.module}/openapi.json")
  }
}
```

**Azure CLI** (for testing):
```bash
az apim api import \
  --path api/v1 \
  --resource-group my-rg \
  --service-name my-apim \
  --specification-path openapi.json \
  --specification-format OpenApi+Json
```

---

## Azure Functions (Backend)

### Function Responsibilities

**Azure Functions implement business logic**:

1. **Process API requests** (parse, validate inputs)
2. **Execute business logic** (core functionality)
3. **Persist state** (write to storage/database)
4. **Call Azure AI Foundry** (for AI/ML features)
5. **Return responses** (conforming to OpenAPI schema)

**Design principles**:
- ✅ **Stateless** (no in-memory state across invocations)
- ✅ **Idempotent** (safe to retry)
- ✅ **Fast** (milliseconds to seconds, not minutes)
- ✅ **Isolated** (one function per logical operation)

---

### Function Example (Python)

**OpenAPI operation**:
```yaml
/resources/{id}:
  get:
    operationId: getResource
    parameters:
      - name: id
        in: path
        required: true
        schema:
          type: string
    responses:
      '200':
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Resource'
      '404':
        description: Not found
```

**Azure Function implementation**:
```python
import logging
import azure.functions as func
from typing import Optional

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('GetResource function triggered')
    
    # Extract path parameter
    resource_id = req.route_params.get('id')
    
    if not resource_id:
        return func.HttpResponse(
            '{"error": "Missing resource ID"}',
            status_code=400,
            mimetype="application/json"
        )
    
    # Fetch resource (example: from storage)
    resource = get_resource_from_storage(resource_id)
    
    if not resource:
        return func.HttpResponse(
            '{"error": "Resource not found"}',
            status_code=404,
            mimetype="application/json"
        )
    
    # Return response matching OpenAPI schema
    return func.HttpResponse(
        resource.to_json(),
        status_code=200,
        mimetype="application/json"
    )

def get_resource_from_storage(resource_id: str) -> Optional[dict]:
    # Implementation: query Azure Storage, Cosmos DB, etc.
    pass
```

**function.json**:
```json
{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "authLevel": "function",
      "type": "httpTrigger",
      "direction": "in",
      "name": "req",
      "methods": ["get"],
      "route": "resources/{id}"
    },
    {
      "type": "http",
      "direction": "out",
      "name": "$return"
    }
  ]
}
```

---

### Azure AI Foundry Integration

**Call Azure AI Foundry from Functions**:

```python
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential

# Initialize client
client = ChatCompletionsClient(
    endpoint="https://<your-foundry-endpoint>",
    credential=AzureKeyCredential("<your-api-key>")
)

# Generate response
response = client.complete(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Azure AI Foundry?"}
    ],
    model="gpt-4",
    max_tokens=500
)

answer = response.choices[0].message.content
```

**Best practices**:
- ✅ Use Managed Identity (no API keys in code)
- ✅ Cache frequently-used responses
- ✅ Stream responses for long completions
- ✅ Handle rate limits and retries

---

## Client Implementation

### Next.js Web UI

**Typed API client** (generated from OpenAPI):

```typescript
// lib/api-client.ts
import { useSession } from 'next-auth/react';

export const useApiClient = () => {
  const { data: session } = useSession();
  
  const fetchApi = async (path: string, options: RequestInit = {}) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}${path}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${session?.accessToken}`,
        'Content-Type': 'application/json',
        'x-correlation-id': crypto.randomUUID(),
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    return response.json();
  };
  
  return { fetchApi };
};
```

**Component usage**:
```typescript
// components/ResourceList.tsx
import { useApiClient } from '@/lib/api-client';
import { useEffect, useState } from 'react';

export const ResourceList = () => {
  const { fetchApi } = useApiClient();
  const [resources, setResources] = useState([]);
  
  useEffect(() => {
    fetchApi('/resources')
      .then(data => setResources(data.items))
      .catch(err => console.error('Failed to fetch resources:', err));
  }, []);
  
  return (
    <ul>
      {resources.map(resource => (
        <li key={resource.id}>{resource.name}</li>
      ))}
    </ul>
  );
};
```

---

### CLI Implementation

**CLI as thin wrapper** (Python with typer):

```python
# cli.py
import typer
import requests
from typing import Optional

app = typer.Typer()

API_BASE_URL = "https://api.example.com/v1"

def get_access_token() -> str:
    # Device code flow implementation (see Auth section)
    pass

@app.command()
def list_resources():
    """List all resources"""
    token = get_access_token()
    
    response = requests.get(
        f"{API_BASE_URL}/resources",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        for item in data["items"]:
            typer.echo(f"{item['id']}: {item['name']}")
    else:
        typer.echo(f"Error: {response.status_code}", err=True)

@app.command()
def get_resource(resource_id: str):
    """Get a specific resource by ID"""
    token = get_access_token()
    
    response = requests.get(
        f"{API_BASE_URL}/resources/{resource_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        typer.echo(f"ID: {data['id']}")
        typer.echo(f"Name: {data['name']}")
    elif response.status_code == 404:
        typer.echo(f"Resource not found: {resource_id}", err=True)
    else:
        typer.echo(f"Error: {response.status_code}", err=True)

if __name__ == "__main__":
    app()
```

**Usage**:
```bash
# List resources
python cli.py list-resources

# Get specific resource
python cli.py get-resource abc123
```

---

## Terraform Infrastructure

### Terraform + MCP Workflow

**Principle**: All infrastructure changes via Terraform, never "click-ops".

**Workflow**:
1. **Plan**: Update Terraform configuration
2. **Review**: Generate terraform plan, review diffs
3. **Apply**: Execute via Terraform MCP pipeline
4. **Verify**: Check Azure resources match desired state

**Benefits**:
- ✅ Reproducible (infrastructure as code)
- ✅ Version controlled (change history)
- ✅ Reviewable (PRs for infra changes)
- ✅ Rollback-able (revert to previous commit)

---

### Terraform MCP Server

**HashiCorp Terraform MCP server**:
- Provides up-to-date provider/module information
- Avoids stale resource arguments
- Integrates with Cursor and other IDEs

**Documentation**: https://developer.hashicorp.com/terraform/mcp-server/deploy

**Usage**:
- Use MCP server to look up providers/modules
- Generate Terraform code from MCP queries
- Validate configurations before apply

---

### Example Terraform Configuration

**Full stack** (APIM + Functions + App Service):

```hcl
# main.tf

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "rg-myapp-prod"
  location = "East US"
}

# API Management
resource "azurerm_api_management" "apim" {
  name                = "apim-myapp-prod"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  publisher_name      = "My Company"
  publisher_email     = "api@example.com"
  sku_name            = "Developer_1"
}

# Import OpenAPI
resource "azurerm_api_management_api" "api" {
  name                = "myapp-api"
  resource_group_name = azurerm_resource_group.rg.name
  api_management_name = azurerm_api_management.apim.name
  revision            = "1"
  display_name        = "My App API"
  path                = "api/v1"
  protocols           = ["https"]

  import {
    content_format = "openapi+json"
    content_value  = file("${path.module}/openapi.json")
  }
}

# Azure Functions
resource "azurerm_storage_account" "functions_sa" {
  name                     = "stmyappfnprod"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_service_plan" "functions_plan" {
  name                = "asp-myapp-functions-prod"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "Y1" # Consumption plan
}

resource "azurerm_linux_function_app" "functions" {
  name                       = "func-myapp-prod"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = azurerm_resource_group.rg.location
  service_plan_id            = azurerm_service_plan.functions_plan.id
  storage_account_name       = azurerm_storage_account.functions_sa.name
  storage_account_access_key = azurerm_storage_account.functions_sa.primary_access_key

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME" = "python"
    "AzureWebJobsFeatureFlags"  = "EnableWorkerIndexing"
  }
}

# Next.js App Service
resource "azurerm_service_plan" "app_plan" {
  name                = "asp-myapp-web-prod"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "B1"
}

resource "azurerm_linux_web_app" "web" {
  name                = "app-myapp-web-prod"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.app_plan.id

  site_config {
    application_stack {
      node_version = "18-lts"
    }
  }

  app_settings = {
    "NEXT_PUBLIC_API_BASE_URL" = "https://${azurerm_api_management.apim.name}.azure-api.net/api/v1"
    "AZURE_AD_B2C_TENANT_ID"   = var.azure_ad_b2c_tenant_id
    "AZURE_AD_B2C_CLIENT_ID"   = var.azure_ad_b2c_client_id
  }
}
```

---

## Azure Landing Zones

### Governance and Compliance

**Azure Landing Zones provide**:
- **Networking**: VNet, subnets, private endpoints, NSGs
- **Identity**: Managed Identity, RBAC, least privilege
- **Policy**: Azure Policy for compliance enforcement
- **Security**: Azure Security Center, Key Vault
- **Monitoring**: Application Insights, Log Analytics
- **Cost Management**: Tagging, budgets, alerts

**Alignment checklist**:
- [ ] Services support Private Endpoints (VNet integration)
- [ ] Managed Identity enabled (no API keys in code)
- [ ] Azure Policy compliance validated
- [ ] Tagging applied (cost center, environment, owner)
- [ ] Logging/monitoring configured (Application Insights)
- [ ] Key Vault for secrets (connection strings, API keys)

---

### Landing Zone Guardrails

**When adding new Azure resources, ensure**:

1. **Networking constraints**:
   - Private endpoints where required
   - VNet integration for Functions/App Service
   - NSG rules reviewed

2. **Identity constraints**:
   - Managed Identity for resource-to-resource auth
   - Least privilege RBAC assignments
   - No service principal secrets in code

3. **Policy compliance**:
   - Azure Policy allows the resource type
   - Required tags present (environment, cost center, owner)
   - SKUs within approved list

4. **Security requirements**:
   - TLS 1.2+ enforced
   - Secrets in Key Vault (not app settings)
   - Diagnostics enabled (logs to Log Analytics)

---

## Definition of Done (Per Feature)

**Checklist for completing a feature**:

- [ ] **OpenAPI updated** (if API changes required)
  - [ ] Reviewed and validated
  - [ ] Published to Swagger UI
  
- [ ] **APIM updated**
  - [ ] OpenAPI contract imported
  - [ ] Policies configured (auth, validation, rate limit)
  
- [ ] **Azure Functions updated**
  - [ ] Business logic implemented
  - [ ] Status codes match OpenAPI
  - [ ] Response schemas conform to contract
  
- [ ] **Next.js client updated**
  - [ ] Typed API calls
  - [ ] Error handling
  - [ ] Telemetry (correlation IDs)
  
- [ ] **CLI updated**
  - [ ] Commands implemented (thin wrapper)
  - [ ] Same contract as web UI
  - [ ] Error messages user-friendly
  
- [ ] **Terraform updated**
  - [ ] Infrastructure changes in Terraform
  - [ ] Applied via MCP pipelines
  - [ ] No portal drift
  
- [ ] **Logging/tracing**
  - [ ] Correlation IDs flow end-to-end
  - [ ] Application Insights configured
  - [ ] Errors logged with context
  
- [ ] **Landing Zone alignment**
  - [ ] Networking constraints met
  - [ ] Identity constraints met
  - [ ] Policy compliance validated
  - [ ] Cost tags applied

---

## Best Practices

### API Design

✅ **RESTful conventions**:
- Use HTTP verbs correctly (GET, POST, PUT, DELETE)
- Nouns for resources, verbs for actions
- Plural resource names (`/resources`, not `/resource`)

✅ **Versioning**:
- Include version in URL path (`/api/v1/resources`)
- Never break backward compatibility within a version
- Deprecate old versions with migration period

✅ **Error responses**:
- Consistent error schema across all endpoints
- Include correlation ID for troubleshooting
- User-friendly messages (not stack traces)

**Example error schema**:
```json
{
  "error": {
    "code": "ResourceNotFound",
    "message": "The resource with ID 'abc123' was not found",
    "correlationId": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

### Security

✅ **Authentication**:
- Always use bearer tokens (no API keys in URLs)
- Validate tokens at APIM (before backend)
- Short token expiry (1 hour)

✅ **Authorization**:
- Enforce RBAC at APIM or Functions
- Least privilege principle
- Audit sensitive operations

✅ **Secrets**:
- Store in Azure Key Vault
- Use Managed Identity to access Key Vault
- Rotate secrets regularly
- Never commit secrets to version control

✅ **Input validation**:
- Validate at APIM (OpenAPI schema)
- Validate again in Functions (defense in depth)
- Sanitize inputs (prevent injection attacks)

---

### Observability

✅ **Correlation IDs**:
- Generate at APIM, pass to Functions
- Include in all logs
- Return in error responses (for support)

✅ **Logging**:
- Log request/response at APIM
- Log business events in Functions
- Centralize in Application Insights

✅ **Metrics**:
- Track API latency (p50, p95, p99)
- Track error rates (by endpoint)
- Track quota usage (per user/subscription)

✅ **Alerting**:
- Alert on high error rates (>5%)
- Alert on high latency (>2 seconds)
- Alert on quota exceeded

---

### Performance

✅ **Caching**:
- Cache frequently-accessed data
- Use Azure Redis Cache for shared state
- Set appropriate TTLs

✅ **Async processing**:
- Use Azure Storage Queues for background tasks
- Don't block API requests on slow operations
- Return 202 Accepted for async operations

✅ **Pagination**:
- Always paginate list endpoints
- Use cursor-based pagination (not offset)
- Default page size: 20-50 items

**Example pagination**:
```json
{
  "items": [...],
  "pagination": {
    "cursor": "eyJpZCI6MTIzfQ==",
    "hasMore": true
  }
}
```

---

## Troubleshooting

### Common Issues

**Issue**: 401 Unauthorized from APIM

**Causes**:
- Token expired
- Token not for correct audience
- Token validation policy misconfigured

**Solutions**:
1. Verify token not expired: Decode JWT at jwt.io
2. Check audience claim matches API app ID
3. Verify APIM policy `<audiences>` matches

---

**Issue**: 400 Bad Request from APIM validation

**Causes**:
- Request body doesn't match OpenAPI schema
- Missing required field
- Invalid enum value

**Solutions**:
1. Check APIM error response for validation details
2. Compare request against OpenAPI spec
3. Test with Swagger UI (should show same error)

---

**Issue**: Function timeout (504 Gateway Timeout)

**Causes**:
- Function taking >230 seconds (default timeout)
- Blocking on slow external API
- Database query slow

**Solutions**:
1. Increase function timeout (if legitimate)
2. Make async (return 202, process in background)
3. Optimize query or cache result
4. Use Durable Functions for long-running workflows

---

**Issue**: High latency on API calls

**Causes**:
- Cold start (Functions on Consumption plan)
- No caching (fetching same data repeatedly)
- N+1 query problem

**Solutions**:
1. Use Premium plan (eliminate cold starts)
2. Add caching (Redis Cache)
3. Optimize database queries (batch fetches)
4. Use CDN for static content

---

## Integration with Engineering Guides

### Related Guides

**[Development Workflow](development-workflow.md)**:
- Phase 0: Plan API endpoints (OpenAPI design)
- Phase 1: Set up Azure environment (Terraform)
- Phase 3: Implement Functions (TDD on backend)
- Phase 5: Deploy via Terraform MCP

**[Environment Setup Guide](environment-setup-guide.md)**:
- Devcontainers work for Azure Functions development
- Include Azure CLI, Terraform, Azure Functions Core Tools
- Mock APIM locally with Azure Functions proxies

**[TDD Principles](../philosophy/tdd-principles.md)**:
- Write tests for Functions (unit + integration)
- Mock Azure services (Storage, Cosmos DB)
- Test OpenAPI contract conformance

**[Documentation & Tracking Guide](documentation-tracking-guide.md)**:
- Document API in Confluence (with Swagger UI links)
- Track features in Jira/ADO (link to OpenAPI operations)
- Create ADRs for architecture decisions (APIM vs alternatives)

---

## References

### Microsoft Learn

- **API Design**: https://learn.microsoft.com/azure/architecture/best-practices/api-design
- **APIM + OpenAPI**: https://learn.microsoft.com/azure/api-management/import-api-from-oas
- **Azure Functions**: https://learn.microsoft.com/azure/azure-functions/
- **Azure AI Foundry**: https://learn.microsoft.com/azure/ai-foundry/
- **Azure Landing Zones**: https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/

### HashiCorp Developer

- **Terraform MCP Server**: https://developer.hashicorp.com/terraform/mcp-server/deploy
- **Azure Provider**: https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs

### OpenAPI

- **OpenAPI 3.1.1 Spec**: https://spec.openapis.org/oas/v3.1.1
- **Swagger Editor**: https://editor.swagger.io/

---

## Summary

**Key takeaways**:

✅ **Contract-first**: OpenAPI is the single source of truth  
✅ **Infrastructure as code**: Terraform for all Azure resources  
✅ **PaaS-first**: Leverage Azure managed services  
✅ **Consistent clients**: CLI and web UI call same API  
✅ **Governance**: Stay within Azure Landing Zone guardrails  
✅ **Observability**: Correlation IDs, logging, metrics  
✅ **Security**: Bearer tokens, RBAC, secrets in Key Vault  

**Start simple, evolve intentionally**:
1. Define OpenAPI contract
2. Deploy APIM + Functions (Terraform)
3. Implement Functions (TDD)
4. Build Next.js UI (OAuth2 + PKCE)
5. Build CLI (device code flow)
6. Add observability (Application Insights)
7. Optimize (caching, async processing)

---

**This guide aligns with**:
- [TDD Principles](../philosophy/tdd-principles.md) - Test backend conformance
- [Development Workflow](development-workflow.md) - API-first design in Phase 0
- [Environment Setup](environment-setup-guide.md) - Devcontainers for Azure dev
- [Documentation & Tracking](documentation-tracking-guide.md) - Document APIs, track features
