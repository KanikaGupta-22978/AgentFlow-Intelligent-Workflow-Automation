const API_BASE = "";
let executionChart = null;
let workflowChart = null;
let executionHistory = [];

let currentPage = 1;
const pageSize = 10;
let totalPages = 1;
let totalExecutions = 0;

let selectedStatus = "";
let searchTerm = "";

// --------------------------------------------------
// API HELPER
// --------------------------------------------------

async function apiRequest(endpoint, method = "GET", body = null) {
    const options = {
        method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (body !== null) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, options);

    let data;

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (!response.ok) {
        throw new Error(
            data.detail || data.message || `Request failed (${response.status})`
        );
    }

    return data;
}

// --------------------------------------------------
// RESULT DISPLAY
// --------------------------------------------------

function findPerformanceReport(data, depth = 0) {
    if (!data || typeof data !== "object" || depth > 6) {
        return null;
    }

    if (
        data.workflow_id === "WF004" ||
        data.workflow_name === "Performance Report"
    ) {
        return data;
    }

    for (const value of Object.values(data)) {
        if (value && typeof value === "object") {
            const result = findPerformanceReport(value, depth + 1);
            if (result) return result;
        }
    }

    return null;
}

function renderPerformanceReport(element, report, originalData) {
    element.innerHTML = "";
    element.style.whiteSpace = "normal";

    const heading = document.createElement("h3");
    heading.textContent = "Performance Report";
    element.appendChild(heading);

    const metrics = [
        ["Zone", report.zone || "All zones"],
        ["Total records", report.total_records ?? 0],
        ["Average performance", report.average_performance_score ?? "N/A"],
        ["DOWN links", report.down_link_count ?? (report.down_links || []).length]
    ];

    const summary = document.createElement("div");
    summary.style.cssText = "display:flex;flex-wrap:wrap;gap:12px;margin:15px 0;";

    metrics.forEach(([label, value]) => {
        const card = document.createElement("div");
        card.style.cssText = "padding:12px;border:1px solid #ddd;border-radius:8px;min-width:130px;";
        card.textContent = `${label}: ${value}`;
        summary.appendChild(card);
    });

    element.appendChild(summary);

    const downLinks = Array.isArray(report.down_links)
        ? report.down_links
        : [];

    const subheading = document.createElement("h3");
    subheading.textContent = `DOWN Links (${downLinks.length})`;
    element.appendChild(subheading);

    if (!downLinks.length) {
        const message = document.createElement("p");
        message.textContent = "No DOWN links found.";
        element.appendChild(message);
    } else {
        const wrapper = document.createElement("div");
        wrapper.style.cssText = "overflow-x:auto;";

        const table = document.createElement("table");
        table.style.cssText = "width:100%;border-collapse:collapse;min-width:900px;";

        const columns = [
            ["Site code", "site_code"],
            ["Link", "link"],
            ["Zone", "zone"],
            ["IP address", "ip_address"],
            ["ISP", "isp"],
            ["Link type", "link_type"],
            ["Uptime", "uptime"],
            ["Performance score", "performance_score"],
            ["Latency", "avg_latency"],
            ["Packet drop", "avg_packet_drop"],
            ["Circuit ID", "circuit_id"],
            ["Site address", "site_address"]
        ];

        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        columns.forEach(([label]) => {
            const th = document.createElement("th");
            th.textContent = label;
            th.style.cssText = "padding:10px;background:#f0f2f8;text-align:left;border:1px solid #ddd;";
            headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");

        downLinks.forEach(record => {
            const row = document.createElement("tr");

            columns.forEach(([, key]) => {
                const cell = document.createElement("td");
                cell.textContent = record[key] ?? "-";
                cell.style.cssText = "padding:10px;border:1px solid #ddd;white-space:nowrap;";
                row.appendChild(cell);
            });

            tbody.appendChild(row);
        });

        table.appendChild(tbody);
        wrapper.appendChild(table);
        element.appendChild(wrapper);
    }

    const details = document.createElement("details");
    const summaryLine = document.createElement("summary");
    summaryLine.textContent = "View complete JSON response";

    const raw = document.createElement("pre");
    raw.textContent = JSON.stringify(originalData, null, 2);
    raw.style.cssText = "overflow:auto;white-space:pre-wrap;";

    details.append(summaryLine, raw);
    element.appendChild(details);
}

function displayResult(elementId, data) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const report = findPerformanceReport(data);

    if (report) {
        renderPerformanceReport(element, report, data);
    } else {
        element.style.whiteSpace = "pre-wrap";
        element.textContent = JSON.stringify(data, null, 2);
    }
}

// --------------------------------------------------
// BACKEND CONNECTION
// --------------------------------------------------

async function checkBackendConnection() {
    const status = document.getElementById("connectionStatus");

    try {
        await apiRequest("/health");

        if (status) {
            status.textContent = "Connected successfully";
        }
    } catch (error) {
        if (status) {
            status.textContent = "Backend unavailable";
        }

        console.error("Backend connection error:", error);
    }
}

// --------------------------------------------------
// DASHBOARD STATISTICS
// --------------------------------------------------

async function loadDashboardStats() {
    try {
        const data = await apiRequest("/executions/summary");

        document.getElementById("totalExecutions").textContent =
            data.total_executions ?? 0;

        document.getElementById("successfulExecutions").textContent =
            data.successful_executions ?? 0;

        document.getElementById("failedExecutions").textContent =
            data.failed_executions ?? 0;

        document.getElementById("runningExecutions").textContent =
            data.running_executions ?? 0;

    } catch (error) {
        console.error("Dashboard statistics error:", error);
    }
}

// --------------------------------------------------
// WORKFLOW LABELS
// --------------------------------------------------

function getWorkflowIdentifier(execution) {
    const storedId = execution.workflow_id;
    const inputData = execution.input_data || {};

    if (storedId !== null && storedId !== undefined && storedId !== "") {
        return String(storedId);
    }

    if (inputData.workflow_id) {
        return String(inputData.workflow_id);
    }

    return "UNKNOWN";
}

function getWorkflowLabel(execution) {
    if (execution.workflow_name) {
        return execution.workflow_name;
    }

    const identifier = getWorkflowIdentifier(execution);

    const predefinedLabels = {
        WF001: "Daily Alert Summary",
        WF002: "Jira Ticket Creation",
        WF003: "Email Notification",
        WF004: "Performance Report"
    };

    if (predefinedLabels[identifier]) {
        return predefinedLabels[identifier];
    }

    if (identifier !== "UNKNOWN") {
        return `Dynamic Workflow #${identifier}`;
    }

    return "Unknown Workflow";
}

// --------------------------------------------------
// DATE FORMATTER
// --------------------------------------------------

function formatDate(value) {
    if (!value) {
        return "-";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}

// --------------------------------------------------
// EXECUTION HISTORY API
// --------------------------------------------------

async function fetchExecutionHistory() {
    const params = new URLSearchParams({
        page: String(currentPage),
        page_size: String(pageSize)
    });

    if (selectedStatus) {
        params.set("status", selectedStatus);
    }

    const data = await apiRequest(
        `/executions/?${params.toString()}`
    );

    executionHistory = data.executions || [];
    totalPages = data.total_pages || 1;
    totalExecutions = data.total || 0;

    return data;
}

// --------------------------------------------------
// PAGINATION CONTROLS
// --------------------------------------------------

function updatePaginationControls() {
    const pageInfo = document.getElementById("historyPageInfo");
    const previousButton = document.getElementById("historyPrevBtn");
    const nextButton = document.getElementById("historyNextBtn");

    if (pageInfo) {
        pageInfo.textContent =
            `Page ${currentPage} of ${totalPages} · ${totalExecutions} executions`;
    }

    if (previousButton) {
        previousButton.disabled = currentPage <= 1;
    }

    if (nextButton) {
        nextButton.disabled = currentPage >= totalPages;
    }
}

async function goToPreviousPage() {
    if (currentPage <= 1) return;

    currentPage--;
    await loadExecutionHistory();
}

async function goToNextPage() {
    if (currentPage >= totalPages) return;

    currentPage++;
    await loadExecutionHistory();
}

// --------------------------------------------------
// HISTORY TABLE
// --------------------------------------------------

function renderExecutionHistory() {
    const tableBody = document.getElementById("historyTable");

    const filtered = executionHistory.filter(execution => {
        const workflow = getWorkflowLabel(execution).toLowerCase();
        const workflowId = getWorkflowIdentifier(execution).toLowerCase();
        const id = String(execution.execution_id ?? "");
        const status = String(execution.status ?? "").toLowerCase();

        const matchesSearch =
            !searchTerm ||
            id.includes(searchTerm) ||
            workflow.includes(searchTerm) ||
            workflowId.includes(searchTerm);

        const matchesStatus =
            !selectedStatus || status === selectedStatus;

        return matchesSearch && matchesStatus;
    });

    tableBody.innerHTML = "";

    if (filtered.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4">No matching executions found on this page.</td>
            </tr>
        `;
        return;
    }

    filtered.forEach(execution => {
        const row = document.createElement("tr");

        row.className = "execution-row";
        row.tabIndex = 0;
        row.setAttribute("role", "button");
        row.title = "Click to view execution details";

        const idCell = document.createElement("td");
        idCell.textContent = `#${execution.execution_id ?? "-"}`;

        const workflowCell = document.createElement("td");
        workflowCell.textContent = getWorkflowLabel(execution);

        const statusCell = document.createElement("td");
        const statusPill = document.createElement("span");

        const status = String(
            execution.status || "unknown"
        ).toLowerCase();

        statusPill.className = `status-pill ${
            ["success", "failed", "running"].includes(status)
                ? status
                : "unknown"
        }`;

        statusPill.textContent = status;
        statusCell.appendChild(statusPill);

        const dateCell = document.createElement("td");
        dateCell.textContent = formatDate(execution.started_at);

        row.append(idCell, workflowCell, statusCell, dateCell);

        row.addEventListener("click", () => {
            loadExecutionDetails(execution.execution_id);
        });

        row.addEventListener("keydown", event => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                loadExecutionDetails(execution.execution_id);
            }
        });

        tableBody.appendChild(row);
    });
}

