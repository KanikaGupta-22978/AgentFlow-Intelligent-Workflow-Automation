# AgentFlow - Intelligent Workflow Automation

## Project Overview

AgentFlow is a configurable workflow automation platform that allows users to define, execute, schedule, and monitor operational workflows through a web dashboard, REST APIs, and natural-language instructions.

It uses Google's Gemini API for natural-language understanding and LangGraph to coordinate workflow selection, parameter extraction, validation, and execution.

## Key Features

- **Natural-language automation:** Describe a task in plain English and let Gemini identify the appropriate workflow and parameters.
- **LangGraph orchestration:** Three-stage agent workflow for selection, parameter extraction and validation, and execution.
- **Fallback mechanism:** Rule-based workflow selection when Gemini is unavailable.
- **Predefined workflows:** Alert summaries, Jira ticket creation, email notifications, and network performance reports.
- **Dynamic workflows:** Create, edit, delete, and execute configurable workflows.
- **Conditional execution:** Support conditional workflow steps.
- **Automated scheduling:** Schedule workflows using APScheduler.
- **Execution monitoring:** View execution history, details, filters, and paginated results.
- **Dashboard analytics:** Monitor workflow activity and execution distribution.
- **Plugin architecture:** Separate integration components for Jira and email operations.
- **REST API:** Backend services exposed through FastAPI.

## Technology Stack

| Component           | Technology            |
| ------------------- | --------------------- |
| Backend             | Python 3.11, FastAPI  |
| AI / LLM            | Google Gemini API     |
| Agent orchestration | LangGraph             |
| Database            | SQLite                |
| ORM                 | SQLAlchemy            |
| Scheduling          | APScheduler           |
| Frontend            | HTML, CSS, JavaScript |
| Testing             | Pytest                |

## Architecture

The application follows a modular architecture:

1. **Frontend:** Provides the dashboard, workflow management, natural-language interaction, scheduling, and execution monitoring.
2. **FastAPI backend:** Exposes API endpoints and coordinates application services.
3. **LangGraph agent:** Manages the natural-language workflow.
4. **Gemini integration:** Interprets user instructions and extracts workflow parameters.
5. **Workflow services:** Validate and execute selected workflows.
6. **Scheduler:** Triggers workflows automatically according to configured schedules.
7. **Database:** Stores workflow and execution information using SQLite and SQLAlchemy.

### LangGraph execution flow

```text
User Instruction
       |
       v
Workflow Selection
       |
       v
Parameter Extraction
       |
       v
Parameter Validation
       |
       v
Workflow Execution
       |
       v
Execution Result
```

Gemini is attempted first. If the LLM request fails, the agent uses rule-based workflow selection as a fallback.

## Available Workflows

| Workflow ID | Workflow                   | Description                                           |
| ----------- | -------------------------- | ----------------------------------------------------- |
| WF001       | Daily Alert Summary        | Generates an alert summary                            |
| WF002       | Jira Ticket Creation       | Creates a ticket through the Jira plugin              |
| WF003       | Email Notification         | Sends an email through the email plugin               |
| WF004       | Network Performance Report | Generates a report for a selected zone and time range |

## Project Setup

### 1. Clone the repository

```bash
git clone https://github.com/KanikaGupta-22978/AgentFlow-Intelligent-Workflow-Automation.git
cd AgentFlow-Intelligent-Workflow-Automation
```

Alternatively, open the extracted project directory in VS Code.

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Configure environment variables

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

Keep your actual `.env` file private. Never commit API keys to GitHub.

### 6. Start the application

```bash
uvicorn app.main:app --reload
```

### 7. Open the application

- Dashboard: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs

## Running Tests

Run the complete automated test suite:

```bash
python -m pytest -q
```

Latest verified result:

**27 tests passed.**

## Demonstration

A suggested demonstration sequence:

1. Open the AgentFlow dashboard.
2. Explore the predefined workflows.
3. Create and manage a dynamic workflow.
4. Submit a natural-language instruction.
5. Show Gemini selecting a workflow and extracting its parameters.
6. Demonstrate workflow execution and the returned result.
7. Configure a scheduled workflow and demonstrate its automatic trigger.
8. Review execution history and dashboard monitoring.

Example natural-language request:

```text
Generate the performance report for Shivamogga Zone
for the last 6 hours.
```

Verified agent result:

```text
Status: success
Workflow: WF004
Zone: Shivamogga Zone
Hours: 6
LLM Used: True
```

## Project Structure

```text
Agentic Worflow Automation/
|
|-- app/
|   |-- agents/
|   |-- api/
|   |-- models/
|   |-- plugins/
|   |-- services/
|   |-- main.py
|
|-- frontend/
|   |-- index.html
|   |-- static/
|       |-- style.css
|       |-- script.js
|
|-- tests/
|-- data/
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- README.md
```

## Known Limitations

- Jira and email integrations currently use mock implementations; real external service integration requires additional configuration and implementation.
- The application currently uses SQLite for persistence.
- Gemini availability depends on API access, network connectivity, and model availability. Rule-based fallback is provided when Gemini requests fail.
- The scheduler and workflow execution have been demonstrated locally; distributed execution and horizontal scaling have not been established.

## Current Project Status

- Gemini-powered natural-language workflow execution verified.
- LangGraph orchestration implemented.
- Rule-based fallback tested.
- Predefined and dynamic workflow functionality implemented.
- Scheduled workflow execution demonstrated.
- Execution history and dashboard monitoring implemented.
- Automated test suite: **27 passed**.

