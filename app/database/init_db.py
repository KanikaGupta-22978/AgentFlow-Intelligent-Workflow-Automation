
from sqlalchemy import inspect, text

from app.database.connection import Base, engine
from app.database import models


def initialize_database():
    # Create tables that do not already exist
    Base.metadata.create_all(bind=engine)

    # Check existing Jira table columns
    inspector = inspect(engine)
    existing_columns = {
        column["name"]
        for column in inspector.get_columns("jira_tickets")
    }

    # Add new columns without deleting existing ticket records
    with engine.begin() as connection:

        if "jira_issue_key" not in existing_columns:
            connection.execute(
                text(
                    "ALTER TABLE jira_tickets "
                    "ADD COLUMN jira_issue_key VARCHAR(50)"
                )
            )

        if "jira_issue_url" not in existing_columns:
            connection.execute(
                text(
                    "ALTER TABLE jira_tickets "
                    "ADD COLUMN jira_issue_url VARCHAR(500)"
                )
            )

    print("Database tables and Jira columns initialized successfully!")


if __name__ == "__main__":
    initialize_database()