// --------------------------------------------------
// LOAD EXECUTION HISTORY
// --------------------------------------------------

async function loadExecutionHistory() {
    const tableBody = document.getElementById("historyTable");

    tableBody.innerHTML = `
        <tr><td colspan="4">Loading executions...</td></tr>
    `;

    try {
        await fetchExecutionHistory();
        renderExecutionHistory();
        updatePaginationControls();
        renderAnalytics();

    } catch (error) {
        tableBody.innerHTML = `
            <tr><td colspan="4">${error.message}</td></tr>
        `;

        console.error("Execution history error:", error);
    }
}

// --------------------------------------------------
// EXECUTION DETAILS
// --------------------------------------------------

function createDetailItem(label, value) {
    const item = document.createElement("div");
    item.className = "detail-item";

    const heading = document.createElement("span");
    heading.className = "detail-label";
    heading.textContent = label;

    const content = document.createElement("strong");
    content.textContent = value ?? "-";

    item.append(heading, content);

    return item;
}

function showExecutionDetails(data) {
    const panel = document.getElementById("executionDetails");
    const subtitle = document.getElementById("executionDetailsSubtitle");
    const content = document.getElementById("executionDetailsContent");

    panel.hidden = false;
    subtitle.textContent = `Execution #${data.execution_id}`;

    content.innerHTML = "";

    const overview = document.createElement("div");
    overview.className = "execution-detail-grid";

    overview.append(
        createDetailItem("Execution ID", `#${data.execution_id}`),
        createDetailItem("Workflow", getWorkflowLabel(data)),
        createDetailItem("Status", data.status),
        createDetailItem("Workflow type", data.workflow_type),
        createDetailItem("Started at", formatDate(data.started_at)),
        createDetailItem("Completed at", formatDate(data.completed_at))
    );

    content.appendChild(overview);

    if (data.error_message) {
        const errorBox = document.createElement("div");
        errorBox.className = "execution-error";

        const errorHeading = document.createElement("h3");
        errorHeading.textContent = "Execution Error";

        const errorText = document.createElement("pre");
        errorText.textContent = data.error_message;

        errorBox.append(errorHeading, errorText);
        content.appendChild(errorBox);
    }

    const inputHeading = document.createElement("h3");
    inputHeading.className = "detail-section-title";
    inputHeading.textContent = "Input Data";

    const inputData = document.createElement("pre");
    inputData.textContent = JSON.stringify(
        data.input_data ?? {},
        null,
        2
    );

    const outputHeading = document.createElement("h3");
    outputHeading.className = "detail-section-title";
    outputHeading.textContent = "Output Data";

    const outputData = document.createElement("pre");
    outputData.textContent = JSON.stringify(
        data.output_data ?? {},
        null,
        2
    );

    content.append(
        inputHeading,
        inputData,
        outputHeading,
        outputData
    );

    panel.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
    });
}

