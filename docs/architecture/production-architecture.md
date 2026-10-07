# Production deployment (aligned to the Foundry baseline)

The application tier follows the Azure Architecture Center **baseline Microsoft Foundry chat
reference architecture**. Microsoft Fabric is added as the governed data platform, and MCP tools
are governed once, through an API Management-backed gateway.

- **Nothing in this view is deployed by this repository.**
- Every component is documented Microsoft behavior. Validate it in your tenant before relying on
  it.

The accelerator running on a laptop corresponds to the **basic** Foundry chat tier: identity is
the perimeter, with no network isolation. The basic tier is explicitly not for production.

## Architecture

<!-- BEGIN GENERATED DIAGRAM: run `ffia diagrams render`; do not edit by hand -->

> Generated from [`education/architecture/views/production.yaml`](../../education/architecture/views/production.yaml). Edit the YAML, then run `ffia diagrams render`.

- **draw.io:** [diagrams/production.drawio](diagrams/production.drawio). Open it in draw.io desktop, diagrams.net or the VS Code Draw.io Integration extension. Page 1 is the full architecture; the next pages build it up one step at a time.
- **Interactive:** run `make run`, then open `http://localhost:5173/architecture/production` to build it step by step, trace requests, switch Executive to L400 and see live runtime state.

```mermaid
flowchart LR
  subgraph vnet["Workload virtual network (private endpoints)"]
    app_gateway["Application Gateway + WAF<br/><small>Sole public entry point</small>"]
    web_app["App Service web app<br/><small>Chat UI and API, zone-redundant</small>"]
    foundry_agent["Foundry Agent Service<br/><small>Foundry project, standard setup</small>"]
    models["Foundry models<br/><small>Deployed model</small>"]
    ai_search["Azure AI Search<br/><small>Grounding index</small>"]
    cosmos["Azure Cosmos DB<br/><small>Agent conversations (customer-owned)</small>"]
    storage["Azure Storage<br/><small>Uploaded files (customer-owned)</small>"]
    key_vault["Key Vault<br/><small>Gateway TLS certificate</small>"]
    private_endpoints["Private endpoints<br/><small>All PaaS in the network</small>"]
    firewall["Azure Firewall<br/><small>Sole egress path</small>"]
  end
  subgraph fabric_capacity["Microsoft Fabric capacity (F2 or higher) - same tenant and region"]
    data_agent["Fabric data agent · PREVIEW<br/><small>Read, user's permissions</small>"]
    semantic_model["Semantic model<br/><small>Direct Lake, RLS applies</small>"]
    onelake["OneLake medallion<br/><small>Deployment pattern chosen per tenant</small>"]
  end
  subgraph tool_zone["Governed tool access (private)"]
    apim["API Management AI gateway · optional<br/><small>Govern MCP tools once</small>"]
    mcp_servers["MCP servers<br/><small>Private, in the network</small>"]
  end
  subgraph platform["Identity and operations"]
    entra["Microsoft Entra ID<br/><small>Users and managed identities</small>"]
    managed_identity["Managed identities<br/><small>Service to service</small>"]
    app_insights["Application Insights<br/><small>Traces and correlation</small>"]
    log_analytics["Azure Monitor<br/><small>Logs and alerts</small>"]
    purview["Microsoft Purview · tenant<br/><small>Data governance</small>"]
    approvals["Approved change flow<br/><small>Scoped writer, audit</small>"]
  end
  users["Users<br/><small>Entra ID sign-in</small>"]
  users -->|HTTPS| app_gateway
  app_gateway -->|WAF inspected| web_app
  web_app -->|Managed identity| foundry_agent
  foundry_agent -->|Reason| models
  foundry_agent -->|Ground| ai_search
  foundry_agent -->|Files| storage
  storage -->|Conversation state| cosmos
  foundry_agent -->|Fabric tool (PREVIEW) as the user| data_agent
  data_agent -->|Governed measures| semantic_model
  semantic_model -->|Direct Lake| onelake
  foundry_agent -->|Outbound tool calls| firewall
  firewall -->|Allowed egress| apim
  apim -->|Policy, quota, audit| mcp_servers
  entra --> managed_identity
  app_insights --> log_analytics
  class users,app_gateway,web_app,foundry_agent,models,ai_search,cosmos,storage,key_vault,private_endpoints,semantic_model,onelake,mcp_servers,firewall,entra,managed_identity,app_insights,log_analytics documented
  class approvals implemented
  class apim optional
  class data_agent preview
  class purview tenant_validation
  classDef implemented stroke-width:2px
  classDef planned stroke-dasharray: 6 4
  classDef preview stroke-dasharray: 2 3
  classDef optional stroke-dasharray: 8 4
  classDef documented stroke-width:1px
  classDef tenant_validation stroke-dasharray: 3 3
```

