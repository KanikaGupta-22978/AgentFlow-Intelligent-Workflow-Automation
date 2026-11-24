# AgentFlow — Intelligent Workflow Automation

AgentFlow is a web-based workflow automation platform for operational tasks. It combines a FastAPI backend, LangGraph-based natural-language workflow selection, configurable integrations, scheduled jobs, and a browser dashboard for execution results and history.

**Live application:** https://agentflow-intelligent-workflow-automation.onrender.com  
**Source code:** https://github.com/KanikaGupta-22978/AgentFlow-Intelligent-Workflow-Automation

## Features

- **Natural-language workflow execution:** Submit an instruction and let the workflow-selection agent identify the relevant workflow. A rule-based fallback is available when Gemini cannot be used.
- **LangGraph orchestration:** Coordinates workflow selection, parameter extraction/validation, and execution.
- **Four predefined workflows:** Daily alert summary, Jira ticket creation, email notification, and network performance reporting.
- **Real integrations:** WF002 creates Jira issues through the Jira REST API. WF003 sends transactional email through the Brevo API. Both require valid environment configuration.
- **Performance reporting:** WF004 filters records by zone and, where timestamps are available, by reporting period. It reports average performance and lists records identified as DOWN by zero uptime.
- **Dynamic workflows:** Create and manage reusable workflow definitions with conditional steps.
- **Scheduling:** APScheduler-backed schedule management for supported workflow types.
- **Execution history and dashboard:** Review execution status, inputs, outputs, activity summaries, and workflow distribution.
- **Plugin architecture:** External integrations are isolated behind plugin components.
- **REST API:** FastAPI endpoints expose workflow, scheduler, and execution-history capabilities.

## Workflow catalogue

| ID | Workflow | What it does |
|---|---|---|
| WF001 | Daily Alert Summary | Collects alerts and summarizes unacknowledged DOWN and HIGH alerts. |
| WF002 | Jira Ticket Creation | Creates an issue in the configured Jira project and records the returned issue details. |
| WF003 | Email Notification | Sends an email using the configured Brevo transactional email account. |
| WF004 | Performance Report | Filters network performance records by zone and optional reporting duration, calculates the average performance score, and lists DOWN links. |

### WF004 data interpretation

The supplied performance dataset contains records with and without individual timestamps. When a duration is requested, WF004 filters timestamped records to the requested interval and retains undated records because their period cannot be verified. In that case, the result marks time filtering as partial and explains the limitation in `time_filter_note`.

A DOWN link is identified from a record whose `uptime` value is zero. The report's total record and DOWN-link counts therefore describe the records retained after the zone and available timestamp filtering rules have been applied; they should not be interpreted as proof that an undated record was DOWN during a specific sub-period.

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
                 |       |
               Jira    Brevo
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

Create a private `.env` file in the project root. Set only the integrations you intend to use:

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

Use the actual model configured for your Gemini account. The sender address must be verified with Brevo, and the Jira account must have permission to create issues in the selected project.

**Never commit `.env`, API keys, passwords, or tokens.** Keep secrets in your local environment or your hosting provider's secret/environment-variable settings. The repository's `.env.example` should contain placeholders only.

### 5. Start the application

```bash
uvicorn app.main:app --reload
```

Open:

- Dashboard: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs

## Tests

Run the automated test suite:

```bash
python -m pytest -q
```

The project had **27 passing tests** in the local verification recorded before the latest documentation and regression-test update. Run the command again after pulling the latest commit to verify the current repository state.

A manual WF004 inspection script is also available at `tests/test_performance_report_workflow.py`; run it directly with:

```bash
python tests/test_performance_report_workflow.py
```

## Demonstration checklist

1. Open the live dashboard and confirm the backend connection.
2. Run WF001 and inspect the unresolved DOWN/HIGH alert summary.
3. Run WF002 with a test incident and confirm the created issue in Jira.
4. Run WF003 with a test recipient and confirm receipt of the email.
5. Run WF004 for a selected zone and duration; inspect the metrics, DOWN-link table, reporting period, and time-filter note.
6. Submit a natural-language request and inspect the selected workflow and execution result.
7. Review the execution-history entry and its details.
8. Open Scheduler Management. The scheduler service can be running while the scheduled-jobs list is empty; create a test schedule and verify its trigger separately before claiming scheduled execution has been end-to-end tested.

### Production verification recorded

The deployed Render application was checked with WF004 using **Shivamogga Zone** and a requested duration of **7 hours**. The observed report displayed:

- Total records: **70**
- Average performance score: **51.26**
- DOWN links: **30**

The dataset includes records without timestamps. WF004 retained those records and reported partial time filtering; therefore these totals are the application's observed report output, not a guarantee that all 70 records fall wholly within the seven-hour interval.

The live Execution History page also showed a successful **Performance Report** execution (execution #1).

## Repository layout

```text
app/
  agents/          # Workflow and plugin selection agents
  api/              # FastAPI route modules
  database/         # SQLAlchemy connection and models
  plugins/          # Jira, email, and plugin registry
  services/         # Workflow execution, data loading, scheduler services
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

Configure production secrets in the Render service's environment settings. Do not store credentials in source files or commit them to GitHub. A push to the configured deployment branch may trigger an automatic Render deployment.

## Current verification notes

- The previously recorded local test run completed with **27 passed**.
- WF002 was verified to create a real Jira issue.
- WF003 was verified by receipt of a real email.
- WF004 was verified in the deployed application and its execution was recorded in production history.
- The scheduler interface reported the scheduler running; a scheduled job trigger still requires a separate end-to-end demonstration.
- Dynamic workflow storage/execution should be demonstrated separately if it is part of the acceptance criteria.