async function loadExecutionDetails(executionId) {
    const panel = document.getElementById("executionDetails");
    const content = document.getElementById("executionDetailsContent");

    panel.hidden = false;
    content.textContent = "Loading execution details...";

    try {
        const data = await apiRequest(
            `/executions/${encodeURIComponent(executionId)}`
        );

        showExecutionDetails(data);

    } catch (error) {
        content.textContent =
            `Unable to load execution details: ${error.message}`;
    }
}

function closeExecutionDetails() {
    document.getElementById("executionDetails").hidden = true;
}

// --------------------------------------------------
// EXECUTION ACTIVITY CHART
// --------------------------------------------------

function renderExecutionChart() {
    const canvas = document.getElementById("executionChart");

    if (!canvas || typeof Chart === "undefined") return;

    const grouped = {};

    executionHistory.forEach(execution => {
        if (!execution.started_at) return;

        const date = new Date(execution.started_at);

        if (Number.isNaN(date.getTime())) return;

        const label = date.toLocaleDateString();

        if (!grouped[label]) {
            grouped[label] = {
                success: 0,
                failed: 0,
                running: 0
            };
        }

        const status = String(execution.status || "").toLowerCase();

        if (grouped[label][status] !== undefined) {
            grouped[label][status]++;
        }
    });

    const labels = Object.keys(grouped).reverse();

    if (executionChart) {
        executionChart.destroy();
    }

    executionChart = new Chart(canvas, {
        type: "line",

        data: {
            labels,

            datasets: [
                {
                    label: "Successful",
                    data: labels.map(label => grouped[label].success),
                    borderColor: "#16a987",
                    backgroundColor: "rgba(22,169,135,0.10)",
                    fill: true,
                    tension: 0.35
                },
                {
                    label: "Failed",
                    data: labels.map(label => grouped[label].failed),
                    borderColor: "#e65c70",
                    backgroundColor: "rgba(230,92,112,0.08)",
                    fill: false,
                    tension: 0.35
                },
                {
                    label: "Running",
                    data: labels.map(label => grouped[label].running),
                    borderColor: "#df982d",
                    backgroundColor: "rgba(223,152,45,0.08)",
                    fill: false,
                    tension: 0.35
                }
            ]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        usePointStyle: true,
                        padding: 18
                    }
                }
            },

            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    },
                    grid: {
                        color: "#edf0f5"
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });

    const message = document.getElementById("executionChartMessage");

    if (message) {
        message.textContent =
            executionHistory.length
                ? `Based on ${executionHistory.length} executions on the current page.`
                : "No execution data is available yet.";
    }
}

