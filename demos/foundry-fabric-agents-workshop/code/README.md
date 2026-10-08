# Code-first samples: Foundry agents + Fabric (Guide 2)

These samples follow the current Microsoft Foundry SDK documentation (October 2026). They need a
Foundry project, a model deployment and, for the Fabric sample, a published Fabric data agent and a
project connection to it. They are **REQUIRES TENANT VALIDATION** until you run them in your tenant.

```bash
uv venv --python 3.14 .venv-foundry && source .venv-foundry/bin/activate
uv pip install azure-ai-projects azure-identity          # azure-ai-projects 2.6 or later
az login --tenant <TENANT_ID>
export FOUNDRY_PROJECT_ENDPOINT="https://<resource>.services.ai.azure.com/api/projects/<project>"
export FOUNDRY_MODEL_DEPLOYMENT="<deployment-name>"
export FABRIC_CONNECTION_NAME="<project-connection-to-the-fabric-data-agent>"
python fabric_sales_agent.py "Which product line grew fastest last month?"
python monthly_brief.py
python market_context_agent.py
```

| Sample | Shows | Labels |
|---|---|---|
| `fabric_sales_agent.py` | A prompt agent with the Fabric data agent tool (preview); answers under the signed-in user's identity | LIVE when run; PREVIEW tool |
| `monthly_brief.py` | One brief per business team focus area, using the same agent | LIVE when run |
| `market_context_agent.py` | Web search tool with citations; why queries leave the compliance boundary | LIVE when run |

Offline equivalents (LOCAL, synthetic): `ffia mfg brief`, `ffia mfg quality`.

Never put tenant, workspace or connection IDs in these files; use environment variables.
