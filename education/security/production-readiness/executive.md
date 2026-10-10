## Business outcome and accountability

Use this accelerator to learn and demonstrate a governed integration, not to certify production.
Fabric owns governed business context; Foundry reasons over it. Models propose, policy constrains,
humans approve and a narrow service writes. A successful demo does not transfer that authority.

Customization starts with a fictional industry overlay and synthetic data. The baseline stays
unchanged; real customer source material and environment identifiers remain outside Git.
An overlay can restrict permissions, never remove approvals or expand the global policy.

## Risk, release and cost

The main threats are injected instructions in tool output, excessive privileges, leaked secrets,
incorrect business numbers and forged evidence. Repository controls include narrow MCP tools,
approval gates, execution labels, baseline evaluation and privacy scanning. Production also needs
authenticated users, protected audit storage, negative access tests and security ownership.

Git review and CI gate release artifacts on tests, types, privacy, dependency checks and evaluation.
CodeQL scans and SBOMs provide additional evidence, not a guarantee. Publication is human-reviewed.
Budget alerts, quotas and a capacity operating schedule reduce exposure; caps do not guarantee
a maximum bill. Copilot subscriptions, model consumption and Fabric capacity are separate costs.

Ask the owner to show actual results, remaining tenant checks and rollback plans before go-live.
Claude Code is documented-only; recorded Copilot model comparisons do not evaluate that product.

## Three reusable production patterns

P14 secures the deployment through appropriate network isolation, identity and protected secrets.
P15 introduces an API Management gateway when multiple consumers need shared quotas, routing or
tool governance; it adds cost and latency and is not automatically necessary for a single app.
The backend must still authorize access after gateway authentication. P18 reuses the same core
through overlays rather than customer-specific forks. Each pattern needs its own evidence:
access-denial tests, observed gateway policy results and an overlay that cannot widen authority.
