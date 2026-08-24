const API_URL =
    "https://recoveryos-api-eey6.onrender.com";


let currentTransaction = null;
let currentAnalysis = null;


/* =========================================================
   HELPERS
========================================================= */

function getElement(id) {
    return document.getElementById(id);
}


function getTransactionData() {

    return {

        transaction_id:
            getElement("transactionId")?.value.trim() || "",

        amount:
            Number(
                getElement("amount")?.value || 0
            ),

        payment_method:
            getElement("paymentMethod")?.value || "",

        customer_age_days:
            Number(
                getElement("customerAge")?.value || 0
            ),

        previous_transactions:
            Number(
                getElement("previousTransactions")?.value || 0
            ),

        previous_successes:
            Number(
                getElement("previousSuccesses")?.value || 0
            ),

        historical_success_rate:
            Number(
                getElement("historicalRate")?.value || 0
            ),

        attempt_number:
            Number(
                getElement("attemptNumber")?.value || 1
            ),

        is_first_purchase:
            getElement("firstPurchase")?.value === "true",

        failure_reason:
            getElement("failureReason")?.value || ""
    };
}


/* =========================================================
   FORMATTING
========================================================= */

function formatCurrency(value) {

    const number = Number(value);

    return new Intl.NumberFormat(
        "en-IN",
        {
            style: "currency",
            currency: "INR",
            maximumFractionDigits: 2
        }
    ).format(
        Number.isFinite(number)
            ? number
            : 0
    );
}


function formatPercent(value) {

    const number =
        Number(value) || 0;

    return `${(
        number * 100
    ).toFixed(2)}%`;
}


function formatActionName(action) {

    if (
        action &&
        typeof action === "object"
    ) {

        action =
            action.action ||
            action.final_action ||
            action.preferred_action ||
            action.name ||
            action.code ||
            "";
    }


    const names = {

        retry:
            "Retry",

        payment_link:
            "Payment Link",

        reminder:
            "Reminder"
    };


    const key =
        String(action || "")
            .trim()
            .toLowerCase();


    if (names[key]) {
        return names[key];
    }


    if (!key) {
        return "Recovery Action";
    }


    return key
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            char => char.toUpperCase()
        );
}


function formatFailureReason(reason) {

    if (
        reason === null ||
        reason === undefined
    ) {

        return "Unknown";
    }


    return String(reason)
        .replaceAll("_", " ")
        .replace(
            /\b\w/g,
            char => char.toUpperCase()
        );
}


/* =========================================================
   POLICY REASON
========================================================= */

function formatPolicyReason(reason) {

    if (
        reason === null ||
        reason === undefined
    ) {

        return "Unknown policy restriction";
    }


    if (Array.isArray(reason)) {

        return reason
            .map(
                item =>
                    formatPolicyReason(item)
            )
            .filter(Boolean)
            .join(", ");
    }


    if (
        typeof reason === "object"
    ) {

        const nested =
            reason.reason ??
            reason.policy_reason ??
            reason.code ??
            reason.message ??
            reason.detail ??
            reason.name;


        if (
            nested !== undefined &&
            nested !== null
        ) {

            return formatPolicyReason(
                nested
            );
        }


        const entries =
            Object.entries(reason);


        if (entries.length > 0) {

            return entries
                .map(
                    ([key, value]) =>
                        `${formatFailureReason(
                            key
                        )}: ${formatPolicyReason(
                            value
                        )}`
                )
                .join(", ");
        }


        return "Unknown policy restriction";
    }


    const names = {

        maximum_retry_attempts_exceeded:
            "Maximum retry attempts exceeded",

        expired_card_cannot_be_retried:
            "Expired card cannot be retried",

        authentication_failure_requires_new_authentication:
            "Authentication failure requires new authentication",

        payment_link_not_preferred_for_insufficient_balance:
            "Payment link is not preferred for insufficient balance",

        temporary_network_error_should_be_retried_first:
            "Temporary network error should be retried first",

        high_value_transaction_requires_review:
            "High-value transaction requires manual review",

        action_blocked_by_policy:
            "Action blocked by policy"
    };


    const key =
        String(reason).trim();


    return (
        names[key] ||
        key
            .replaceAll("_", " ")
            .replace(
                /\b\w/g,
                char => char.toUpperCase()
            )
    );
}


