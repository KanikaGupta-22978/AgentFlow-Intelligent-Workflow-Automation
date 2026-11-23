from app.plugins.email_plugin import EmailPlugin


def main():
    email = EmailPlugin()

    email_data = {
        "recipient": "admin@example.com",
        "subject": "Network Alert Notification",
        "message": "A high latency alert has been detected on the network."
    }

    result = email.execute(email_data)

    print("===== EMAIL PLUGIN TEST =====")
    print("SUCCESS:", result["success"])
    print("PLUGIN:", result["plugin"])
    print("RECIPIENT:", result["recipient"])
    print("SUBJECT:", result["subject"])
    print("MESSAGE:", result["message"])


if __name__ == "__main__":
    main()