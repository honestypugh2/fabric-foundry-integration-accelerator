"""Write one monthly brief per business team focus area with the sales insights agent.

Run fabric_sales_agent.py once first (it creates the agent). In production, a Logic Apps
Recurrence trigger or a Foundry routine starts this, and a Teams or Outlook connector delivers it.
"""

import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

TEAMS = {
    "Structural & Metals": "product lines STR and MET",
    "Enclosures": "product line ENC",
    "Hardware & Fabrication": "product lines FAS and FAB",
    "Key Accounts": "the Key Account customer segment",
}
PROMPT = """Write the monthly brief for the {team} team, whose focus is {focus}, for last month.
Use the Fabric tool for: booked revenue, change vs the previous month and the same month last year,
target attainment, gross margin, and the fastest-growing product. Then give three plain-language
insights and one recommended action. Flag any data-quality issue that affects these numbers.
Keep it under 200 words. Label the numbers as synthetic demonstration data."""


def main() -> None:
    project = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"], credential=DefaultAzureCredential()
    )
    openai = project.get_openai_client(agent_name="sales-insights-agent")
    for team, focus in TEAMS.items():
        response = openai.responses.create(tool_choice="required", input=PROMPT.format(team=team, focus=focus))
        print(f"\n=== {team} [LIVE]\n{response.output_text}")


if __name__ == "__main__":
    main()