// --------------------------------------------------
// WORKFLOW DISTRIBUTION CHART
// --------------------------------------------------

function renderWorkflowChart() {
    const canvas = document.getElementById("workflowChart");
    const legend = document.getElementById("workflowLegend");

    if (!canvas || typeof Chart === "undefined") return;

    const counts = {};

    executionHistory.forEach(execution => {
        const workflow = getWorkflowLabel(execution);
        counts[workflow] = (counts[workflow] || 0) + 1;
    });

    const labels = Object.keys(counts);
    const values = Object.values(counts);

    const colors = [
        "#7563ed",
        "#16a987",
        "#e99b3b",
        "#e66b83",
        "#4f8bdc",
        "#a28ae8"
    ];

    if (workflowChart) {
        workflowChart.destroy();
    }

    workflowChart = new Chart(canvas, {
        type: "doughnut",

        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: labels.map(
                    (_, index) => colors[index % colors.length]
                ),
                borderWidth: 3,
                borderColor: "#ffffff",
                hoverOffset: 7
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "68%",
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });

    if (!legend) return;

    legend.innerHTML = "";

    labels.forEach((label, index) => {
        const item = document.createElement("span");
        item.className = "legend-item";

        const dot = document.createElement("span");
        dot.className = "legend-dot";
        dot.style.backgroundColor = colors[index % colors.length];

        const text = document.createElement("span");
        text.textContent = `${label} (${values[index]})`;

        item.append(dot, text);
        legend.appendChild(item);
    });
}

function renderAnalytics() {
    renderExecutionChart();
    renderWorkflowChart();
}

// --------------------------------------------------
// HISTORY FILTERS
// --------------------------------------------------

function applyHistoryFilters() {
    searchTerm = document
        .getElementById("historySearch")
        .value.trim()
        .toLowerCase();

    selectedStatus = document
        .getElementById("historyStatus")
        .value.toLowerCase();

    currentPage = 1;
    loadExecutionHistory();
}

// --------------------------------------------------
// NATURAL LANGUAGE EXECUTION
// --------------------------------------------------

async function executeNaturalLanguage() {
    const instruction = document
        .getElementById("userInstruction")
        .value.trim();

    const button = document.getElementById("executeInstructionBtn");

    if (!instruction) {
        alert("Please enter a workflow instruction.");
        return;
    }

    button.disabled = true;
    button.textContent = "Executing...";

    displayResult("chatResult", {
        status: "processing",
        message: "Your workflow is being processed..."
    });

    try {
        const data = await apiRequest(
            "/workflows/execute-natural-language",
            "POST",
            {
                user_instruction: instruction
            }
        );

        displayResult("chatResult", data);

        currentPage = 1;
        await refreshDashboard();

    } catch (error) {
        displayResult("chatResult", {
            status: "error",
            message: error.message
        });

    } finally {
        button.disabled = false;
        button.textContent = "✳ Execute workflow";
    }
}
function createWorkflowModal(workflowId) {
    const existing = document.getElementById("workflowModal");

    if (existing) existing.remove();

    const configurations = {
        WF002: {
            title: "Create Jira ticket",
            description: "Enter the incident ticket details.",
            fields: [
                {
                    name: "title",
                    label: "Ticket title",
                    placeholder: "Enter ticket title",
                    required: true
                },
                {
                    name: "description",
                    label: "Description",
                    placeholder: "Describe the incident",
                    type: "textarea",
                    required: true
                }
            ]
        },

        WF003: {
            title: "Send email notification",
            description: "Provide the notification details.",
            fields: [
                {
                    name: "recipient",
                    label: "Recipient email",
                    placeholder: "name@example.com",
                    type: "email",
                    required: true
                },
                {
                    name: "subject",
                    label: "Email subject",
                    placeholder: "Enter subject",
                    required: true
                },
                {
                    name: "message",
                    label: "Email message",
                    placeholder: "Write your message",
                    type: "textarea",
                    required: true
                }
            ]
        },

        WF004: {
            title: "Generate performance report",
            description: "Select the zone and reporting duration.",
            fields: [
                {
                    name: "zone",
                    label: "Network zone",
                    type: "select",
                    options: [
                        "Shivamogga Zone",
                        "mangaluru Zone"
                    ],
                    required: true
                },
                {
                    name: "hours",
                    label: "Requested duration (hours)",
                    placeholder: "Example: 6",
                    type: "number",
                    required: false
                }
            ]
        }
    };

    const config = configurations[workflowId];

    if (!config) return null;

    const modal = document.createElement("div");
    modal.id = "workflowModal";
    modal.className = "workflow-modal-overlay";

    const dialog = document.createElement("div");
    dialog.className = "workflow-modal";

    const heading = document.createElement("h2");
    heading.textContent = config.title;

    const description = document.createElement("p");
    description.textContent = config.description;

    const closeButton = document.createElement("button");
    closeButton.type = "button";
    closeButton.className = "modal-close";
    closeButton.textContent = "×";

    const form = document.createElement("form");
    form.id = "workflowInputForm";

    config.fields.forEach(field => {
        const group = document.createElement("div");
        group.className = "form-group";

        const label = document.createElement("label");
        label.textContent = field.label;
        label.htmlFor = `workflow-${field.name}`;

        let input;

        if (field.type === "textarea") {
            input = document.createElement("textarea");
            input.rows = 4;

        } else if (field.type === "select") {
            input = document.createElement("select");

            const placeholder = document.createElement("option");
            placeholder.value = "";
            placeholder.textContent = "Select a zone";
            input.appendChild(placeholder);

            field.options.forEach(optionValue => {
                const option = document.createElement("option");
                option.value = optionValue;
                option.textContent = optionValue;
                input.appendChild(option);
            });

        } else {
            input = document.createElement("input");
            input.type = field.type || "text";
        }

        input.id = `workflow-${field.name}`;
        input.name = field.name;
        input.placeholder = field.placeholder || "";
        input.required = field.required;

        group.append(label, input);
        form.appendChild(group);
    });

    const actions = document.createElement("div");
    actions.className = "modal-actions";

    const cancelButton = document.createElement("button");
    cancelButton.type = "button";
    cancelButton.className = "secondary";
    cancelButton.textContent = "Cancel";

    const submitButton = document.createElement("button");
    submitButton.type = "submit";
    submitButton.className = "execute-button";
    submitButton.textContent = "Execute workflow";

    actions.append(cancelButton, submitButton);
    form.appendChild(actions);

    dialog.append(closeButton, heading, description, form);
    modal.appendChild(dialog);
    document.body.appendChild(modal);

    function closeModal() {
        modal.remove();
    }

    closeButton.addEventListener("click", closeModal);
    cancelButton.addEventListener("click", closeModal);

    modal.addEventListener("click", event => {
        if (event.target === modal) closeModal();
    });

    form.addEventListener("submit", async event => {
        event.preventDefault();

        const inputData = {};

        config.fields.forEach(field => {
            const input = form.elements[field.name];

            if (input.value !== "") {
                inputData[field.name] =
                    field.type === "number"
                        ? Number(input.value)
                        : input.value.trim();
            }
        });

        submitButton.disabled = true;
        submitButton.textContent = "Executing...";

        try {
            await executePredefinedWorkflow(workflowId, inputData);
            closeModal();

        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Execute workflow";
        }
    });

    return modal;
}