Solid boxes are implemented here or documented by Microsoft; dashed boxes are planned, preview or optional.

### Workflow

*DOCUMENTED.* The governed-question flow on production infrastructure, numbered like an Azure Architecture Center workflow.

1. A signed-in user opens the chat experience over HTTPS.
2. Application Gateway terminates TLS and the WAF inspects the request.
3. The web app calls Foundry Agent Service through a private endpoint with its managed identity.
4. The agent follows its instructions and selects tools.
5. It asks the Fabric data agent with the user's identity. Preview. Same tenant and region; each user needs access to the data agent and its sources.
6. The data agent answers from governed measures; row-level security still applies.
7. The model composes the answer with the retrieved context.
8. The conversation is persisted in your Cosmos DB before the response returns.
9. Traces and logs land in Application Insights and Azure Monitor.

### Components

| Component | Status | Role | In this repository |
|---|---|---|---|
| Users | Microsoft-documented | Users sign in with Microsoft Entra ID. Their identity flows to the Fabric data agent, which only returns data they are allowed to see. | - |
| Application Gateway + WAF | Microsoft-documented | Terminates TLS, inspects traffic with the web application firewall and routes to the web app. It is the only public entry point in the baseline. | - |
| App Service web app | Microsoft-documented | Hosts the chat experience. Calls Foundry Agent Service over a private endpoint with a managed identity - no keys in configuration. | - |
| Foundry Agent Service | Microsoft-documented | Owns reasoning and orchestration; consumes Fabric context; never performs authoritative writes directly. | - |
| Foundry models | Microsoft-documented | The deployed model the agent reasons with, reached over private connectivity. | - |
| Azure AI Search | Microsoft-documented | Grounding index used by the agent's search tool, reached through a private endpoint with managed identity and least-privilege roles. | - |
| Azure Cosmos DB | Microsoft-documented | Stores agent conversation state in your subscription. Foundry manages the schema; you own the resource, its governance and its audit. | - |
| Azure Storage | Microsoft-documented | Holds files uploaded in chat sessions, owned by your subscription and managed by Foundry. | - |
| Key Vault | Microsoft-documented | Holds the TLS certificate for Application Gateway. Services authenticate with managed identities, so no application secrets are stored. | - |
| Private endpoints | Microsoft-documented | Every platform service is reached through a private endpoint; public access is disabled. | - |
| Fabric data agent | Preview | Uses the end user's identity; Fabric permissions decide what is visible. | - |
| Semantic model | Microsoft-documented | Direct Lake reads Gold Delta tables; measures are the governed definitions agents should reuse. | - |
| OneLake medallion | Microsoft-documented | Lakehouses in OneLake hold each layer; notebooks transform; tests check row counts and baselines. | - |
| API Management AI gateway | Optional | Adds authentication, rate limits, logging and policies in front of MCP servers and model endpoints. | - |
| MCP servers | Microsoft-documented | Workload-owned MCP servers reached privately. Record-level authorization stays in the server. | - |
| Azure Firewall | Microsoft-documented | All outbound traffic from agents - public tools and external MCP servers - is inspected and allowed or denied here. | - |
| Microsoft Entra ID | Microsoft-documented | User, approver and writer are different identities; agents act on behalf of users or as scoped identities. | - |
| Managed identities | Microsoft-documented | The web app, Foundry project and gateway authenticate to each other with managed identities and least-privilege role assignments. | - |
| Application Insights | Microsoft-documented | Structured logs with correlation IDs locally; traces in a monitoring service in production. | - |
| Azure Monitor | Microsoft-documented | Central logs, metrics and alerts for the workload, including gateway and firewall diagnostics. | - |
| Microsoft Purview | Requires tenant validation | Data governance across Fabric items. Validate which Purview capabilities apply to your Fabric items and region. | - |
| Approved change flow | Implemented in this repository | Separation of duties, expiry and destination binding protect the decision. | - |

