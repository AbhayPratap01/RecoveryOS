const API_BASE =
    "https://recoveryos-api-eey6.onrender.com";


/* =========================================================
   ELEMENTS
========================================================= */

const transactionInput =
    document.getElementById("transactionInput");

const searchButton =
    document.getElementById("searchButton");

const transactionSelect =
    document.getElementById("transactionSelect");

const selectLoadButton =
    document.getElementById("selectLoadButton");

const refreshButton =
    document.getElementById("refreshButton");

const transactionCount =
    document.getElementById("transactionCount");

const errorBox =
    document.getElementById("errorBox");

const successBox =
    document.getElementById("successBox");

const emptyState =
    document.getElementById("emptyState");

const summarySection =
    document.getElementById("summarySection");

const timelineSection =
    document.getElementById("timelineSection");

const rawSection =
    document.getElementById("rawSection");

const summaryTransaction =
    document.getElementById("summaryTransaction");

const summaryAction =
    document.getElementById("summaryAction");

const summaryPolicy =
    document.getElementById("summaryPolicy");

const summaryStatus =
    document.getElementById("summaryStatus");

const timeline =
    document.getElementById("timeline");

const rawAudit =
    document.getElementById("rawAudit");


/* =========================================================
   ERROR / SUCCESS
========================================================= */

function showError(message) {

    errorBox.textContent = message;

    errorBox.style.display = "block";

}


function hideError() {

    errorBox.textContent = "";

    errorBox.style.display = "none";

}


function showSuccess(message) {

    successBox.textContent = message;

    successBox.style.display = "block";

}


function hideSuccess() {

    successBox.textContent = "";

    successBox.style.display = "none";

}


/* =========================================================
   RESET
========================================================= */

function resetView() {

    summarySection.style.display = "none";

    timelineSection.style.display = "none";

    rawSection.style.display = "none";

    emptyState.style.display = "block";

    timeline.innerHTML = "";

    rawAudit.textContent = "";

}


/* =========================================================
   FORMATTERS
========================================================= */

function formatAction(action) {

    if (!action) {
        return "—";
    }

    return String(action)
        .replace(/_/g, " ")
        .replace(/\b\w/g, char =>
            char.toUpperCase()
        );

}


function formatDate(timestamp) {

    if (!timestamp) {
        return "";
    }

    const date =
        new Date(timestamp);

    if (Number.isNaN(date.getTime())) {
        return "";
    }

    return date.toLocaleString(
        "en-IN",
        {
            dateStyle: "medium",
            timeStyle: "short"
        }
    );

}


function formatCurrency(amount) {

    const value =
        Number(amount || 0);

    return `₹${value.toLocaleString(
        "en-IN",
        {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    )}`;

}


/* =========================================================
   EXTRACT TRANSACTION IDS
========================================================= */

function extractTransactionIds(data) {

    const ids = new Set();


    /*
     * Case 1:
     *
     * Backend returns:
     *
     * [
     *   {
     *      transaction_id: "txn_000001"
     *   }
     * ]
     */

    if (Array.isArray(data)) {

        data.forEach(item => {

            if (item?.transaction_id) {

                ids.add(
                    String(item.transaction_id)
                );

            }

        });

    }


    /*
     * Case 2:
     *
     * Backend returns:
     *
     * {
     *    events: [...]
     * }
     */

    if (Array.isArray(data?.events)) {

        data.events.forEach(event => {

            if (event?.transaction_id) {

                ids.add(
                    String(event.transaction_id)
                );

            }

        });

    }


    /*
     * Case 3:
     *
     * Backend returns:
     *
     * {
     *    audits: [...]
     * }
     */

    if (Array.isArray(data?.audits)) {

        data.audits.forEach(item => {

            if (item?.transaction_id) {

                ids.add(
                    String(item.transaction_id)
                );

            }

        });

    }


    /*
     * Case 4:
     *
     * Backend returns:
     *
     * {
     *    data: [...]
     * }
     */

    if (Array.isArray(data?.data)) {

        data.data.forEach(item => {

            if (item?.transaction_id) {

                ids.add(
                    String(item.transaction_id)
                );

            }

        });

    }


    return Array.from(ids).sort();

}


/* =========================================================
   LOAD AVAILABLE TRANSACTIONS
========================================================= */

