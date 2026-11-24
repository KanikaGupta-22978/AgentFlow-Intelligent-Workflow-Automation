
 // --------------------------------------------------
 // RESULT DISPLAY
 // --------------------------------------------------

function findPerformanceReport(data, depth = 0) {
    if (!data || typeof data !== "object" || depth > 5) {
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
            const match = findPerformanceReport(value, depth + 1);
            if (match) return match;
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

    // Summary cards
    const summary = document.createElement("div");
    summary.style.cssText =
        "display:flex;flex-wrap:wrap;gap:12px;margin:12px 0 18px;";

    const metrics = [
        ["Zone", report.zone || "All zones"],
        ["Total records", report.total_records ?? 0],
        ["Average performance", report.average_performance_score ?? "N/A"],
        ["DOWN links", report.down_link_count ?? (report.down_links || []).length]
    ];

    metrics.forEach(([label, value]) => {
        const card = document.createElement("div");
        card.style.cssText =
            "padding:12px 16px;border:1px solid #e5e9f2;border-radius:10px;background:#fff;min-width:130px;";

        const caption = document.createElement("div");
        caption.textContent = label;
        caption.style.cssText =
            "font-size:12px;color:#64748b;margin-bottom:5px;";

        const metric = document.createElement("strong");
        metric.textContent = String(value);
        metric.style.cssText = "font-size:18px;color:#17233d;";

        card.append(caption, metric);
        summary.appendChild(card);
    });

    element.appendChild(summary);

    // DOWN links table
    const downLinks = Array.isArray(report.down_links)
        ? report.down_links
        : [];

    const downHeading = document.createElement("h3");
    downHeading.textContent = `DOWN Links (${downLinks.length})`;
    downHeading.style.margin = "18px 0 10px";
    element.appendChild(downHeading);

    if (downLinks.length === 0) {
        const empty = document.createElement("p");
        empty.textContent =
            "No DOWN links were found in the selected reporting period.";
        element.appendChild(empty);
    } else {
        const wrapper = document.createElement("div");
        wrapper.style.cssText =
            "width:100%;overflow-x:auto;border:1px solid #e5e9f2;border-radius:10px;";

        const table = document.createElement("table");
        table.style.cssText =
            "width:100%;min-width:1250px;border-collapse:collapse;background:#fff;font-size:12px;";

        const columns = [
            ["Site code", "site_code"],
            ["Link", "link"],
            ["Zone", "zone"],
            ["IP address", "ip_address"],
            ["ISP", "isp"],
            ["Link type", "link_type"],
            ["Link speed (Mbps)", "link_speed_mbps"],
            ["Uptime", "uptime"],
            ["Performance score", "performance_score"],
            ["Latency", "avg_latency"],
            ["Packet drop", "avg_packet_drop"],
            ["Jitter", "avg_jitter"],
            ["CPU", "avg_cpu"],
            ["Memory", "avg_memory"],
            ["Circuit ID", "circuit_id"],
            ["Site address", "site_address"]
        ];

        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");

        columns.forEach(([label]) => {
            const th = document.createElement("th");
            th.textContent = label;
            th.style.cssText =
                "padding:11px 10px;text-align:left;white-space:nowrap;background:#f4f6fb;color:#475569;border-bottom:1px solid #e5e9f2;";
            headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");

        downLinks.forEach(record => {
            const row = document.createElement("tr");

            columns.forEach(([, key]) => {
                const cell = document.createElement("td");
                const value = record[key];

                cell.textContent =
                    value === null || value === undefined || value === ""
                        ? "-"
                        : String(value);

                cell.style.cssText =
                    "padding:10px;border-bottom:1px solid #edf0f5;white-space:nowrap;color:#334155;";

                row.appendChild(cell);
            });

            tbody.appendChild(row);
        });

        table.appendChild(tbody);
        wrapper.appendChild(table);
        element.appendChild(wrapper);
    }

    // Reporting period
    const period = document.createElement("p");
    period.textContent =
        `Reporting period: ${report.reporting_period?.start || "-"} to ${report.reporting_period?.end || "-"}`;
    period.style.cssText =
        "margin:12px 0;color:#64748b;font-size:12px;";

    element.appendChild(period);

    // Complete JSON response
    const details = document.createElement("details");
    details.style.marginTop = "14px";

    const summaryLine = document.createElement("summary");
    summaryLine.textContent =
        "View complete execution response (JSON)";
    summaryLine.style.cursor = "pointer";

    const raw = document.createElement("pre");
    raw.textContent = JSON.stringify(originalData, null, 2);
    raw.style.cssText =
        "margin-top:10px;padding:14px;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;background:#f7f8fb;border-radius:8px;";

    details.append(summaryLine, raw);
    element.appendChild(details);
}

function displayResult(elementId, data) {
    const element = document.getElementById(elementId);

    if (!element) return;

    const report = findPerformanceReport(data);

    if (report) {
        renderPerformanceReport(element, report, data);
        return;
    }

    element.style.whiteSpace = "pre-wrap";
    element.textContent = JSON.stringify(data, null, 2);
}