### Aligned to

- [Baseline Microsoft Foundry chat reference architecture](https://learn.microsoft.com/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-chat) (GUIDANCE)
- [Basic Microsoft Foundry chat reference architecture](https://learn.microsoft.com/azure/architecture/ai-ml/architecture/basic-microsoft-foundry-chat) (GUIDANCE)
- [Baseline Microsoft Foundry chat reference architecture in an Azure landing zone](https://learn.microsoft.com/azure/architecture/ai-ml/architecture/baseline-microsoft-foundry-landing-zone) (GUIDANCE)
- [Use the Microsoft Fabric data agent tool in Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/fabric) (PREVIEW)
- [Overview of MCP servers in Azure API Management](https://learn.microsoft.com/azure/api-management/mcp-server-overview) (GA)
- [Govern MCP tools by using an AI gateway (Microsoft Foundry)](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/governance) (PREVIEW)
- [Microsoft Fabric deployment patterns](https://learn.microsoft.com/azure/architecture/data-guide/technology-choices/fabric-deployment-patterns) (GUIDANCE)
- [Azure Well-Architected Framework service guide for Microsoft Fabric](https://learn.microsoft.com/azure/well-architected/microsoft-fabric/overview) (GUIDANCE)
- [Data architecture for AI agents across your organization](https://learn.microsoft.com/azure/cloud-adoption-framework/ai-agents/data-architecture-plan) (GUIDANCE)

<!-- END GENERATED DIAGRAM -->

## Design decisions to carry into production

| Decision | Baseline guidance | Why it matters here |
|---|---|---|
| One public entry | Application Gateway with WAF in front of the web app | Agents and the Foundry portal are not publicly reachable |
| Private connectivity | Private endpoints for every platform service | Data and agent state never cross the public internet |
| Controlled egress | Azure Firewall is the only egress path for agent tool calls | External tools and MCP servers are allowed explicitly |
| No secrets | Managed identities between services; Key Vault holds only the gateway TLS certificate | Removes key sprawl |
| Shared responsibility | Foundry manages agent state in Cosmos DB, Storage and AI Search in *your* subscription | Govern, monitor and audit those resources as your own |
| User identity to Fabric | Foundry Fabric data agent tool is **preview**; on behalf of the user, same tenant and region | Fabric permissions and RLS still apply; service principals are not supported |
| One MCP gateway | The Foundry AI gateway for MCP tools runs on API Management (**preview** in the Foundry portal) | Draw one gateway, not two; backend authorization stays in each server |
| Fabric deployment pattern | Choose monolithic, multi-workspace or multi-capacity deliberately | Workspaces are the governance boundary; capacities isolate performance |

## Considerations

- **Reliability:** use zone-redundant app hosting as in the baseline, and Fabric capacity and
  replication strategies per the Well-Architected guide for Fabric.
- **Security:** identity first, then network isolation and egress control. Approval, the scoped
  writer and audit still apply to every write.
- **Cost Optimization:** account for gateway, firewall, private endpoints and Fabric capacity.
  Use the basic tier only for proofs of concept.
- **Operational Excellence:** follow the landing-zone split between platform and workload teams,
  using Git and deployment pipelines for Fabric items.
- **Performance Efficiency:** keep the data agent on curated sources, and serve governed
  measures through Direct Lake.

## Related

- [reference-architecture.md](reference-architecture.md) and [live-vs-offline.md](live-vs-offline.md).