// --------------------------------------------------
// PREDEFINED WORKFLOW EXECUTION
// --------------------------------------------------

async function executePredefinedWorkflow(workflowId, inputData = {}) {
    const button = document.querySelector(
        `[data-workflow="${workflowId}"]`
    );

    if (
        ["WF002", "WF003", "WF004"].includes(workflowId) &&
        Object.keys(inputData).length === 0
    ) {
        createWorkflowModal(workflowId);
        return;
    }

    if (button) {
        button.disabled = true;
        button.textContent = "Executing...";
    }

    try {
        const data = await apiRequest(
            `/workflows/execute?workflow_id=${encodeURIComponent(workflowId)}`,
            "POST",
            inputData
        );

        displayResult("workflowResult", data);

        currentPage = 1;
        await refreshDashboard();

    } catch (error) {
        displayResult("workflowResult", {
            status: "error",
            message: error.message
        });

    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = "Run workflow <span>→</span>";
        }
    }
}

// --------------------------------------------------
// DYNAMIC WORKFLOW LIBRARY
// --------------------------------------------------

function renderDynamicWorkflows(workflows) {
    const grid = document.getElementById("dynamicWorkflowGrid");
    const status = document.getElementById("dynamicWorkflowStatus");

    if (!grid || !status) return;

    grid.innerHTML = "";
    const items = Array.isArray(workflows) ? workflows : [];

    status.textContent = `${items.length} saved dynamic workflow${items.length === 1 ? "" : "s"}`;
    status.classList.toggle("is-empty", items.length === 0);

    if (items.length === 0) {
        const empty = document.createElement("div");
        empty.className = "dynamic-workflow-empty";
        empty.textContent = "No dynamic workflows have been saved yet.";
        grid.appendChild(empty);
        return;
    }

    items.forEach(workflow => {
        const card = document.createElement("article");
        card.className = "dynamic-workflow-card";

        const top = document.createElement("div");
        top.className = "dynamic-workflow-card-top";

        const idBadge = document.createElement("span");
        idBadge.className = "workflow-code";
        idBadge.textContent = `DYNAMIC · #${workflow.workflow_id}`;

        const stateBadge = document.createElement("span");
        stateBadge.className = `dynamic-state ${String(workflow.status || "active").toLowerCase()}`;
        stateBadge.textContent = workflow.status || "active";
        top.append(idBadge, stateBadge);

        const title = document.createElement("h3");
        title.textContent = workflow.name || `Dynamic Workflow #${workflow.workflow_id}`;

        const description = document.createElement("p");
        description.className = "dynamic-workflow-description";
        description.textContent = workflow.description || "No description provided.";

        const metadata = document.createElement("div");
        metadata.className = "dynamic-workflow-meta";

        const trigger = document.createElement("span");
        trigger.textContent = `Trigger: ${workflow.trigger || "manual"}`;

        const steps = Array.isArray(workflow.steps) ? workflow.steps : [];

        const stepCount = document.createElement("span");
        stepCount.textContent = `${steps.length} step${steps.length === 1 ? "" : "s"}`;

        metadata.append(trigger, stepCount);

        const details = document.createElement("details");
        details.className = "dynamic-workflow-details";

        const summary = document.createElement("summary");
        summary.textContent = "View workflow steps";

        const stepList = document.createElement("ol");
        stepList.className = "dynamic-step-list";

        if (steps.length === 0) {
            const item = document.createElement("li");
            item.textContent = "No steps defined.";
            stepList.appendChild(item);
        } else {
            steps.forEach((step, index) => {
                const item = document.createElement("li");
                const action = step.action || "unknown action";
                const label = step.description || action.replaceAll("_", " ");

                item.textContent = `${index + 1}. ${label} · ${action}`;

                if (step.condition) {
                    const condition = document.createElement("small");
                    condition.textContent =
                        `Condition: ${step.condition.field} ${step.condition.operator} ${String(step.condition.value)}`;

                    item.appendChild(condition);
                }

                stepList.appendChild(item);
            });
        }

        details.append(summary, stepList);

        const execute = document.createElement("button");
        execute.type = "button";
        execute.className = "dynamic-execute-button";
        execute.textContent = "▶ Execute workflow";
        execute.disabled =
            String(workflow.status || "active").toLowerCase() !== "active";

        execute.addEventListener("click", () => {
            executeDynamicWorkflow(workflow.workflow_id, execute);
        });

        card.append(top, title, description, metadata, details, execute);
        grid.appendChild(card);
    });
}

