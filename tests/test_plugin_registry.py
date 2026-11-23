
from app.database.connection import SessionLocal
from app.plugins.plugin_registry import PluginRegistry


def main():
    db = SessionLocal()

    try:
        registry = PluginRegistry(db)

        print("===== PLUGIN REGISTRY TEST =====")

        print("REGISTERED PLUGINS:", registry.list_plugins())

        # Test Jira plugin
        jira_result = registry.execute_plugin(
            "jira",
            {
                "title": "Network Connection Issue",
                "description": "Network connection failure detected."
            }
        )

        print("\nJIRA RESULT:", jira_result)

        # Test Email plugin
        email_result = registry.execute_plugin(
            "email",
            {
                "recipient": "admin@example.com",
                "subject": "Network Alert",
                "message": "A network issue has been detected."
            }
        )

        print("\nEMAIL RESULT:", email_result)

    finally:
        db.close()


if __name__ == "__main__":
    main()
