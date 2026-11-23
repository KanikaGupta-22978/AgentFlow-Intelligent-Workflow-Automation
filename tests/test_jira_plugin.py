
from app.database.connection import SessionLocal
from app.plugins.jira_plugin import JiraPlugin


def main():
    db = SessionLocal()

    try:
        jira = JiraPlugin(db)

        ticket_data = {
            "title": "Network Alert - High Latency",
            "description": "High latency detected on device 240004-MECCCA-SD-3057."
        }

        result = jira.execute(ticket_data)

        print("===== JIRA PLUGIN TEST =====")
        print("SUCCESS:", result["success"])
        print("PLUGIN:", result["plugin"])
        print("TICKET ID:", result["ticket_id"])
        print("TITLE:", result["title"])
        print("STATUS:", result["status"])
        print("MESSAGE:", result["message"])

    finally:
        db.close()


if __name__ == "__main__":
    main()
