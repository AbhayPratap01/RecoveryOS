const API_BASE = "https://recoveryos-api-eey6.onrender.com";

const transactionInput = document.getElementById("transactionInput");
const searchButton = document.getElementById("searchButton");

const errorBox = document.getElementById("errorBox");

const emptyState = document.getElementById("emptyState");
const summarySection = document.getElementById("summarySection");
const timelineSection = document.getElementById("timelineSection");
const rawSection = document.getElementById("rawSection");

const summaryTransaction = document.getElementById("summaryTransaction");
const summaryAction = document.getElementById("summaryAction");
const summaryPolicy = document.getElementById("summaryPolicy");
const summaryStatus = document.getElementById("summaryStatus");

const timeline = document.getElementById("timeline");
const rawAudit = document.getElementById("rawAudit");


function showError(message) {
    errorBox.textContent = message;
    errorBox.style.display = "block";
}


function hideError() {
    errorBox.textContent = "";
    errorBox.style.display = "none";
}


function resetView() {
    summarySection.style.display = "none";
    timelineSection.style.display = "none";
    rawSection.style.display = "none";

    emptyState.style.display = "block";

    timeline.innerHTML = "";
    rawAudit.textContent = "";
}


function formatAction(action) {
    if (!action) {
        return "—";
    }

    return action
        .replace(/_/g, " ")
        .replace(/\b\w/g, char => char.toUpperCase());
}


function formatStatus(status) {
    if (!status) {
        return "—";
    }

    return status
        .replace(/_/g, " ")
        .replace(/\b\w/g, char => char.toUpperCase());
}


function addTimelineItem(title, meta) {
    const item = document.createElement("div");
    item.className = "timeline-item";

    const dot = document.createElement("div");
    dot.className = "timeline-dot";

    const titleElement = document.createElement("div");
    titleElement.className = "timeline-title";
    titleElement.textContent = title;

    const metaElement = document.createElement("div");
    metaElement.className = "timeline-meta";
    metaElement.textContent = meta;

    item.appendChild(dot);
    item.appendChild(titleElement);
    item.appendChild(metaElement);

    timeline.appendChild(item);
}


function renderAudit(data) {

    emptyState.style.display = "none";

    summarySection.style.display = "block";
    timelineSection.style.display = "block";
    rawSection.style.display = "block";


    const transactionId =
        data.transaction_id ||
        data.transactionId ||
        "Unknown";


    const action =
        data.action ||
        data.final_action ||
        data.execution?.action ||
        "—";


    const policyAllowed =
        data.policy?.allowed;


    let policyStatus = "Not evaluated";

    if (policyAllowed === true) {
        policyStatus = "Approved";
    } else if (policyAllowed === false) {
        policyStatus = "Rejected";
    }


    let executionStatus =
        data.execution?.status ||
        data.status ||
        "Analyzed";


    summaryTransaction.textContent = transactionId;
    summaryAction.textContent = formatAction(action);
    summaryPolicy.textContent = policyStatus;
    summaryStatus.textContent = formatStatus(executionStatus);


    timeline.innerHTML = "";


    addTimelineItem(
        "Transaction analyzed",
        `Action: ${formatAction(action)} • Policy: ${policyStatus}`
    );


    if (data.policy) {

        const reasons =
            Array.isArray(data.policy.reasons)
                ? data.policy.reasons
                : [];


        if (policyAllowed === true) {

            addTimelineItem(
                "Policy approved",
                reasons.length
                    ? `Approved • ${reasons.join(", ")}`
                    : "Selected recovery action passed policy checks."
            );

        } else if (policyAllowed === false) {

            addTimelineItem(
                "Policy rejected",
                reasons.length
                    ? reasons.join(", ")
                    : "Selected recovery action was rejected by policy."
            );
        }
    }


    if (data.execution) {

        const recovered =
            data.execution.recovered === true;

        const amount =
            data.execution.amount_recovered ??
            data.execution.amountRecovered ??
            0;


        if (recovered) {

            addTimelineItem(
                "Payment successfully recovered",
                `Action: ${formatAction(data.execution.action || action)} • ₹${Number(amount).toLocaleString("en-IN")} recovered`
            );

        } else {

            addTimelineItem(
                "Recovery attempt failed",
                data.execution.message ||
                "Recovery attempt was unsuccessful."
            );
        }
    }


    if (data.audit_id) {

        addTimelineItem(
            "Audit record created",
            `Audit ID: ${data.audit_id}`
        );
    }


    rawAudit.textContent =
        JSON.stringify(data, null, 2);
}


async function loadAudit() {

    const transactionId =
        transactionInput.value.trim();


    if (!transactionId) {

        showError(
            "Please enter a transaction ID."
        );

        return;
    }


    hideError();

    searchButton.disabled = true;
    searchButton.textContent = "Loading...";


    try {

        /*
         * The audit endpoint accepts the transaction ID.
         *
         * Example:
         * /audit/txn_000003
         */

        const response = await fetch(
            `${API_BASE}/audit/${encodeURIComponent(transactionId)}`,
            {
                method: "GET",
                headers: {
                    "Accept": "application/json"
                }
            }
        );


        if (!response.ok) {

            let message =
                `Unable to load audit (${response.status})`;

            try {

                const errorData =
                    await response.json();

                if (errorData.detail) {
                    message = errorData.detail;
                }

            } catch (_) {
                // Ignore invalid error response.
            }

            throw new Error(message);
        }


        const data =
            await response.json();


        renderAudit(data);

    } catch (error) {

        resetView();

        showError(
            error.message ||
            "Failed to load audit information."
        );

    } finally {

        searchButton.disabled = false;
        searchButton.textContent = "Load Audit";
    }
}


searchButton.addEventListener(
    "click",
    loadAudit
);


transactionInput.addEventListener(
    "keydown",
    event => {

        if (event.key === "Enter") {
            loadAudit();
        }

    }
);