async function loadDynamicWorkflows() {
    const status = document.getElementById("dynamicWorkflowStatus");
    const grid = document.getElementById("dynamicWorkflowGrid");

    if (status) status.textContent = "Loading saved dynamic workflows...";
    if (grid) grid.innerHTML = "";

    try {
        const workflows = await apiRequest("/dynamic-workflows/");
        renderDynamicWorkflows(workflows);
        return workflows;

    } catch (error) {
        if (status) {
            status.textContent =
                `Unable to load dynamic workflows: ${error.message}`;

            status.classList.add("is-error");
        }

        console.error("Dynamic workflow loading error:", error);
        return [];
    }
}

async function executeDynamicWorkflow(workflowId, button) {
    if (button) {
        button.disabled = true;
        button.textContent = "Executing...";
    }

    try {
        const result = await apiRequest(
            `/dynamic-workflows/${encodeURIComponent(workflowId)}/execute`,
            "POST",
            { input_data: {} }
        );

        displayResult("workflowResult", result);

        currentPage = 1;
        await refreshDashboard();
        await loadDynamicWorkflows();

        document.getElementById("workflowResult").scrollIntoView({
            behavior: "smooth",
            block: "nearest"
        });

    } catch (error) {
        displayResult("workflowResult", {
            status: "error",
            workflow_id: workflowId,
            message: error.message
        });

    } finally {
        if (button && button.isConnected) {
            button.disabled = false;
            button.textContent = "▶ Execute workflow";
        }
    }
}
// --------------------------------------------------
// SCHEDULER DISPLAY
// --------------------------------------------------

function formatSchedule(job) {
    const type = String(job.schedule_type || "").toLowerCase();
    const trigger = String(job.trigger || "");

    if (type === "interval") {
        const match = trigger.match(
            /interval\[(?:(\d+) day[s]?, )?(?:(\d+):)?(\d+):(\d+)\]/i
        );

        if (match) {
            const days = Number(match[1] || 0);
            const hours = Number(match[2] || 0);
            const minutes = Number(match[3] || 0);
            const seconds = Number(match[4] || 0);

            const parts = [];

            if (days) parts.push(`${days} day${days === 1 ? "" : "s"}`);
            if (hours) parts.push(`${hours} hour${hours === 1 ? "" : "s"}`);
            if (minutes) parts.push(`${minutes} minute${minutes === 1 ? "" : "s"}`);
            if (seconds) parts.push(`${seconds} second${seconds === 1 ? "" : "s"}`);

            return `Every ${parts.join(" ") || "interval"}`;
        }

        return trigger || "Interval schedule";
    }

    if (type === "daily") return "Daily at 9:00 AM";
    if (type === "weekly") return "Weekly · Monday at 10:00 AM";
    if (type === "monthly") return "Monthly · 1st day at 9:00 AM";
    if (type === "one_time") return "One-time execution";

    return trigger || type || "Schedule not specified";
}

function getScheduledWorkflowLabel(workflowId) {
    const labels = {
        WF001: "Daily Alert Summary",
        WF002: "Ticket Creation",
        WF003: "Email Notification",
        WF004: "Performance Report"
    };

    return labels[workflowId] || workflowId || "Unknown workflow";
}

