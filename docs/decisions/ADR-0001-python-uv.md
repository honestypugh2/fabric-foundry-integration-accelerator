# ADR-0001: Python 3.14 with uv

- Status: Accepted
- Date: 2026-10-05

## Context

The backend needs one Python runtime and package manager that every required library
supports. The goals are reproducible installs, fast environment creation and strict typing.
The brief requires uv, `pyproject.toml`, a committed `uv.lock`, the newest stable Python that
every dependency supports, and an activated virtual environment before any install.

## Options

1. Python 3.14 + uv
2. Python 3.13 + uv
3. Python 3.12 + pip/pip-tools

## Decision

Use **Python 3.14** (`requires-python = ">=3.14,<3.15"`) managed by **uv 0.12.23**:

- the `uv_build` backend;
- exact `==` pins;
- a committed `uv.lock`;
- installs only after `uv venv` and `source .venv/bin/activate`.

## Rationale

- Python 3.13 moved to security-only support on 2026-10-01. Python 3.14 receives bugfixes until
  2027-10.
- The full planned dependency set resolved under Python 3.14 in Phase 0: 178 packages,
  0 known vulnerabilities from `pip-audit`. A smoke test passed for FastMCP, Agent Framework
  and Pyright.
- uv gives deterministic locks, fast installs and managed Python versions.

## Trade-offs

- `fabric-cicd`, `ms-fabric-cli` and `fabric-data-agent-sdk` declare Python below 3.14.
  - They are excluded from the project environment.
  - When needed, they run as isolated tools on Python 3.13, for example
    `uv tool install --python 3.13 ms-fabric-cli==1.7.0`.
- uv ignores dependency upper bounds on `Requires-Python`. Reviewers must check new
  dependencies (CI check planned for Phase 8).

## Security impact

- Exact pins plus a lockfile let `pip-audit` audit an exact, reproducible dependency set. CI
  fails on HIGH/CRITICAL findings.

## Operations impact

- Contributors need uv 0.12.23+.
- CI uses `astral-sh/setup-uv`, pinned by commit SHA, with `uv sync --frozen`.

## Offline impact

- After `uv sync`, no network access is needed to run tests or the offline demo.

## Education impact

- Labs teach uv workflows (`uv venv`, activate, `uv sync`, `uv add pkg==x.y.z`). These match
  Microsoft and Astral documentation.

## Revisit trigger

- Python 3.15 GA with full dependency support.
- A required Microsoft SDK dropping 3.14 support.
- A uv breaking change.

## Authoritative references

- `python-lifecycle` in `docs/research/sources.yaml`
- uv documentation: <https://docs.astral.sh/uv/>
