"""Export real control-plane responses as frontend test fixtures.

Run after changing API models or education content:

    source .venv/bin/activate && python -m tests.contract.export_frontend_fixtures

The responses come from the real FastAPI app over the offline container, so frontend tests mock
fetch with data that matches the backend contract. ``tests/contract/test_frontend_fixtures.py``
validates the committed fixtures against the Pydantic models.
"""

import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from fabric_foundry_accelerator.api.app import create_app
from fabric_foundry_accelerator.config.settings import Settings
from fabric_foundry_accelerator.services.container import build_container

FIXTURES = Path("frontend/src/test/fixtures")
GUIDE = "hc-01-fabric-mcp-powerbi-medallion-lab"
LESSON = "p08-human-in-the-loop"
LAKEHOUSE = "local-lh-hc-lab-7file-v1"


def _write(name: str, payload: object) -> None:
    (FIXTURES / f"{name}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    """Export every fixture the frontend tests use."""
    FIXTURES.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as runtime:
        settings = Settings(audit_path=None, runtime_root=Path(runtime))
        with TestClient(create_app(build_container(settings))) as client:
            gets = {
                "runtime-status": "/api/v1/runtime/status",
                "demo-status": "/api/v1/demo/status",
                "patterns": "/api/v1/patterns",
                "pattern-p08": "/api/v1/patterns/P08",
                "signals": "/api/v1/patterns/signals",
                "guides": "/api/v1/guides",
                "guide-hc01": f"/api/v1/guides/{GUIDE}",
                "lessons": "/api/v1/education/lessons",
                "lesson-p08": f"/api/v1/education/lessons/{LESSON}",
                "labs": "/api/v1/education/labs",
                "lab-governed-change": "/api/v1/education/labs/lab-governed-change",
                "architecture": "/api/v1/education/architecture",
                "completeness": "/api/v1/education/completeness",
                "profiles": "/api/v1/profiles",
                "views": "/api/v1/education/views",
                "view-reference": "/api/v1/education/views/reference",
                "view-system": "/api/v1/education/views/system",
                "view-hc01": "/api/v1/education/views/hc-01",
                "view-system-runtime": "/api/v1/education/views/system/runtime",
                "agent-profile": "/api/v1/agents/sales-insights-agent",
                "bakeoff-tasks": "/api/v1/bakeoff/tasks",
                "bakeoff-scorecard": "/api/v1/bakeoff/scorecard",
            }
            for name, path in gets.items():
                response = client.get(path)
                response.raise_for_status()
                _write(name, response.json())
            reads = {
                "read-workspaces": {"operation": "list_workspaces"},
                "read-items": {"operation": "list_items", "workspace_id": "local-ws-synthetic"},
                "read-tables": {"operation": "list_tables", "lakehouse_id": LAKEHOUSE},
                "read-preview": {
                    "operation": "read_table",
                    "lakehouse_id": LAKEHOUSE,
                    "table": "silver_patients",
                    "limit": 3,
                },
            }
            for name, body in reads.items():
                response = client.post("/api/v1/fabric/read", json=body)
                response.raise_for_status()
                _write(name, response.json())
            lesson = client.get(f"/api/v1/education/lessons/{LESSON}").json()
            check = lesson["checks"][0]["id"]
            _write(
                "check-grade",
                client.post(
                    f"/api/v1/education/lessons/{LESSON}/checks/{check}", json={"choice": 1}
                ).json(),
            )
            _write(
                "recommend",
                client.post(
                    "/api/v1/patterns/recommend", json={"needs": ["business-system-write"]}
                ).json(),
            )
            _write(
                "evaluation",
                client.post(
                    "/api/v1/evaluations/run",
                    json={"profile": "hc-lab-7file-v1", "observed_label": "LOCAL"},
                ).json(),
            )
            plan = client.post(
                "/api/v1/plans",
                json={
                    "operation": "create_lakehouse",
                    "target": {
                        "workspace_alias": "demo-dev",
                        "item_type": "Lakehouse",
                        "item_name": "healthcare_lakehouse",
                        "destination": "LOCAL",
                    },
                    "reason": "Rehearsal of guide step: Create and confirm the lakehouse",
                    "requested_by": "engineer-a",
                },
            ).json()
            _write("plan", plan)
            approval = client.post(
                "/api/v1/approvals",
                json={
                    "change_id": plan["change_id"],
                    "approver": "approver-b",
                    "decision": "APPROVED",
                },
            ).json()
            _write("approval", approval)
            _write(
                "execution",
                client.post(
                    "/api/v1/fabric/change",
                    json={
                        "change_id": plan["change_id"],
                        "approval_id": approval["approval_id"],
                        "executed_by": "scoped-writer",
                    },
                ).json(),
            )
            _write("audit", client.get(f"/api/v1/audit/{plan['correlation_id']}").json())
            _write("demo-run", client.post("/api/v1/demo/run").json())
            for name, question in {
                "agent-answer": "Which product line grew fastest last month?",
                "agent-unsupported": "Tell me a joke about steel beams.",
            }.items():
                response = client.post("/api/v1/agents/ask", json={"question": question})
                response.raise_for_status()
                _write(name, response.json())
            _write("agent-eval", client.post("/api/v1/agents/evaluate").json())
            _write(
                "knowledge-unavailable",
                client.post(
                    "/api/v1/knowledge/search", json={"question": "Are briefs sent automatically?"}
                ).json(),
            )
            _write(
                "agent-workflow",
                client.post("/api/v1/agents/workflows/monthly-insights", json={}).json(),
            )
        preview = Settings(
            audit_path=None, runtime_root=Path(runtime), preview_features=("foundry_iq_knowledge",)
        )
        with TestClient(create_app(build_container(preview))) as client:
            _write(
                "knowledge-simulated",
                client.post(
                    "/api/v1/knowledge/search",
                    json={"question": "Can agents fix data quality issues in the source?"},
                ).json(),
            )
    print(f"exported fixtures to {FIXTURES}")  # noqa: T201


if __name__ == "__main__":
    main()
