## Why it matters

Most organizations want one thing from enterprise AI: an assistant that answers questions from
**trusted data** and can **help get work done** without creating a new, unaccountable path to
change business systems. Pattern P06 is the anchor design for that assistant.

Each layer has one job, and none of them does another layer's job:

| Layer | Owns | Leaders should ask |
|---|---|---|
| Microsoft Fabric | Governed business context: curated data, definitions, security | Is the data the agent reads already certified? |
| Microsoft Foundry | Reasoning, orchestration, evaluation, tracing | How do we know answers are grounded and safe? |
| MCP | Standard access to tools | Which tools may the agent use at all? |
| Entra identity and policy | Authority | Whose permissions does the agent use? |
| People and business systems | Approval and the system of record | Who accepts the risk of an action? |

**The value:** answers reuse the governance you already invested in Fabric, and actions reuse
your approval model instead of bypassing it. **The risk to manage:** an agent that can reach a
tool is not authorized to use it — authority comes from identity and policy, and high-impact
actions always need a person (pattern P08).

## What is GA and what is preview (as of October 2026)

| Building block | Status |
|---|---|
| Foundry Agent Service, Agent Framework, tracing, core evaluators | GA |
| Fabric data agents, semantic models, lakehouses | GA |
| Foundry tool that calls a Fabric data agent; Fabric IQ tool | PREVIEW |

The pattern is therefore **MIXED**: a production design can be built on GA parts today, with the
preview tools added behind a feature flag when they reach GA.

> In this accelerator the offline demo runs the context, access, approval and evidence parts
> **SIMULATED LOCALLY**. The agent step is answered by a deterministic local agent over synthetic
> sales data, labeled **LOCAL** - a teaching analog, not a language model and never presented as
> Foundry. A live Foundry agent is opt-in; the routed live path still **REQUIRES TENANT VALIDATION**.
