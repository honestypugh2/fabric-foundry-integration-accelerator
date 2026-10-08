"""Add public market context with the web search tool, with citations.

Web search uses Grounding with Bing. Queries leave the Azure compliance and geo boundary and follow
Bing's terms of use, so never put confidential data in a query. For production, restrict results to
allow-listed domains with a Bing Custom Search connection (see the web search tool documentation).
"""

import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, WebSearchTool
from azure.identity import DefaultAzureCredential

INSTRUCTIONS = """You summarize public market information for a manufacturer's sales team.
Use only what the web search tool returns and cite every source URL. Do not speculate about any
company's non-public information. Never include internal sales figures in a search query."""


def main() -> None:
    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential()
    )
    agent = project.agents.create_version(
        agent_name="market-context-agent",
        definition=PromptAgentDefinition(
            model=os.environ["FOUNDRY_MODEL_DEPLOYMENT"], instructions=INSTRUCTIONS, tools=[WebSearchTool()]
        ),
    )
    openai = project.get_openai_client(agent_name=agent.name)
    response = openai.responses.create(
        tool_choice="required",
        input="Summarize this month's public news on steel prices that affect enclosure manufacturers.",
    )
    print("[LIVE] web-grounded answer (check the citations):\n" + response.output_text)


if __name__ == "__main__":
    main()
