# Policies

Use these policies to limit tools, require write approval and control fallback behavior.
Write approval is tied to a destination and expires.

The server checks the applicable policy before a tool or provider call.
MCP access does not grant write authority.
See [the approval flow](../../docs/architecture/control-plane.md).

## Notebook diagnostics and runs

`inspect_notebook_runtime` and `run_notebook` describe separate operations on an existing
Notebook. They are not notebook creation or publication. A diagnostic may consume Spark
capacity even when it writes no data; a run can overwrite several tables without an atomic
rollback across them.

Both are disabled in the default customer overlays. An explicitly reviewed overlay must
allow the operation and retain its human approval rule. LIVE also requires the existing live
mutation gate, exact target checks and a supporting authorized executor. Policy definitions
are planning support, not an executor: the current API live writer does not support these
operations and returns `UNAVAILABLE`, never a LOCAL substitute.

For an approved native-extension workflow, verify the remote kernel and exact source/binding,
check active/recent execution, and obtain separate approval before each diagnostic or run.
Do not use generic shell/REST execution or rename an operation to bypass policy.
LOCAL execution is only an item-level SIMULATED approval rehearsal, not Spark execution or
proof of table outputs.
