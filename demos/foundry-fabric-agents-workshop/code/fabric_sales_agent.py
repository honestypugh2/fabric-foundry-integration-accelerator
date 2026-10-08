"""Create a Foundry prompt agent that answers sales questions through a Fabric data agent.

The Fabric data agent tool (preview) runs with the signed-in user's identity (on-behalf-of), so
Fabric permissions and row-level security apply. Service principals are not supported for it.
"""

import os
import sys

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    FabricDataAgentToolParameters,
    MicrosoftFabricPreviewTool,
    PromptAgentDefinition,
    ToolProjectConnection,
)
from azure.identity import DefaultAzureCredential

INSTRUCTIONS = """You are the sales insights agent for a manufacturer (synthetic demo data).
Always get numbers from the Fabric tool; never estimate them. Say which measure you used.
If the data looks wrong (duplicates, negative quantities, unmapped regions), say so instead of
hiding it. You cannot change data; propose fixes for a data steward instead."""


def main() -> None:
    question = " ".join(sys.argv[1:]) or "Which product line grew fastest last month, and by how much?"
    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential()
    )
    connection = project.connections.get(os.environ["FABRIC_CONNECTION_NAME"])
    agent = project.agents.create_version(
        agent_name="sales-insights-agent",
        definition=PromptAgentDefinition(
            model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
            instructions=INSTRUCTIONS,
            tools=[
                MicrosoftFabricPreviewTool(
                    fabric_dataagent_preview=FabricDataAgentToolParameters(
                        project_connections=[ToolProjectConnection(project_connection_id=connection.id)]
                    )
                )
            ],
        ),
    )
    print(f"[LIVE] agent {agent.name} version {agent.version}")
    openai = project.get_openai_client(agent_name=agent.name)
    response = openai.responses.create(tool_choice="required", input=question)
    print(response.output_text)


if __name__ == "__main__":
    main()
