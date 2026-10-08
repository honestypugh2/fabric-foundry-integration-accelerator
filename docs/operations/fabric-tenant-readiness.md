# Fabric tenant readiness for the live labs

The default demo is offline and needs no tenant. This runbook prepares the presenter's demo
tenant for the opt-in LIVE paths:

- live read-only Fabric provider;
- Fabric MCP `fabric-readonly` profile;
- reference notebooks;
- the gated scoped writer.

Every step below is read-only, except the ones marked **(change)**. Do a **(change)** step
yourself in the portal, as the tenant administrator, after reviewing it. Nothing in this
repository makes these changes for you.

## 1. Check first

```bash
az login --tenant <TENANT_ID>          # the demo tenant admin account; never the default tenant
ffia fabric readiness --tenant <TENANT_ID>
```

`ffia fabric readiness` makes only GET requests and token requests. It reports PASS, WARN, FAIL or
SKIPPED, with a remediation for each check:

| Check | What it reads | Typical failure and fix |
|---|---|---|
| Pinned tenant | The bindings file or `--tenant` | WARN without a bindings file: see step 6 |
| Azure CLI sign-in | A Fabric token for the pinned tenant | Session expired, or the cached account belongs to another tenant (`AADSTS90072`): run `az login --tenant <TENANT_ID>` |
| Fabric API access | `GET /v1/workspaces` | `401 UserNotLicensed`: see step 2 |
| Fabric capacity | `GET /v1/capacities` | No active capacity: see step 3 |
| Bound workspace | The workspace list | Not visible, or not on a capacity: see steps 5 and 6 |
| Tenant settings | `GET /v1/admin/tenantsettings` (admin only) | Disabled settings: see step 4. SKIPPED for non-admins |

The command fails fast. If `az` opens a browser, or hangs waiting for interactive sign-in, the
check stops after 30 seconds and asks you to sign in again.

## 2. Activate the account in Fabric — (change)

`401 UserNotLicensed` can appear even when Power BI plans are assigned. It means the account is
not active in the Fabric service yet.

1. Sign in once at the Fabric portal with the demo admin account.
2. Accept the Fabric (Free) license if prompted.
3. Confirm the account has a Fabric (Free), Power BI Pro or Premium Per User license.

## 3. Get capacity — (change)

A **Premium Per User** capacity (SKU `PP*`) does not count: it cannot host lakehouses or
notebooks. Readiness only accepts F, FT (trial) and P SKUs.

Choose one:

- **Fabric trial.** In the Fabric portal, open account manager → **Start trial**. The trial lasts
  60 days and is the fastest option. See the `fabric-trial` source.
- **F SKU.** In an Azure subscription of the demo tenant:
  1. Register the `Microsoft.Fabric` resource provider.
  2. Create an F2 or larger capacity.
  3. Add the demo admin account as a capacity administrator.
  4. Pause the capacity when it is not in use. F SKUs bill per CU-hour while running; for
     example, an F8 in Central US is 8 × the per-CU retail price, about $1.44/hour as of
     2026-10-07.

  Pause and resume with the Azure CLI:

  ```bash
  az rest --method post --url "https://management.azure.com/subscriptions/<SUB>/resourceGroups/<RG>/providers/Microsoft.Fabric/capacities/<NAME>/suspend?api-version=2023-11-01"
  az rest --method post --url "https://management.azure.com/subscriptions/<SUB>/resourceGroups/<RG>/providers/Microsoft.Fabric/capacities/<NAME>/resume?api-version=2023-11-01"
  ```

## 4. Tenant settings — (change, Fabric administrator)

The labs rely on these settings. Enable them for the whole tenant, or only for a lab security
group. Readiness matches each setting by name or by its portal title, because Microsoft does not
publish a stable catalog of setting names.

| Purpose | Portal setting (title may vary) | Required |
|---|---|---|
| Create Fabric items | Users can create Fabric items | Yes |
| Power BI Modeling MCP and DAX tools | XMLA endpoints | Yes |
| DAX reconciliation through `executeQueries` | Dataset Execute Queries REST API (Integration settings) | Yes |
| Git integration for workspaces | Users can synchronize workspace items with their Git repositories | Yes |
| Workspace sync with GitHub | Users can sync workspace items with GitHub repositories | No (needed for repo-first change, Pattern 20; HC-01 does not use it) |
| Copilot and Fabric data agents | Users can use Copilot, AI Agents and other AI experiences powered by Azure OpenAI | No |
| Ontology (PREVIEW), Power BI MCP endpoints (PREVIEW) | Users can create Ontology (preview) items; Power BI Model Context Protocol server endpoints (preview) | No, reported as informational and left off |

## 5. Dedicated dev workspace — (change)

1. Create a workspace for the labs, for example `ffia-dev`.
2. Assign it to the trial or F capacity (workspace settings → License info).
3. Never use a shared or production workspace.

## 6. Bind the workspace locally (git-ignored)

```bash
cp config/customers/example-healthcare.local.example.yaml config/customers/example-healthcare.local.yaml
# edit: tenant_id, workspaces.demo-dev.workspace_id, optional semantic_models.<profile>
ffia fabric readiness           # now reads the tenant from the bindings file
```

The `*.local.yaml` files are ignored by Git. Real identifiers never leave that file. Before any
commit, run `ffia privacy scan`.

## 7. Turn on live reads (opt-in)

```bash
FFIA_ENVIRONMENT=hybrid FFIA_FABRIC_LIVE=1 make run-api
FFIA_FABRIC_LIVE=1 pytest -m live tests/integration -q     # read-only smoke test
```

What each live result looks like:

- Results are labeled `LIVE`, with `cloud_operation_performed: true`.
- Lakehouse table lists are labeled `PREVIEW`, because that REST API is in preview.
- In `hybrid` mode, a failed read falls back to LOCAL data, and the fallback is labeled. Writes
  never fall back.

## 8. Live writes stay gated

The scoped writer supports only `create_lakehouse` and `create_notebook`. It is wired only when
all of these hold:

- `FFIA_ALLOW_LIVE_MUTATION=1` is set;
- `FFIA_FABRIC_LIVE=1` is set;
- the bindings file exists.

Every change then still needs a plan, policy approval, approval by a different person, and a live
duplicate re-check. It is verified and audited afterwards. Run it only against the dev workspace,
and only after you have reviewed the plan.

## Fabric MCP note

In a new, empty workspace, `onelake_list-workspaces` (Fabric MCP 1.4.0) returned an empty list,
while `core_search-catalog` found the workspace. Use `core_search-catalog` to discover workspaces,
and confirm with the Fabric portal.

## If the tenant cannot be made ready

Run the demo offline. Every act has a LOCAL or SIMULATED equivalent with the same teaching
objective; see [demo-continuity.md](demo-continuity.md). Present the live steps as documented
behavior, labeled **REQUIRES TENANT VALIDATION**. Never present them as observed results.