function renderScheduledJobs(data) {
    const container = document.getElementById("schedulerResult");

    if (!container) return;

    container.innerHTML = "";

    const jobs = data.jobs || [];
    const schedulerRunning = data.running ?? data.scheduler_running ?? false;

    const status = document.createElement("div");
    status.className = "scheduler-status";

    const statusText = document.createElement("strong");
    statusText.textContent = schedulerRunning
        ? "Scheduler is running"
        : "Scheduler is stopped";

    const count = document.createElement("span");
    count.textContent = `${jobs.length} scheduled job${jobs.length === 1 ? "" : "s"}`;

    status.append(statusText, count);
    container.appendChild(status);

    if (!jobs.length) {
        const empty = document.createElement("p");
        empty.textContent = "No scheduled jobs found. Create a schedule above.";
        container.appendChild(empty);
        return;
    }

    const grid = document.createElement("div");
    grid.className = "scheduled-jobs-grid";

    jobs.forEach(job => {
        const card = document.createElement("article");
        card.className = "scheduled-job-card";

        const badge = document.createElement("span");
        badge.className = "workflow-code";
        badge.textContent = job.workflow_id || "Workflow";

        const title = document.createElement("h3");
        title.textContent = getScheduledWorkflowLabel(job.workflow_id);

        const jobId = document.createElement("p");
        jobId.textContent = `Job ID: ${job.id || job.job_id || "-"}`;

        const scheduleLabel = document.createElement("span");
        scheduleLabel.textContent = "SCHEDULE";

        const schedule = document.createElement("p");
        schedule.textContent = formatSchedule(job);

        const nextLabel = document.createElement("span");
        nextLabel.textContent = "NEXT EXECUTION";

        const next = document.createElement("p");
        next.textContent = formatDate(job.next_run_time);

        const cancelButton = document.createElement("button");
        cancelButton.type = "button";
        cancelButton.className = "secondary cancel-schedule-button";
        cancelButton.textContent = "Cancel schedule";

        const jobIdValue = job.id || job.job_id;

        cancelButton.addEventListener("click", () => {
            cancelScheduledJob(jobIdValue, cancelButton);
        });

        card.append(
            badge,
            title,
            jobId,
            scheduleLabel,
            schedule,
            nextLabel,
            next,
            cancelButton
        );

        grid.appendChild(card);
    });

    container.appendChild(grid);
}

// --------------------------------------------------
// SCHEDULER API
// --------------------------------------------------

async function refreshSchedulerStatus() {
    const container = document.getElementById("schedulerResult");

    if (container) {
        container.textContent = "Loading scheduled jobs...";
    }

    try {
        const data = await apiRequest("/scheduler/jobs");
        renderScheduledJobs(data);
        return data;

    } catch (error) {
        if (container) {
            container.textContent =
                `Unable to load scheduled jobs: ${error.message}`;
        }

        throw error;
    }
}

async function startScheduler() {
    const button = document.getElementById("startSchedulerBtn");

    if (button) button.disabled = true;

    try {
        await apiRequest("/scheduler/start", "POST");
        await refreshSchedulerStatus();

    } catch (error) {
        const container = document.getElementById("schedulerResult");

        if (container) {
            container.textContent =
                `Unable to start scheduler: ${error.message}`;
        }

    } finally {
        if (button) button.disabled = false;
    }
}

async function stopScheduler() {
    const button = document.getElementById("stopSchedulerBtn");

    if (button) button.disabled = true;

    try {
        await apiRequest("/scheduler/stop", "POST");
        await refreshSchedulerStatus();

    } catch (error) {
        const container = document.getElementById("schedulerResult");

        if (container) {
            container.textContent =
                `Unable to stop scheduler: ${error.message}`;
        }

    } finally {
        if (button) button.disabled = false;
    }
}

async function loadScheduledJobs() {
    try {
        await refreshSchedulerStatus();
    } catch (error) {
        console.error("Scheduled jobs error:", error);
    }
}

// --------------------------------------------------
// SCHEDULER FORM
// --------------------------------------------------

function updateScheduleFields() {
    const type = document.getElementById("scheduleType").value;

    const fields = {
        interval: document.getElementById("intervalFields"),
        daily: document.getElementById("timeFields"),
        weekly: document.getElementById("weeklyFields"),
        monthly: document.getElementById("monthlyFields"),
        once: document.getElementById("onceFields")
    };

    Object.entries(fields).forEach(([key, element]) => {
        if (!element) return;

        const visible = key === type;
        element.hidden = !visible;

        element.querySelectorAll("input, select").forEach(input => {
            input.disabled = !visible;
            input.required = visible;
        });
    });
}

