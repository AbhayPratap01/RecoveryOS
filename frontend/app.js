const API_URL = "https://recoveryos-api-eey6.onrender.com";

let currentTransaction = null;
let currentAnalysis = null;


/* =========================================================
   HELPERS
========================================================= */

function getElement(id) {
    return document.getElementById(id);
}


function getTransactionData() {

    const transactionId = getElement("transactionId");
    const amount = getElement("amount");
    const paymentMethod = getElement("paymentMethod");
    const customerAge = getElement("customerAge");
    const previousTransactions = getElement("previousTransactions");
    const previousSuccesses = getElement("previousSuccesses");
    const historicalRate = getElement("historicalRate");
    const attemptNumber = getElement("attemptNumber");
    const firstPurchase = getElement("firstPurchase");
    const failureReason = getElement("failureReason");

    return {
        transaction_id:
            transactionId ? transactionId.value : "",

        amount:
            amount ? Number(amount.value) : 0,

        payment_method:
            paymentMethod ? paymentMethod.value : "",

        customer_age_days:
            customerAge ? Number(customerAge.value) : 0,

        previous_transactions:
            previousTransactions
                ? Number(previousTransactions.value)
                : 0,

        previous_successes:
            previousSuccesses
                ? Number(previousSuccesses.value)
                : 0,

        historical_success_rate:
            historicalRate
                ? Number(historicalRate.value)
                : 0,

        attempt_number:
            attemptNumber
                ? Number(attemptNumber.value)
                : 1,

        is_first_purchase:
            firstPurchase
                ? firstPurchase.value === "true"
                : false,

        failure_reason:
            failureReason
                ? failureReason.value
                : ""
    };
}

/* =========================================================
   RANDOM TRANSACTION FROM DATASET
========================================================= */

function setFieldValue(id, value) {
    const field = getElement(id);

    if (!field) {
        return;
    }

    if (value === null || value === undefined) {
        return;
    }

    field.value = value;
}


function resetAnalysisUI() {

    currentAnalysis = null;

    const emptyDecision = getElement("emptyDecision");
    const decisionContent = getElement("decisionContent");
    const resultSection = getElement("resultSection");
    const auditSection = getElement("auditSection");
    const error = getElement("error");

    if (emptyDecision) {
        emptyDecision.classList.remove("hidden");
    }

    if (decisionContent) {
        decisionContent.classList.add("hidden");
    }

    if (resultSection) {
        resultSection.classList.add("hidden");
    }

    if (auditSection) {
        auditSection.classList.add("hidden");
    }

    if (error) {
        error.classList.add("hidden");
    }
}


function populateTransaction(transaction) {

    if (!transaction) {
        throw new Error("No transaction data was returned.");
    }

    const transactionId =
        transaction.transaction_id ??
        transaction.transactionId ??
        transaction.id;

    const amount =
        transaction.amount;

    const paymentMethod =
        transaction.payment_method ??
        transaction.paymentMethod;

    const customerAge =
        transaction.customer_age_days ??
        transaction.customerAgeDays ??
        transaction.customer_age;

    const previousTransactions =
        transaction.previous_transactions ??
        transaction.previousTransactions;

    const previousSuccesses =
        transaction.previous_successes ??
        transaction.previousSuccesses;

    const historicalRate =
        transaction.historical_success_rate ??
        transaction.historicalSuccessRate;

    const attemptNumber =
        transaction.attempt_number ??
        transaction.attemptNumber;

    const isFirstPurchase =
        transaction.is_first_purchase ??
        transaction.isFirstPurchase;

    const failureReason =
        transaction.failure_reason ??
        transaction.failureReason;


    setFieldValue(
        "transactionId",
        transactionId
    );

    setFieldValue(
        "amount",
        amount
    );

    setFieldValue(
        "paymentMethod",
        paymentMethod
    );

    setFieldValue(
        "customerAge",
        customerAge
    );

    setFieldValue(
        "previousTransactions",
        previousTransactions
    );

    setFieldValue(
        "previousSuccesses",
        previousSuccesses
    );

    setFieldValue(
        "historicalRate",
        historicalRate
    );

    setFieldValue(
        "attemptNumber",
        attemptNumber
    );

    setFieldValue(
        "firstPurchase",
        Boolean(isFirstPurchase)
            ? "true"
            : "false"
    );

    setFieldValue(
        "failureReason",
        failureReason
    );


    currentTransaction =
        getTransactionData();


    resetAnalysisUI();
}


