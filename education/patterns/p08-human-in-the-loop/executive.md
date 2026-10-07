## Why it matters

AI agents are now good at *proposing* changes: create a lakehouse, update a semantic model, publish
a report. The risk is not that the proposal is wrong — it is that a plausible proposal gets
**executed without anyone accountable deciding it should be**.

Pattern P08 keeps the speed of AI and the accountability of your operating model:

| Step | Who | Outcome |
|---|---|---|
| Propose | The agent | A written plan: what, where, risk, rollback |
| Validate | Deterministic rules | Policy, duplicates and permissions checked the same way every time |
| Approve | An accountable person | Recorded decision, never the requester |
| Execute | A narrowly scoped service | Only the approved change, only on the approved target |
| Verify and audit | The platform | Evidence that the change happened as approved |

**Decision for leaders:** which changes need a human, and who is accountable for approving them.
Everything else in this pattern is engineering.

> Status: the pattern uses GA building blocks. In this accelerator the flow runs **SIMULATED
> LOCALLY**; live Fabric writes need an authorized writer that is added later.