async function loadAvailableTransactions() {

    transactionSelect.innerHTML = `
        <option value="">
            Loading transactions...
        </option>
    `;

    transactionSelect.disabled = true;

    refreshButton.disabled = true;

    hideError();

    hideSuccess();


    try {

        const response =
            await fetch(
                `${API_BASE}/audit`,
                {
                    method: "GET",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


        if (!response.ok) {

            throw new Error(
                `Unable to load audit records (${response.status})`
            );

        }


        const data =
            await response.json();


        const transactionIds =
            extractTransactionIds(data);


        transactionSelect.innerHTML = "";


        if (transactionIds.length === 0) {

            transactionSelect.innerHTML = `
                <option value="">
                    No audited transactions available
                </option>
            `;

            transactionCount.textContent =
                "No audit records are currently available.";

            return;

        }


        const defaultOption =
            document.createElement("option");

        defaultOption.value = "";

        defaultOption.textContent =
            "Select a transaction...";

        transactionSelect.appendChild(
            defaultOption
        );


        transactionIds.forEach(
            transactionId => {

                const option =
                    document.createElement("option");

                option.value =
                    transactionId;

                option.textContent =
                    transactionId;

                transactionSelect.appendChild(
                    option
                );

            }
        );


        transactionCount.textContent =
            `${transactionIds.length} audited transaction${transactionIds.length === 1 ? "" : "s"} available.`;


    } catch (error) {

        console.error(
            "Failed to load available transactions:",
            error
        );


        transactionSelect.innerHTML = `
            <option value="">
                Unable to load transactions
            </option>
        `;


        transactionCount.textContent =
            "Could not retrieve audit records.";


        showError(
            error.message ||
            "Failed to load available transactions."
        );

    } finally {

        transactionSelect.disabled = false;

        refreshButton.disabled = false;

    }

}


/* =========================================================
   TIMELINE ITEM
========================================================= */

function addTimelineItem(
    title,
    meta,
    timestamp = ""
) {

    const item =
        document.createElement("div");

    item.className =
        "timeline-item";


    const dot =
        document.createElement("div");

    dot.className =
        "timeline-dot";


    const titleElement =
        document.createElement("div");

    titleElement.className =
        "timeline-title";

    titleElement.textContent =
        title;


    const metaElement =
        document.createElement("div");

    metaElement.className =
        "timeline-meta";

    metaElement.textContent =
        meta;


    item.appendChild(dot);

    item.appendChild(titleElement);

    item.appendChild(metaElement);


    if (timestamp) {

        const timeElement =
            document.createElement("div");

        timeElement.className =
            "timeline-meta";

        timeElement.style.marginTop =
            "6px";

        timeElement.style.fontSize =
            "12px";

        timeElement.textContent =
            timestamp;

        item.appendChild(
            timeElement
        );

    }


    timeline.appendChild(item);

}


/* =========================================================
   RENDER AUDIT
========================================================= */

function renderAudit(data) {

    const events =
        Array.isArray(data.events)
            ? data.events
            : [];


    if (events.length === 0) {

        resetView();

        showError(
            "No audit events found for this transaction."
        );

        return;

    }


    hideError();

    hideSuccess();


    emptyState.style.display =
        "none";

    summarySection.style.display =
        "block";

    timelineSection.style.display =
        "block";

    rawSection.style.display =
        "block";


    const transactionId =
        data.transaction_id ||
        events[0]?.transaction_id ||
        "Unknown";


    /*
     * Newest event first.
     */

    const orderedEvents =
        [...events].reverse();


    const latestEvent =
        orderedEvents[0];


    /* =====================================================
       SUMMARY
    ===================================================== */

    const action =
        latestEvent.final_action ||
        latestEvent.preferred_action ||
        "—";


    let policyStatus =
        "Not evaluated";


    if (
        latestEvent.policy_allowed === true
    ) {

        policyStatus =
            "Approved";

    } else if (
        latestEvent.policy_allowed === false
    ) {

        policyStatus =
            "Rejected";

    }


    let status =
        "Analyzed";


    if (
        latestEvent.execution
    ) {

        if (
            latestEvent.execution.recovered
        ) {

            status =
                "Recovered";

        } else {

            status =
                "Recovery Failed";

        }

    }


    summaryTransaction.textContent =
        transactionId;

    summaryAction.textContent =
        formatAction(action);

    summaryPolicy.textContent =
        policyStatus;

    summaryStatus.textContent =
        status;


    /* =====================================================
       TIMELINE
    ===================================================== */

    timeline.innerHTML = "";


    orderedEvents.forEach(
        event => {

            const action =
                event.final_action ||
                event.preferred_action ||
                "—";


            const timestamp =
                formatDate(
                    event.timestamp
                );


            let title =
                "Transaction analyzed";


            if (
                event.execution
            ) {

                if (
                    event.execution.recovered
                ) {

                    title =
                        "Payment successfully recovered";

                } else {

                    title =
                        "Recovery attempt failed";

                }

            } else if (
                event.policy_allowed === false
            ) {

                title =
                    "Recovery blocked by policy";

            } else {

                title =
                    "Transaction analyzed";

            }


            let description =
                `Action: ${formatAction(action)}`;


            if (
                event.execution
            ) {

                if (
                    event.execution.recovered
                ) {

                    const amount =
                        event.execution
                            .amount_recovered ?? 0;


                    description +=
                        ` • SUCCESS • ${formatCurrency(
                            amount
                        )} recovered`;

                } else {

                    description +=
                        " • Recovery unsuccessful";

                }

            }


            if (
                event.policy_allowed !==
                undefined
            ) {

                description +=
                    event.policy_allowed
                        ? " • Policy approved"
                        : " • Policy blocked";

            }


            if (
                Array.isArray(
                    event.policy_reasons
                ) &&
                event.policy_reasons.length
            ) {

                description +=
                    ` • ${event.policy_reasons.join(
                        ", "
                    )}`;

            }


            addTimelineItem(
                title,
                description,
                timestamp
            );

        }
    );


    /* =====================================================
       RAW AUDIT
    ===================================================== */

    rawAudit.textContent =
        JSON.stringify(
            data,
            null,
            2
        );

}


/* =========================================================
   LOAD ONE TRANSACTION
========================================================= */

async function loadAuditById(
    transactionId
) {

    transactionId =
        String(transactionId || "").trim();


    if (!transactionId) {

        showError(
            "Please select or enter a transaction ID."
        );

        return;

    }


    hideError();

    hideSuccess();


    searchButton.disabled =
        true;

    selectLoadButton.disabled =
        true;


    try {

        const response =
            await fetch(
                `${API_BASE}/audit/${encodeURIComponent(
                    transactionId
                )}`,
                {
                    method: "GET",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


        if (
            response.status === 404
        ) {

            throw new Error(
                `No audit record found for transaction "${transactionId}".`
            );

        }


        if (!response.ok) {

            let message =
                `Unable to load audit (${response.status})`;


            try {

                const errorData =
                    await response.json();


                if (
                    errorData.detail
                ) {

                    if (
                        typeof errorData.detail ===
                        "string"
                    ) {

                        message =
                            errorData.detail;

                    } else if (
                        errorData.detail.message
                    ) {

                        message =
                            errorData.detail.message;

                    }

                }

            } catch (_) {

                // Ignore invalid JSON.

            }


            throw new Error(message);

        }


        const data =
            await response.json();


        renderAudit(data);


        transactionInput.value =
            transactionId;

        transactionSelect.value =
            transactionId;


        showSuccess(
            `Audit loaded for ${transactionId}.`
        );


    } catch (error) {

        resetView();


        showError(
            error.message ||
            "Failed to load audit information."
        );


        console.error(
            "Audit loading failed:",
            error
        );

    } finally {

        searchButton.disabled =
            false;

        selectLoadButton.disabled =
            false;

    }

}


/* =========================================================
   MANUAL SEARCH
========================================================= */

async function loadAudit() {

    const transactionId =
        transactionInput.value.trim();


    await loadAuditById(
        transactionId
    );

}


/* =========================================================
   SELECTED TRANSACTION
========================================================= */

async function loadSelectedAudit() {

    const transactionId =
        transactionSelect.value;


    if (!transactionId) {

        showError(
            "Please select a transaction first."
        );

        return;

    }


    await loadAuditById(
        transactionId
    );

}


/* =========================================================
   EVENTS
========================================================= */

searchButton.addEventListener(
    "click",
    loadAudit
);


selectLoadButton.addEventListener(
    "click",
    loadSelectedAudit
);


refreshButton.addEventListener(
    "click",
    loadAvailableTransactions
);


transactionInput.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter"
        ) {

            loadAudit();

        }

    }
);


transactionSelect.addEventListener(
    "change",
    () => {

        const selectedId =
            transactionSelect.value;


        if (selectedId) {

            transactionInput.value =
                selectedId;

        }

    }
);


/* =========================================================
   INITIAL LOAD
========================================================= */

loadAvailableTransactions();