/* =========================================================
   ERROR
========================================================= */

function showError(message) {

    const error =
        getElement("error");


    if (!error) {
        return;
    }


    error.textContent =
        message;

    error.classList.remove(
        "hidden"
    );
}


function clearError() {

    const error =
        getElement("error");


    if (!error) {
        return;
    }


    error.textContent = "";

    error.classList.add(
        "hidden"
    );
}


/* =========================================================
   ANALYZE TRANSACTION
========================================================= */

async function analyzeTransaction() {

    clearError();


    const loading =
        getElement("loading");

    const button =
        getElement("analyzeButton");


    if (loading) {

        loading.classList.remove(
            "hidden"
        );
    }


    if (button) {

        button.disabled = true;
    }


    try {

        currentTransaction =
            getTransactionData();


        if (
            !currentTransaction.transaction_id
        ) {

            throw new Error(
                "Transaction ID is required."
            );
        }


        const response =
            await fetch(
                `${API_URL}/analyze`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            currentTransaction
                        )
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            let detail =
                data.detail;


            if (
                typeof detail === "object"
            ) {

                detail =
                    detail.message ||
                    detail.detail ||
                    "Analysis failed";
            }


            throw new Error(
                detail ||
                "Analysis failed"
            );
        }


        currentAnalysis =
            data;


        displayDecision(
            currentAnalysis
        );


    } catch (error) {

        console.error(
            "Analysis error:",
            error
        );


        showError(
            `Analysis failed: ${error.message}`
        );


    } finally {

        if (loading) {

            loading.classList.add(
                "hidden"
            );
        }


        if (button) {

            button.disabled = false;
        }
    }
}


/* =========================================================
   DISPLAY DECISION
========================================================= */

function displayDecision(data) {

    const emptyDecision =
        getElement("emptyDecision");

    const decisionContent =
        getElement("decisionContent");


    if (emptyDecision) {

        emptyDecision.classList.add(
            "hidden"
        );
    }


    if (decisionContent) {

        decisionContent.classList.remove(
            "hidden"
        );
    }


    const probabilities =
        data.probabilities || {};


    const action =
        data.final_action ||
        data.preferred_action ||
        "";


    const selectedProbability =
        Number(
            probabilities[action] || 0
        );


    const recommendedAction =
        getElement(
            "recommendedAction"
        );


    if (recommendedAction) {

        recommendedAction.textContent =
            formatActionName(
                action
            ).toUpperCase();
    }


    const recommendedProbability =
        getElement(
            "recommendedProbability"
        );


    if (recommendedProbability) {

        recommendedProbability.textContent =
            formatPercent(
                selectedProbability
            );
    }


    updateProbability(
        "retry",
        probabilities.retry
    );

    updateProbability(
        "paymentLink",
        probabilities.payment_link
    );

    updateProbability(
        "reminder",
        probabilities.reminder
    );


    updatePolicy(
        data.policy
    );


    renderDecisionExplanation(
        data
    );


    const resultSection =
        getElement(
            "resultSection"
        );


    if (resultSection) {

        resultSection.classList.add(
            "hidden"
        );
    }


    const auditSection =
        getElement(
            "auditSection"
        );


    if (auditSection) {

        auditSection.classList.add(
            "hidden"
        );
    }
}


/* =========================================================
   PROBABILITY BARS
========================================================= */

function updateProbability(
    name,
    value
) {

    const numericValue =
        Number(value || 0);

    const percent =
        numericValue * 100;


    const bar =
        getElement(
            `${name}Bar`
        );

    const text =
        getElement(
            `${name}Probability`
        );


    if (bar) {

        const safePercent =
            Math.min(
                Math.max(
                    percent,
                    0
                ),
                100
            );


        bar.style.width =
            `${safePercent}%`;
    }


    if (text) {

        text.textContent =
            `${percent.toFixed(2)}%`;
    }
}


/* =========================================================
   POLICY
========================================================= */