async function loadRandomTransaction() {

    const button =
        getElement(
            "randomTransactionButton"
        );


    if (button) {

        button.disabled = true;
        button.textContent = "Loading...";
    }


    clearError();


    try {

        const response =
            await fetch(
                `${API_URL}/transactions/random`,
                {
                    method: "GET",
                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            let detail =
                data.detail;


            if (
                typeof detail === "object"
                && detail !== null
            ) {

                detail =
                    detail.message ||
                    detail.detail ||
                    "Unable to load random transaction.";
            }


            throw new Error(
                detail ||
                "Unable to load random transaction."
            );
        }


        /*
         * Backend may return either:
         *
         * {
         *     transaction_id: "...",
         *     amount: ...
         * }
         *
         * OR:
         *
         * {
         *     transaction: {
         *         transaction_id: "...",
         *         ...
         *     }
         * }
         */

        const transaction =
            data.transaction ||
            data;


        populateTransaction(
            transaction
        );


        console.log(
            "Random transaction loaded:",
            transaction
        );


    } catch (error) {

        console.error(
            "Random transaction loading failed:",
            error
        );


        showError(
            `Unable to load random transaction: ${error.message}`
        );


    } finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "🎲 Random Transaction";
        }
    }
}


function initializeRandomTransactionButton() {

    let button =
        getElement(
            "randomTransactionButton"
        );


    /*
     * If button does not already exist
     * in index.html, create it automatically.
     */

    if (!button) {

        const transactionIdInput =
            getElement(
                "transactionId"
            );


        if (!transactionIdInput) {

            console.warn(
                "transactionId input not found."
            );

            return;
        }


        button =
            document.createElement(
                "button"
            );


        button.type = "button";

        button.id =
            "randomTransactionButton";

        button.className =
            "random-transaction-button";

        button.textContent =
            "🎲 Random Transaction";


        /*
         * Styling
         */

        button.style.marginTop =
            "8px";

        button.style.padding =
            "9px 14px";

        button.style.border =
            "1px solid #334155";

        button.style.borderRadius =
            "8px";

        button.style.background =
            "#111827";

        button.style.color =
            "#e2e8f0";

        button.style.cursor =
            "pointer";

        button.style.fontSize =
            "12px";


        /*
         * Put button below transaction ID
         */

        if (
            transactionIdInput.parentElement
        ) {

            transactionIdInput
                .parentElement
                .appendChild(button);
        }
    }


    /*
     * Prevent duplicate event listeners
     */

    if (
        !button.dataset.listenerAttached
    ) {

        button.addEventListener(
            "click",
            loadRandomTransaction
        );


        button.dataset.listenerAttached =
            "true";
    }
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
        Number.isFinite(number) ? number : 0
    );
}


function formatPercent(value) {

    let number = Number(value);

    if (!Number.isFinite(number)) {
        number = 0;
    }

    /*
       Backend probabilities are expected as decimals.
       Example:
       0.6802 -> 68.02%
    */

    return `${(number * 100).toFixed(2)}%`;
}


