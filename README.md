# AgentFlow — Intelligent Workflow Automation

AgentFlow is a web-based workflow automation platform for operational tasks. It combines a FastAPI backend, LangGraph-based natural-language workflow selection, configurable integrations, scheduled jobs, and a browser dashboard for execution results and history.

- **Live application:** https://agentflow-intelligent-workflow-automation.onrender.com
- **Source code:** https://github.com/KanikaGupta-22978/AgentFlow-Intelligent-Workflow-Automation

## Features

- **Natural-language workflow execution:** Submit an instruction and let the workflow-selection agent identify the relevant workflow. A rule-based fallback is available when Gemini cannot be used.
- **LangGraph orchestration:** Coordinates workflow selection, parameter extraction/validation, and execution.
- **Four predefined workflows:** Daily alert summary, Jira ticket creation, email notification, and network performance reporting.
- **Jira integration:** WF002 creates issues through the Jira REST API. Duplicate checks are performed before issue creation.
- **Email integration:** WF003 sends transactional email through the Brevo API.
- **Performance reporting:** WF004 filters records by zone and optional reporting duration, calculates average performance, and lists records identified as DOWN by zero uptime.
- **Compound workflow:** A performance report request can also request a Jira incident and/or email delivery of the report.
- **Dynamic workflows:** Create and manage reusable workflow definitions with conditional steps.
- **Scheduling:** APScheduler-backed schedule management for supported workflow types, using the Asia/Kolkata timezone.
- **Execution history and dashboard:** Review execution status, inputs, outputs, activity summaries, and workflow distribution.
- **Plugin architecture:** External integrations are isolated behind plugin components.
- **REST API:** FastAPI endpoints expose workflow, scheduler, dynamic workflow, and execution-history capabilities.

## Workflow catalogue

| ID | Workflow | What it does |
|---|---|---|
| WF001 | Daily Alert Summary | Summarizes unacknowledged DOWN and HIGH alerts. |
| WF002 | Jira Ticket Creation | Creates an issue in the configured Jira project and records the returned issue details. |
| WF003 | Email Notification | Sends an email using the configured Brevo transactional email account. |
| WF004 | Performance Report | Filters network performance records by zone and optional reporting duration, calculates the average performance score, and lists DOWN links. |
| WF004+COMPOUND | Report and follow-up actions | Generates a performance report and performs explicitly requested Jira and/or email actions. |

## WF004 data interpretation

The supplied performance dataset contains records with and without individual timestamps.

- When no duration is requested, WF004 uses all records matching the requested zone (or all zones if no zone is specified).
- When a duration is requested, only records with valid timestamps inside the requested reporting interval are included.
- Records with missing or invalid timestamps, and records outside the requested interval, are excluded from time-filtered calculations and counted separately in the result.
- A DOWN link is identified from a record whose `uptime` value is zero.

Report totals and averages describe only the records included after the requested zone and time filters have been applied. The supplied dataset is a static demonstration dataset; it should not be interpreted as live network telemetry.

## Technology stack

| Area | Technology |
|---|---|
| Backend/API | Python, FastAPI |
| Agent orchestration | LangGraph |
| Natural-language model | Google Gemini API |
| Persistence | SQLite, SQLAlchemy |
| Scheduling | APScheduler |
| Frontend | HTML, CSS, JavaScript |
| Integrations | Jira REST API, Brevo transactional email API |
| Tests | Pytest |
| Hosting | Render |

## Architecture overview

```text
Browser dashboard / Natural-language instruction
                    |
                    v
               FastAPI API
                    |
          Workflow selection agent
             (LangGraph / Gemini)
                    |
        Parameter extraction/validation
                    |
                    v
             Workflow service
          /       |       |       \
       WF001    WF002   WF003    WF004
                 |       |         |
               Jira    Brevo   Report data
                    |
                    v
          Execution history database

       APScheduler ----> Workflow service
```

## Run locally

### 1. Clone the repository

```bash
git clone https://github.com/KanikaGupta-22978/AgentFlow-Intelligent-Workflow-Automation.git
cd AgentFlow-Intelligent-Workflow-Automation
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a private `.env` file in the project root. Configure only the integrations you intend to use:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_supported_gemini_model

JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-jira-account-email
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY

BREVO_API_KEY=your_brevo_api_key
EMAIL_SENDER=your-verified-sender@example.com
```