function updatePolicy(policy) {

    const status =
        getElement(
            "policyStatus"
        );

    const reasons =
        getElement(
            "policyReasons"
        );


    if (
        !status ||
        !reasons
    ) {
        return;
    }


    if (
        !policy ||
        policy.allowed === true
    ) {

        status.textContent =
            "✓ APPROVED";

        status.style.color =
            "#22c55e";

        reasons.textContent =
            "No policy restrictions.";

        reasons.style.color =
            "#94a3b8";

        return;
    }


    status.textContent =
        "✕ BLOCKED";

    status.style.color =
        "#ef4444";


    const policyReasons =
        Array.isArray(
            policy.reasons
        )
            ? policy.reasons
            : [];


    if (
        policyReasons.length === 0
    ) {

        reasons.textContent =
            "Action blocked by policy.";

    } else {

        reasons.innerHTML =
            policyReasons
                .map(
                    reason =>
                        `<div>• ${escapeHtml(
                            formatPolicyReason(
                                reason
                            )
                        )}</div>`
                )
                .join("");
    }


    reasons.style.color =
        "#ef4444";
}


/* =========================================================
   DECISION EXPLANATION
========================================================= */

function renderDecisionExplanation(
    data
) {

    const container =
        getElement(
            "reasonList"
        );


    if (!container) {
        return;
    }


    if (!currentTransaction) {

        container.innerHTML = `
            <div class="reason-loading">
                Transaction data unavailable.
            </div>
        `;

        return;
    }


    const transaction =
        currentTransaction;


    const probabilities =
        data.probabilities || {};


    const selectedAction =
        data.final_action ||
        data.preferred_action ||
        "";


    const selectedProbability =
        Number(
            probabilities[selectedAction] || 0
        );


    const actions = [
        "retry",
        "payment_link",
        "reminder"
    ];


    const rankedActions =
        actions
            .filter(
                action =>
                    probabilities[action] !==
                    undefined
            )
            .map(
                action => ({
                    action,

                    probability:
                        Number(
                            probabilities[action]
                        ) || 0
                })
            )
            .sort(
                (a, b) =>
                    b.probability -
                    a.probability
            );


    const rawBest =
        rankedActions[0] || null;


    const reasons = [];


    if (selectedAction) {

        if (
            rawBest &&
            rawBest.action ===
                selectedAction
        ) {

            reasons.push(
                `AI selected ${formatActionName(
                    selectedAction
                )} because it has the highest estimated recovery probability of ${formatPercent(
                    selectedProbability
                )}.`
            );

        } else if (rawBest) {

            reasons.push(
                `Decision engine selected ${formatActionName(
                    selectedAction
                )} with an estimated recovery probability of ${formatPercent(
                    selectedProbability
                )}; the raw highest-probability action was ${formatActionName(
                    rawBest.action
                )} at ${formatPercent(
                    rawBest.probability
                )}.`
            );

        } else {

            reasons.push(
                `Decision engine selected ${formatActionName(
                    selectedAction
                )}.`
            );
        }
    }


    reasons.push(
        `Customer has ${transaction.previous_transactions} previous transactions.`
    );


    reasons.push(
        `Customer has ${transaction.previous_successes} previous successful transactions.`
    );


    reasons.push(
        `Historical customer success rate is ${formatPercent(
            transaction.historical_success_rate
        )}.`
    );


    reasons.push(
        `This is recovery attempt #${transaction.attempt_number}.`
    );


    reasons.push(
        `Failure reason: ${formatFailureReason(
            transaction.failure_reason
        )}.`
    );


    if (
        data.policy &&
        data.policy.allowed === true
    ) {

        reasons.push(
            "The selected recovery action passed all policy checks."
        );

    } else if (
        data.policy &&
        Array.isArray(
            data.policy.reasons
        )
    ) {

        data.policy.reasons.forEach(
            reason => {

                reasons.push(
                    `Policy restriction: ${formatPolicyReason(
                        reason
                    )}.`
                );
            }
        );
    }


    container.innerHTML =
        reasons
            .map(
                reason => `
                    <div class="reason-item">
                        <span class="reason-icon">✓</span>
                        <span>
                            ${escapeHtml(reason)}
                        </span>
                    </div>
                `
            )
            .join("");
}


/* =========================================================
   EXECUTE RECOVERY
========================================================= */