function formatActionName(action) {

    /*
       Prevent:
       [object Object]

       from appearing if backend returns an object.
    */

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
        .replace(/\b\w/g, char =>
            char.toUpperCase()
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
        .replace(/\b\w/g, char =>
            char.toUpperCase()
        );
}


/* =========================================================
   POLICY REASON FORMATTER
========================================================= */

function formatPolicyReason(reason) {

    if (
        reason === null ||
        reason === undefined
    ) {
        return "Unknown policy restriction";
    }


    /*
       Arrays
    */

    if (Array.isArray(reason)) {

        return reason
            .map(item =>
                formatPolicyReason(item)
            )
            .filter(Boolean)
            .join(", ");
    }


    /*
       Objects

       This is the important fix for:

       [object Object]
    */

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
                    ([key, value]) => {

                        return `${formatFailureReason(
                            key
                        )}: ${formatPolicyReason(
                            value
                        )}`;
                    }
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


    return names[key] ||
        key
            .replaceAll("_", " ")
            .replace(/\b\w/g, char =>
                char.toUpperCase()
            );
}


/* =========================================================
   NORMALIZE BACKEND DATA
========================================================= */

function normalizeRejectedActions(value) {

    if (!value) {
        return [];
    }


    if (Array.isArray(value)) {
        return value;
    }


    /*
       Backend may return:

       {
           "retry": "reason",
           "payment_link": "reason"
       }
    */

    if (
        typeof value === "object"
    ) {

        return Object.entries(value)
            .map(
                ([action, reason]) => ({
                    action,
                    reason
                })
            );
    }


    return [
        {
            action: value
        }
    ];
}


function extractPolicyReasons(detail) {

    if (!detail) {
        return [];
    }


    if (Array.isArray(detail)) {
        return detail;
    }


    if (
        typeof detail === "string"
    ) {

        return [detail];
    }


    if (
        typeof detail === "object"
    ) {

        if (
            Array.isArray(detail.reasons)
        ) {

            return detail.reasons;
        }


        if (
            detail.reason !== undefined
        ) {

            return [
                detail.reason
            ];
        }


        if (
            detail.policy_reason !== undefined
        ) {

            return [
                detail.policy_reason
            ];
        }


        if (
            detail.message !== undefined
        ) {

            return [
                detail.message
            ];
        }


        if (
            detail.detail !== undefined
        ) {

            return [
                detail.detail
            ];
        }
    }


    return [];
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
   ERROR UI
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


    /*
       Hide previous execution result
       until a new recovery is executed.
    */

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
   POLICY DISPLAY
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
                    reason => {

                        return `
                            <div>
                                • ${escapeHtml(
                                    formatPolicyReason(
                                        reason
                                    )
                                )}
                            </div>
                        `;
                    }
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


    /*
       Calculate the raw probability winner.

       This prevents the UI from falsely saying
       "highest probability" when policy rules
       caused another action to be selected.
    */

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
                    undefined &&
                    probabilities[action] !==
                    null
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
        rankedActions[0] ||
        null;


    const reasons = [];


    /*
       Decision reason
    */

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


    /*
       Customer history
    */

    if (
        transaction.previous_transactions !==
        undefined
    ) {

        reasons.push(
            `Customer has ${transaction.previous_transactions} previous transactions.`
        );
    }


    if (
        transaction.previous_successes !==
        undefined
    ) {

        reasons.push(
            `Customer has ${transaction.previous_successes} previous successful transactions.`
        );
    }


    if (
        transaction.historical_success_rate !==
        undefined
    ) {

        reasons.push(
            `Historical customer success rate is ${formatPercent(
                transaction.historical_success_rate
            )}.`
        );
    }


    if (
        transaction.attempt_number !==
        undefined
    ) {

        reasons.push(
            `This is recovery attempt #${transaction.attempt_number}.`
        );
    }


    if (
        transaction.failure_reason
    ) {

        reasons.push(
            `Failure reason: ${formatFailureReason(
                transaction.failure_reason
            )}.`
        );
    }


    /*
       Policy
    */

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


    /*
       Rejected actions

       Handles:

       [
           "retry"
       ]

       OR

       [
           {
               action: "retry",
               reason: "..."
           }
       ]

       OR

       {
           retry: "..."
       }
    */

    const rejectedActions =
        normalizeRejectedActions(
            data.rejected_actions
        );


    rejectedActions.forEach(
        item => {

            let action =
                item;

            let reason =
                null;


            if (
                typeof item === "object" &&
                item !== null
            ) {

                action =
                    item.action ||
                    item.final_action ||
                    item.preferred_action ||
                    item.name ||
                    item.code ||
                    "Recovery action";


                reason =
                    item.reason ??
                    item.policy_reason ??
                    item.message ??
                    item.detail ??
                    null;
            }


            const actionName =
                formatActionName(
                    action
                );


            if (reason) {

                reasons.push(
                    `${actionName} was rejected by policy: ${formatPolicyReason(
                        reason
                    )}.`
                );

            } else {

                reasons.push(
                    `${actionName} was rejected by policy.`
                );
            }
        }
    );


    /*
       Render
    */

    container.innerHTML =
        reasons
            .map(
                reason => {

                    return `
                        <div class="reason-item">

                            <span class="reason-icon">
                                ✓
                            </span>

                            <span>
                                ${escapeHtml(
                                    reason
                                )}
                            </span>

                        </div>
                    `;
                }
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


        /*
           POLICY BLOCKED
        */

        if (
            response.status === 403
        ) {

            const detail =
                data.detail ||
                {};


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


            renderDecisionExplanation({

                ...currentAnalysis,

                policy:
                    blockedPolicy
            });


            displayPolicyBlocked(
                blockedPolicy
            );


            updateResultVisualState(
                false
            );


            return;
        }


        /*
           OTHER HTTP ERRORS
        */

        if (!response.ok) {

            const detail =
                data.detail;


            if (
                detail &&
                typeof detail === "object"
            ) {

                const reasons =
                    Array.isArray(
                        detail.reasons
                    )
                        ? detail.reasons
                            .map(
                                formatPolicyReason
                            )
                            .join(", ")
                        : "";


                throw new Error(
                    `${detail.message ||
                        detail.detail ||
                        "Execution failed"}${
                        reasons
                            ? `: ${reasons}`
                            : ""
                    }`
                );
            }


            throw new Error(
                detail ||
                "Execution failed"
            );
        }


        /*
           SUCCESSFUL HTTP RESPONSE
        */

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
   RESULT VISUAL STATE
========================================================= */

function updateResultVisualState(
    success
) {

    const section =
        getElement(
            "resultSection"
        );


    if (!section) {
        return;
    }


    section.dataset.state =
        success
            ? "success"
            : "failed";


    section.classList.toggle(
        "success",
        success
    );


    section.classList.toggle(
        "failed",
        !success
    );


    /*
       Support several possible icon
       class names from the existing HTML.
    */

    const icon =
        section.querySelector(
            ".result-icon, " +
            ".result-status-icon, " +
            ".status-icon, " +
            ".result-symbol"
        );


    if (icon) {

        icon.textContent =
            success
                ? "✓"
                : "×";


        icon.style.color =
            success
                ? "#22c55e"
                : "#ef4444";


        icon.style.background =
            success
                ? "rgba(34,197,94,0.15)"
                : "rgba(239,68,68,0.15)";
    }
}


/* =========================================================
   POLICY BLOCKED RESULT
========================================================= */

function displayPolicyBlocked(
    policy
) {

    const section =
        getElement(
            "resultSection"
        );


    if (!section) {
        return;
    }


    section.classList.remove(
        "hidden"
    );


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


    /*
       Backend currently does not create
       an execution audit event when it
       returns HTTP 403.
    */

    if (audit) {

        audit.textContent =
            "Policy blocked — execution not performed";


        audit.style.color =
            "#ef4444";
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
   DISPLAY EXECUTION
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


    updateResultVisualState(
        recovered
    );


    const section =
        getElement(
            "resultSection"
        );


    if (section) {

        section.classList.remove(
            "hidden"
        );
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

        if (recovered) {

            status.textContent =
                "Payment Recovered";


            status.style.color =
                "#22c55e";

        } else {

            status.textContent =
                "Recovery Attempt Failed";


            status.style.color =
                "#ef4444";
        }
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
            data.audit_id ||
            "—";


        audit.style.color =
            "";
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
                )}`
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


/* =========================================================
   DISPLAY AUDIT TIMELINE
========================================================= */

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


    timeline.innerHTML =
        "";


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


    /*
       Newest first
    */

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


            /*
               Execution information
            */

            if (
                event.execution
            ) {

                if (
                    event.execution.recovered
                ) {

                    description +=
                        ` • SUCCESS • ${formatCurrency(
                            event.execution
                                .amount_recovered
                        )} recovered`;

                } else {

                    description +=
                        " • Recovery unsuccessful";
                }
            }


            /*
               Policy information
            */

            if (
                event.policy_allowed !==
                undefined
            ) {

                description +=
                    event.policy_allowed
                        ? " • Policy approved"
                        : " • Policy blocked";
            }


            /*
               Timestamp
            */

            let timestamp =
                "";


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
                        getAuditTitle(
                            event
                        )
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


/* =========================================================
   AUDIT TITLE
========================================================= */

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
            ".api-status"
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
                <span
                    style="
                        background:#22c55e;
                    "
                ></span>
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
                    style="
                        background:#ef4444;
                    "
                ></span>
                API Offline
            `;
        }
    }
}


/* =========================================================
   EVENT LISTENERS
========================================================= */

function initializeEventListeners() {

    const analyzeButton =
        getElement(
            "analyzeButton"
        );


    const executeButton =
        getElement(
            "executeButton"
        );


    /*
       These listeners are safe even if
       your HTML already uses onclick.
    */

    if (
        analyzeButton &&
        !analyzeButton.dataset.listenerAttached
    ) {

        analyzeButton.addEventListener(
            "click",
            analyzeTransaction
        );


        analyzeButton.dataset.listenerAttached =
            "true";
    }


    if (
        executeButton &&
        !executeButton.dataset.listenerAttached
    ) {

        executeButton.addEventListener(
            "click",
            executeRecovery
        );


        executeButton.dataset.listenerAttached =
            "true";
    }
}


/* =========================================================
   INITIALIZATION
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeEventListeners();

        initializeRandomTransactionButton();

        checkAPI();

    }
);