Use a Gemini model supported by your account. The sender address must be verified with Brevo, and the Jira account must have permission to create issues in the selected project.

**Never commit `.env`, API keys, passwords, or tokens.** Keep secrets in your local environment or your hosting provider's secret/environment-variable settings. The committed `.env.example` contains placeholders only.

### 5. Start the application

```bash
uvicorn app.main:app --reload
```

Open:

- Dashboard: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health

## Tests

Run the automated test suite:

```bash
python -m pytest -q
```

**Latest recorded local result:** 35 passed.

A manual WF004 inspection script is also available at `tests/test_performance_report_workflow.py`:

```bash
python tests/test_performance_report_workflow.py
```

## Demonstration guide

1. Open the live dashboard and confirm the backend connection.
2. Run WF001 and inspect the unresolved DOWN/HIGH alert summary.
3. Run WF002 with a test incident and confirm the created issue in Jira. Avoid creating duplicate production tickets during repeated demonstrations.
4. Run WF003 with a test recipient and confirm receipt of the email.
5. Run WF004 for a selected zone and duration; inspect the metrics, DOWN-link table, reporting period, and timestamp-exclusion counts.
6. Run an all-zones report without a time filter and inspect the aggregate metrics.
7. Submit a natural-language instruction and inspect the selected workflow and execution result.
8. Review the execution-history entry and its details.
9. In Scheduler Management, create a non-disruptive test schedule, verify its next-run time, and confirm its execution-history entry after it triggers. Remove temporary test schedules after verification.
10. If demonstrating dynamic workflows, create and execute a representative workflow definition and inspect its execution result.

## Verification record

The following checks have been completed and recorded during project development:

- **Automated tests:** 35 tests passed locally after the all-zones regression test was added.
- **Jira:** Real Jira REST API issue creation was verified. Duplicate detection was also exercised against an existing issue; the duplicate case did not create another issue.
- **Email:** Real Brevo email delivery was verified by receipt of the message.
- **Compound workflow:** A performance report request combining Jira incident handling and email delivery was executed. The report and email succeeded; the Jira duplicate check correctly identified an existing matching issue.
- **Scheduler:** The Asia/Kolkata timezone configuration was checked. A short-interval WF001 schedule executed successfully, and the weekly Monday 9:00 AM IST schedule's next-run time was checked in the interface. A future scheduled trigger should be re-demonstrated if required for formal acceptance.
- **WF004 local and production:** The all-zones request was verified locally and on the deployed Render application.

### Latest all-zones production report

The deployed application was checked with the instruction:

```text
Generate a performance summary report for all zones using all available records, without applying any time filter.
```

Observed production result:

| Metric | Result |
|---|---:|
| Zone | All zones |
| Total records | 157 |
| Average performance score | 60.44 |
| DOWN links | 52 |

The report's detailed DOWN Links table rendered in the live application, and the dashboard reported a successful backend connection.

The supplied dataset is static demonstration data, not live network monitoring. These figures describe the current contents of that dataset and may change if the dataset is updated.

## Repository layout

```text
app/
  agents/          # Workflow and plugin selection agents
  api/             # FastAPI route modules
  database/        # SQLAlchemy connection and models
  plugins/         # Jira, email, and plugin registry
  services/        # Workflow execution, data loading, scheduler services
  main.py
frontend/
  index.html
  static/
    script.js
    style.css
data/               # Supplied alert and performance datasets
tests/              # Automated and manual test utilities
requirements.txt
.env.example
.gitignore
README.md
```

## Deployment

The production dashboard is hosted on Render:

https://agentflow-intelligent-workflow-automation.onrender.com

Configure production secrets in the Render service's environment settings. Do not store credentials in source files or commit them to GitHub. The repository's `master` branch is configured for automatic deployment; confirm the deployment event in Render after pushing a change.

## Security and operational notes

- Keep all API credentials in environment variables or the hosting provider's secret store.
- Use placeholder values only in `.env.example`.
- Use test recipients and non-production sample incidents when demonstrating integrations.
- Review execution history after running workflows, especially when a workflow sends email or creates external tickets.
- Treat the included network dataset as sample data unless it is replaced with a trusted live data source.

## Project status

The application, four predefined workflows, integrations, reporting fix, automated regression coverage, and latest production deployment have been completed and verified as described above. Any additional acceptance checks for dynamic workflow execution or a future scheduler trigger should be demonstrated against the evaluator's required scenarios.
