"""Create a Foundry prompt agent that answers sales questions through a Fabric data agent.

The Fabric data agent tool (preview) runs with the signed-in user's identity (on-behalf-of), so
Fabric permissions and row-level security apply. Service principals are not supported for it.
"""

import sys

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    FabricDataAgentToolParameters,
    MicrosoftFabricPreviewTool,
    PromptAgentDefinition,
    ToolProjectConnection,
)
from azure.identity import AzureCliCredential

from fabric_foundry_accelerator.config.bindings import BindingsError, load_bindings
from fabric_foundry_accelerator.config.settings import Settings

INSTRUCTIONS = """You are the sales insights agent for a manufacturer (synthetic demo data).
Answer only questions about this sales data. For anything else (jokes, general knowledge, other
companies), reply in one sentence that you only answer questions about the governed sales data,
and do not call any tool.
For sales questions, always get numbers from the Fabric tool; never estimate them. Say which
measure you used. "Last month" means the last complete calendar month before today. Order dates
after today are a data-quality issue: exclude them from results and report them.
State target attainment as a percentage of target (for example, 143.1% of
target).
If the data looks wrong (duplicates, negative quantities, unmapped regions), say so instead of
hiding it. You cannot change data; propose fixes for a data steward instead."""


def main() -> None:
    """Create an approved agent version, then ask a synthetic question using private settings."""
    settings = Settings()
    bindings = load_bindings(settings.config_root, settings.overlay, settings=settings)
    if bindings is None or bindings.foundry is None:
        raise BindingsError(
            "Configure Azure, Fabric and Foundry variables in the ignored .env file"
        )
    foundry = bindings.foundry
    if not foundry.model_deployments or not foundry.fabric_connection:
        raise BindingsError("FOUNDRY_MODEL_DEPLOYMENT and FABRIC_CONNECTION_NAME are required")
    question = (
        " ".join(sys.argv[1:]) or "Which product line grew fastest last month, and by how much?"
    )
    project = AIProjectClient(
        endpoint=foundry.endpoint, credential=AzureCliCredential(tenant_id=bindings.tenant_id)
    )
    connection = project.connections.get(foundry.fabric_connection)
    agent = project.agents.create_version(
        agent_name="sales-insights-agent",
        definition=PromptAgentDefinition(
            model=foundry.model_deployments[0],
            instructions=INSTRUCTIONS,
            tools=[
                MicrosoftFabricPreviewTool(
                    fabric_dataagent_preview=FabricDataAgentToolParameters(
                        project_connections=[
                            ToolProjectConnection(project_connection_id=connection.id)
                        ]
                    )
                )
            ],
        ),
    )
    sys.stdout.write("[LIVE] Agent version created\n")
    openai = project.get_openai_client(agent_name=agent.name)
    # "auto": the agent decides; the evaluation suite checks that sales answers are grounded.
    response = openai.responses.create(tool_choice="auto", input=question)
    sys.stdout.write(f"[PREVIEW] Fabric data agent response\n{response.output_text}\n")


if __name__ == "__main__":
    main()
