# Live integration tests (opt-in)

Marked `live`; require explicit environment variables; read-only by default; mutation requires
`live_mutation` plus `FFIA_ALLOW_LIVE_MUTATION=1`. Never run in default CI.

| Test | Needs | Does |
|---|---|---|
| `test_fabric_live_readonly.py` | `az login --tenant <TENANT_ID>`, `FFIA_FABRIC_LIVE=1`, `config/customers/<overlay>.local.yaml` | Runs `ffia fabric readiness` checks and lists workspaces (GET only) |

```bash
FFIA_FABRIC_LIVE=1 pytest -m live tests/integration -q
```

There is no `live_mutation` test: live writes are performed only through the approved change flow
by a person, never by a test run.