async function executeRecovery() {

    if (
        !currentTransaction ||
        !currentAnalysis
    ) {

        showError(
            "Analyze a transaction first."
        );

        return;
    }


    clearError();


    const button =
        getElement(
            "executeButton"
        );


    if (button) {

        button.disabled = true;

        button.textContent =
            "Executing recovery...";
    }


    try {

        const selectedAction =
            currentAnalysis.final_action ||
            currentAnalysis.preferred_action;


        if (!selectedAction) {

            throw new Error(
                "No recovery action was selected."
            );
        }


        const response =
            await fetch(
                `${API_URL}/execute`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            transaction_id:
                                currentTransaction
                                    .transaction_id,

                            action:
                                selectedAction
                        })
                }
            );


        const data =
            await response.json();


        if (
            response.status === 403
        ) {

            const detail =
                data.detail || {};


            const reasons =
                extractPolicyReasons(
                    detail
                );


            const blockedPolicy = {

                allowed: false,

                reasons:
                    reasons.length
                        ? reasons
                        : [
                            "action_blocked_by_policy"
                        ]
            };


            updatePolicy(
                blockedPolicy
            );


            displayPolicyBlocked(
                blockedPolicy
            );


            return;
        }


        if (!response.ok) {

            let message =
                data.detail ||
                "Execution failed";


            if (
                typeof message ===
                "object"
            ) {

                message =
                    message.message ||
                    message.detail ||
                    "Execution failed";
            }


            throw new Error(
                message
            );
        }


        displayExecution(
            data
        );


        await loadAudit();


    } catch (error) {

        console.error(
            "Execution error:",
            error
        );


        showError(
            `Execution failed: ${error.message}`
        );


    } finally {

        if (button) {

            button.disabled = false;

            button.innerHTML =
                'Execute Recovery <span>↗</span>';
        }
    }
}


/* =========================================================
   EXECUTION RESULT
========================================================= */

function displayExecution(
    data
) {

    const execution =
        data.execution;


    if (!execution) {

        console.warn(
            "Execution response did not contain execution data.",
            data
        );

        return;
    }


    const recovered =
        Boolean(
            execution.recovered
        );


    const section =
        getElement(
            "resultSection"
        );


    if (section) {

        section.classList.remove(
            "hidden"
        );

        section.dataset.state =
            recovered
                ? "success"
                : "failed";
    }


    const status =
        getElement(
            "executionStatus"
        );

    const message =
        getElement(
            "executionMessage"
        );

    const amount =
        getElement(
            "recoveredAmount"
        );

    const audit =
        getElement(
            "auditId"
        );


    if (status) {

        status.textContent =
            recovered
                ? "Payment Recovered"
                : "Recovery Attempt Failed";

        status.style.color =
            recovered
                ? "#22c55e"
                : "#ef4444";
    }


    if (message) {

        message.textContent =
            execution.message ||
            (
                recovered
                    ? "Payment successfully recovered."
                    : "Recovery attempt was unsuccessful."
            );
    }


    if (amount) {

        amount.textContent =
            formatCurrency(
                execution.amount_recovered
            );

        amount.style.color =
            recovered
                ? "#22c55e"
                : "#ef4444";
    }


    if (audit) {

        audit.textContent =
            data.audit_id || "—";
    }
}


/* =========================================================
   POLICY BLOCKED
========================================================= */

function displayPolicyBlocked(
    policy
) {

    const section =
        getElement(
            "resultSection"
        );


    if (section) {

        section.classList.remove(
            "hidden"
        );

        section.dataset.state =
            "failed";
    }


    const status =
        getElement(
            "executionStatus"
        );

    const message =
        getElement(
            "executionMessage"
        );

    const amount =
        getElement(
            "recoveredAmount"
        );

    const audit =
        getElement(
            "auditId"
        );


    if (status) {

        status.textContent =
            "Recovery Action Blocked";

        status.style.color =
            "#ef4444";
    }


    if (message) {

        const reasons =
            policy.reasons || [];


        message.textContent =
            reasons.length
                ? `The recovery action was blocked by policy: ${reasons
                    .map(
                        formatPolicyReason
                    )
                    .join(", ")}.`
                : "The recovery action was blocked by the policy engine.";
    }


    if (amount) {

        amount.textContent =
            formatCurrency(0);

        amount.style.color =
            "#ef4444";
    }


    if (audit) {

        audit.textContent =
            "Policy blocked — execution not performed";

        audit.style.color =
            "#ef4444";
    }
}


