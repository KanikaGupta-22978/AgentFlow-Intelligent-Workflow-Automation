
from pathlib import Path
from dotenv import load_dotenv

from app.database.connection import SessionLocal
from app.plugins.jira_plugin import JiraPlugin


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def main():
    db = SessionLocal()

    try:
        jira = JiraPlugin(db)

        ticket_data = {
            "title": "Network Alert - High Latency",
            "description": "High latency detected on device 240004-MECCCA-SD-3057."
        }

        result = jira.execute(ticket_data)

        print("\n===== JIRA PLUGIN TEST =====")
        print("SUCCESS:", result.get("success"))
        print("PLUGIN:", result.get("plugin"))
        print("MESSAGE:", result.get("message"))

        if result.get("success"):
            print("LOCAL TICKET ID:", result.get("ticket_id"))
            print("JIRA ISSUE KEY:", result.get("jira_issue_key"))
            print("JIRA ISSUE URL:", result.get("jira_issue_url"))
            print("STATUS:", result.get("status"))

    finally:
        db.close()


if __name__ == "__main__":
    main()
