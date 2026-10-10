# Environment configuration

Status: **IMPLEMENTED / LOCAL configuration**, used by live providers when enabled.
The root `.env` is the normal home for Azure, Fabric and Foundry variables. It is Git-ignored.
Do not paste its values into documentation, screenshots, logs or commits.

Precedence: constructor arguments > process environment > `.env.local` > `.env` > defaults.
`.env.local` is optional, not required. The tracked [template](../../.env.example) contains
switches and variable names only. Existing private YAML bindings remain compatible; explicit
environment bindings take precedence.

| Group | Variables | Used for |
|---|---|---|
| Runtime | `FFIA_ENVIRONMENT`, `FFIA_OVERLAY`, `FFIA_FABRIC_LIVE`, `FFIA_FOUNDRY_LIVE`, `FFIA_ALLOW_LIVE_MUTATION` | HYBRID routing, overlay, enabled providers, write gate |
| Azure | `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP` | Pinned delegated identity and Foundry resource scope |
| Fabric | `FABRIC_WORKSPACE_ALIAS`, `FABRIC_WORKSPACE_ID`, `FABRIC_WORKSPACES`, `FABRIC_CONNECTION_NAME` | Dev workspace, JSON alias/semantic-model bindings, Foundry's existing Fabric connection |
| Foundry | `FOUNDRY_RESOURCE_NAME`, `FOUNDRY_PROJECT_NAME`, `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL_DEPLOYMENT`, `FOUNDRY_AGENT_NAMES` | Existing resource/project, validated endpoint, deployment, JSON list of existing agents |
| Optional telemetry | `FFIA_APPLICATIONINSIGHTS_CONNECTION_STRING` | Explicitly enabled client telemetry export; never needed by offline tests |

`FABRIC_WORKSPACES` is a JSON object whose keys are neutral aliases; each entry contains a
`workspace_id` and a `semantic_models` alias-to-ID map. `FOUNDRY_AGENT_NAMES` is a JSON array.
Named cloud values are held as `SecretStr` in settings. Invalid bindings are rejected without
echoing their values. The endpoint must match the bound Foundry account and project.

Entra/Azure CLI authentication is used. An API key, client secret or browser credential is
not required. Sign in to the intended demo tenant privately. Never replace the signed-in
user with a service principal for the preview Fabric data agent tool.

## Startup

```bash
source .venv/bin/activate
make run                         # .env-backed live-first HYBRID; both guides
make run API_ARGS=--offline       # explicitly disables cloud providers and writes
make demo-offline                 # always offline, regardless of .env
```

Restart the API after changing `.env`; it is read at process startup. Shell variables are
not automatically exported by this file, but the application, readiness commands and Guide 2
code-first script load it through the same typed settings/binding resolver.

The code-first agent-authoring script creates a version and still needs separate write
approval. For existing-agent verification use `make demo-live` instead.

## Missing service or binding

- HYBRID with no local bindings: startup logs a warning; reads return LOCAL with a fallback reason.
- Invalid/partial environment bindings: explicit configuration error, never silent simulation.
- Strict LIVE: no local fallback.
- Writes: live mutation flag remains off by default; no failed live write becomes a local write.
- Tests and frontend fixture export ignore private dotenv files; opt-in live tests are separate.