/* =========================================================
   AUDIT
========================================================= */

async function loadAudit() {

    if (!currentTransaction) {
        return;
    }


    const transactionId =
        currentTransaction.transaction_id;


    if (!transactionId) {
        return;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/audit/${encodeURIComponent(
                    transactionId
                )}`,
                {
                    method: "GET",
                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );


        if (!response.ok) {

            console.warn(
                "Audit endpoint returned:",
                response.status
            );

            return;
        }


        const data =
            await response.json();


        displayAudit(
            data.events || []
        );


    } catch (error) {

        console.error(
            "Audit loading failed:",
            error
        );
    }
}


function displayAudit(
    events
) {

    const section =
        getElement(
            "auditSection"
        );

    const timeline =
        getElement(
            "auditTimeline"
        );


    if (
        !section ||
        !timeline
    ) {
        return;
    }


    timeline.innerHTML = "";


    if (
        !events ||
        events.length === 0
    ) {

        timeline.innerHTML = `
            <div class="reason-loading">
                No audit events found.
            </div>
        `;

        section.classList.remove(
            "hidden"
        );

        return;
    }


    const orderedEvents =
        [...events].reverse();


    orderedEvents.forEach(
        event => {

            const div =
                document.createElement(
                    "div"
                );


            div.className =
                "timeline-event";


            let description =
                `Action: ${formatActionName(
                    event.final_action ||
                    event.preferred_action
                )}`;


            if (
                event.execution
            ) {

                if (
                    event.execution.recovered
                ) {

                    description +=
                        ` • SUCCESS • ${formatCurrency(
                            event.execution.amount_recovered
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


            let timestamp = "";


            if (
                event.timestamp
            ) {

                const date =
                    new Date(
                        event.timestamp
                    );


                if (
                    !Number.isNaN(
                        date.getTime()
                    )
                ) {

                    timestamp =
                        date.toLocaleString(
                            "en-IN",
                            {
                                dateStyle:
                                    "medium",

                                timeStyle:
                                    "short"
                            }
                        );
                }
            }


            div.innerHTML = `
                <strong>
                    ${escapeHtml(
                        getAuditTitle(event)
                    )}
                </strong>

                <p>
                    ${escapeHtml(
                        description
                    )}
                </p>

                ${
                    timestamp
                        ? `
                            <small>
                                ${escapeHtml(
                                    timestamp
                                )}
                            </small>
                        `
                        : ""
                }
            `;


            timeline.appendChild(
                div
            );
        }
    );


    section.classList.remove(
        "hidden"
    );
}


function getAuditTitle(
    event
) {

    if (
        event.execution &&
        event.execution.recovered
    ) {

        return "Payment successfully recovered";
    }


    if (
        event.execution
    ) {

        return "Recovery attempt failed";
    }


    if (
        event.policy_allowed === false
    ) {

        return "Recovery blocked by policy";
    }


    return "Transaction analyzed";
}


/* =========================================================
   API HEALTH
========================================================= */

async function checkAPI() {

    const apiStatus =
        document.querySelector(
            ".header-status"
        );


    try {

        const response =
            await fetch(
                `${API_URL}/health`
            );


        if (!response.ok) {

            throw new Error(
                "API unavailable"
            );
        }


        if (apiStatus) {

            apiStatus.innerHTML = `
                <span class="status-dot"></span>
                API Connected
            `;
        }


    } catch (error) {

        console.error(
            "API health check failed:",
            error
        );


        if (apiStatus) {

            apiStatus.innerHTML = `
                <span
                    class="status-dot"
                    style="background:#ef4444"
                ></span>
                API Offline
            `;
        }
    }
}


/* =========================================================
   SECURITY
========================================================= */

function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* =========================================================
   INITIALIZATION
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        checkAPI();
    }
);


/*
 * Expose functions globally.
 */

window.analyzeTransaction =
    analyzeTransaction;

window.executeRecovery =
    executeRecovery;