async function createScheduledWorkflow(event) {
    event.preventDefault();

    const button = document.getElementById("createScheduleBtn");
    const message = document.getElementById("scheduleMessage");

    const workflowId =
        document.getElementById("scheduleWorkflow").value;

    const scheduleType =
        document.getElementById("scheduleType").value;

    let endpoint = "";
    let payload = {};

    if (scheduleType === "interval") {
        const minutes = Number(
            document.getElementById("scheduleMinutes").value
        );

        if (!Number.isInteger(minutes) || minutes < 1) {
            message.textContent = "Enter a valid interval of at least one minute.";
            return;
        }

        endpoint = "/scheduler/schedule";
        payload = {
            workflow_id: workflowId,
            interval_minutes: minutes
        };

    } else if (scheduleType === "daily") {
        const time = document.getElementById("scheduleTime").value;

        if (!time) {
            message.textContent = "Select a daily execution time.";
            return;
        }

        endpoint = "/scheduler/daily";
        payload = {
            workflow_id: workflowId,
            time
        };

    } else if (scheduleType === "weekly") {
        const time = document.getElementById("scheduleTime").value;
        const day = document.getElementById("scheduleDay").value;

        if (!time || !day) {
            message.textContent = "Select a weekday and execution time.";
            return;
        }

        endpoint = "/scheduler/weekly";
        payload = {
            workflow_id: workflowId,
            day,
            time
        };

    } else if (scheduleType === "monthly") {
        const time = document.getElementById("scheduleTime").value;
        const day = Number(
            document.getElementById("scheduleMonthDay").value
        );

        if (!time || !Number.isInteger(day) || day < 1 || day > 31) {
            message.textContent =
                "Select a valid time and a day between 1 and 31.";
            return;
        }

        endpoint = "/scheduler/monthly";
        payload = {
            workflow_id: workflowId,
            day,
            time
        };

    } else if (scheduleType === "once") {
        const dateTime =
            document.getElementById("scheduleDateTime").value;

        if (!dateTime) {
            message.textContent = "Select a date and time.";
            return;
        }

        const selectedDate = new Date(dateTime);

        if (Number.isNaN(selectedDate.getTime()) ||
            selectedDate <= new Date()) {
            message.textContent = "Choose a future date and time.";
            return;
        }

        endpoint = "/scheduler/once";
        payload = {
            workflow_id: workflowId,
            run_date: `${dateTime}:00+05:30`
        };
    }

    button.disabled = true;
    button.textContent = "Creating...";
    message.textContent = "Starting scheduler and creating your schedule...";

    try {
        await apiRequest("/scheduler/start", "POST");

        const result = await apiRequest(
            endpoint,
            "POST",
            payload
        );

        message.textContent =
            result.message || "Schedule created successfully.";

        document.getElementById("scheduleForm").reset();
        updateScheduleFields();

        await refreshSchedulerStatus();

    } catch (error) {
        message.textContent =
            `Unable to create schedule: ${error.message}`;

    } finally {
        button.disabled = false;
        button.textContent = "Create Schedule";
    }
}

// --------------------------------------------------
// CANCEL SCHEDULE
// --------------------------------------------------

async function cancelScheduledJob(jobId, button) {
    if (!jobId) {
        alert("This scheduled job does not have a valid job ID.");
        return;
    }

    const confirmed = confirm(
        `Are you sure you want to cancel scheduled job "${jobId}"?`
    );

    if (!confirmed) return;

    if (button) {
        button.disabled = true;
        button.textContent = "Cancelling...";
    }

    try {
        const result = await apiRequest(
            `/scheduler/jobs/${encodeURIComponent(jobId)}`,
            "DELETE"
        );

        const message = document.getElementById("scheduleMessage");

        if (message) {
            message.textContent =
                result.message || "Schedule cancelled successfully.";
        }

        await refreshSchedulerStatus();

    } catch (error) {
        const message = document.getElementById("scheduleMessage");

        if (message) {
            message.textContent =
                `Unable to cancel schedule: ${error.message}`;
        }

        if (button) {
            button.disabled = false;
            button.textContent = "Cancel schedule";
        }
    }
}

// --------------------------------------------------
// DASHBOARD REFRESH
// --------------------------------------------------

async function refreshDashboard() {
    await loadDashboardStats();
    await loadExecutionHistory();
}

// --------------------------------------------------
// NAVIGATION
// --------------------------------------------------

function setupNavigation() {
    const links = document.querySelectorAll(".sidebar nav a");

    links.forEach(link => {
        link.addEventListener("click", () => {
            links.forEach(item => item.classList.remove("active"));
            link.classList.add("active");
        });
    });
}

// --------------------------------------------------
// INITIALIZATION
// --------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {

    document
        .getElementById("executeInstructionBtn")
        .addEventListener("click", executeNaturalLanguage);

    document
        .querySelectorAll("[data-workflow]")
        .forEach(button => {
            button.addEventListener("click", () => {
                executePredefinedWorkflow(button.dataset.workflow);
            });
        });

    document
        .getElementById("startSchedulerBtn")
        .addEventListener("click", startScheduler);

    document
        .getElementById("stopSchedulerBtn")
        .addEventListener("click", stopScheduler);

    document
        .getElementById("refreshJobsBtn")
        .addEventListener("click", loadScheduledJobs);

    document
        .getElementById("scheduleType")
        .addEventListener("change", updateScheduleFields);

    document
        .getElementById("scheduleForm")
        .addEventListener("submit", createScheduledWorkflow);

    document
        .getElementById("refreshDynamicWorkflowsBtn")
        .addEventListener("click", loadDynamicWorkflows);

    document
        .getElementById("refreshHistoryBtn")
        .addEventListener("click", loadExecutionHistory);

    document
        .getElementById("historySearch")
        .addEventListener("input", applyHistoryFilters);

    document
        .getElementById("historyStatus")
        .addEventListener("change", applyHistoryFilters);

    document
        .getElementById("historyPrevBtn")
        .addEventListener("click", goToPreviousPage);

    document
        .getElementById("historyNextBtn")
        .addEventListener("click", goToNextPage);

    document
        .getElementById("closeExecutionDetailsBtn")
        .addEventListener("click", closeExecutionDetails);

    updateScheduleFields();
    setupNavigation();

    checkBackendConnection();
    refreshDashboard();
    loadScheduledJobs();
    loadDynamicWorkflows();
});
