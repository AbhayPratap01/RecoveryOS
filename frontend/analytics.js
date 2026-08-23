const DATA_PATH = "../data/";


/* ============================================================
   CSV LOADER
   ============================================================ */

async function loadCSV(filename) {

    const response = await fetch(
        DATA_PATH + filename
    );

    if (!response.ok) {
        throw new Error(
            `Unable to load ${filename}`
        );
    }

    const text = await response.text();

    return parseCSV(text);
}


/* ============================================================
   CSV PARSER
   ============================================================ */

function parseCSV(text) {

    const lines = text
        .trim()
        .split(/\r?\n/);

    if (lines.length < 2) {
        return [];
    }

    const headers = parseCSVLine(
        lines[0]
    );

    return lines
        .slice(1)
        .map(line => {

            const values =
                parseCSVLine(line);

            const row = {};

            headers.forEach(
                (header, index) => {

                    row[header.trim()] =
                        values[index] !== undefined
                            ? values[index].trim()
                            : "";

                }
            );

            return row;
        });
}


/* ============================================================
   CSV LINE PARSER
   Handles quoted commas correctly
   ============================================================ */

function parseCSVLine(line) {

    const result = [];

    let current = "";
    let insideQuotes = false;

    for (
        let i = 0;
        i < line.length;
        i++
    ) {

        const char = line[i];

        if (char === '"') {

            if (
                insideQuotes &&
                line[i + 1] === '"'
            ) {

                current += '"';

                i++;

            }
            else {

                insideQuotes =
                    !insideQuotes;

            }

        }

        else if (
            char === "," &&
            !insideQuotes
        ) {

            result.push(current);

            current = "";

        }

        else {

            current += char;

        }

    }

    result.push(current);

    return result;
}


/* ============================================================
   HELPERS
   ============================================================ */

function number(value) {

    const n = Number(value);

    return Number.isFinite(n)
        ? n
        : 0;
}


/*
   IMPORTANT

   Some datasets store recovery rates as:

       0.5007  -> 50.07%

   Other datasets may store:

       49.55   -> 49.55%

   This helper supports BOTH formats.
*/

function fractionToPercent(value) {

    const n = number(value);

    if (n <= 1) {

        return n * 100;

    }

    return n;
}


function formatPercent(value) {

    return `${number(value).toFixed(2)}%`;
}


function formatNumber(value) {

    return number(value)
        .toLocaleString("en-IN");
}


function formatCurrency(value) {

    return "₹" +
        number(value)
            .toLocaleString(
                "en-IN",
                {
                    maximumFractionDigits: 0
                }
            );
}


function normalize(value) {

    return String(value)
        .trim()
        .toLowerCase();
}


function findRow(
    rows,
    column,
    value
) {

    return rows.find(
        row =>
            normalize(row[column]) ===
            normalize(value)
    );
}


/* ============================================================
   CHART DEFAULTS
   ============================================================ */

Chart.defaults.color =
    "#7f8ba5";

Chart.defaults.font.family =
    "Inter, Arial, sans-serif";


/* ============================================================
   METRICS
   ============================================================ */

function renderMetrics(
    strategyData
) {

    const recoveryOS =
        findRow(
            strategyData,
            "Strategy",
            "RecoveryOS"
        );

    if (!recoveryOS) {

        console.warn(
            "RecoveryOS row not found."
        );

        return;
    }

    const transactions =
        number(
            recoveryOS["Transactions"]
        );

    const recovered =
        number(
            recoveryOS["Recovered"]
        );

    const recoveryRate =
        fractionToPercent(
            recoveryOS["Recovery Rate"]
        );

    const revenue =
        number(
            recoveryOS["Revenue Recovered"]
        );


    document.getElementById(
        "transactions"
    ).textContent =
        formatNumber(
            transactions
        );


    document.getElementById(
        "recoveryRate"
    ).textContent =
        formatPercent(
            recoveryRate
        );


    document.getElementById(
        "recovered"
    ).textContent =
        formatNumber(
            recovered
        );


    document.getElementById(
        "revenue"
    ).textContent =
        formatCurrency(
            revenue
        );
}


/* ============================================================
   STRATEGY CHART
   ============================================================ */

function renderStrategyChart(
    strategyData
) {

    const labels =
        strategyData.map(
            row =>
                row["Strategy"]
        );


    const values =
        strategyData.map(
            row =>
                fractionToPercent(
                    row["Recovery Rate"]
                )
        );


    new Chart(
        document.getElementById(
            "strategyChart"
        ),
        {

            type: "bar",

            data: {

                labels,

                datasets: [
                    {

                        label:
                            "Recovery Rate",

                        data:
                            values,

                        borderRadius: 6,

                        borderWidth: 0
                    }
                ]
            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    },

                    tooltip: {

                        callbacks: {

                            label:
                                function(context) {

                                    return (
                                        " Recovery Rate: " +
                                        formatPercent(
                                            context.raw
                                        )
                                    );

                                }

                        }

                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        suggestedMax: 60,

                        ticks: {

                            callback:
                                value =>
                                    value + "%"

                        }

                    }

                }

            }

        }
    );
}


/* ============================================================
   POLICY SENSITIVITY
   ============================================================ */

function renderPolicyChart(
    policyData
) {

    const order = [
        "Relaxed",
        "Current",
        "Strict"
    ];


    const sorted =
        policyData
            .filter(
                row =>
                    order.includes(
                        row["policy"]
                    )
            )
            .sort(
                (a, b) =>
                    order.indexOf(
                        a["policy"]
                    ) -
                    order.indexOf(
                        b["policy"]
                    )
            );


    const labels =
        sorted.map(
            row =>
                row["policy"]
        );


    /*
       FIX:
       Convert both:

       0.5092 -> 50.92
       49.20  -> 49.20
    */

    const values =
        sorted.map(
            row =>
                fractionToPercent(
                    row["recovery_rate"]
                )
        );


    new Chart(
        document.getElementById(
            "policyChart"
        ),
        {

            type: "bar",

            data: {

                labels,

                datasets: [
                    {

                        label:
                            "Recovery Rate",

                        data:
                            values,

                        borderRadius: 6,

                        borderWidth: 0
                    }
                ]
            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    },

                    tooltip: {

                        callbacks: {

                            label:
                                function(context) {

                                    return (
                                        " Recovery Rate: " +
                                        formatPercent(
                                            context.raw
                                        )
                                    );

                                }

                        }

                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        suggestedMax: 60,

                        ticks: {

                            callback:
                                value =>
                                    value + "%"

                        }

                    }

                }

            }

        }
    );
}


/* ============================================================
   FAILURE REASON
   ============================================================ */

function renderFailureChart(
    failureData
) {

    /*
       Only show Current policy.
    */

    let rows =
        failureData.filter(
            row =>
                normalize(
                    row["policy"]
                ) === "current"
        );


    /*
       If the dataset does not contain
       "Current", use all rows.
    */

    if (rows.length === 0) {

        rows = [
            ...failureData
        ];

    }


    rows.sort(
        (a, b) =>
            fractionToPercent(
                b["recovery_rate"]
            ) -
            fractionToPercent(
                a["recovery_rate"]
            )
    );


    const labels =
        rows.map(
            row =>
                row["failure_reason"]
        );


    /*
       FIX:
       Handles both decimal fractions
       and already-percentage values.
    */

    const values =
        rows.map(
            row =>
                fractionToPercent(
                    row["recovery_rate"]
                )
        );


    new Chart(
        document.getElementById(
            "failureChart"
        ),
        {

            type: "bar",

            data: {

                labels,

                datasets: [
                    {

                        label:
                            "Recovery Rate",

                        data:
                            values,

                        borderRadius: 5,

                        borderWidth: 0
                    }
                ]
            },

            options: {

                indexAxis: "y",

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    },

                    tooltip: {

                        callbacks: {

                            label:
                                function(context) {

                                    return (
                                        " Recovery Rate: " +
                                        formatPercent(
                                            context.raw
                                        )
                                    );

                                }

                        }

                    }

                },

                scales: {

                    x: {

                        beginAtZero: true,

                        suggestedMax: 100,

                        ticks: {

                            callback:
                                value =>
                                    value + "%"

                        }

                    }

                }

            }

        }
    );
}


/* ============================================================
   ROBUSTNESS
   ============================================================ */

function renderRobustnessChart(
    robustnessData
) {

    /*
       Only RecoveryOS.
    */

    const rows =
        robustnessData.filter(
            row =>
                normalize(
                    row["strategy"]
                ) === "recoveryos"
        );


    /*
       Put scenarios in meaningful order.
    */

    const order = [
        "Low Noise",
        "Normal",
        "High Noise",
        "Amount -20%",
        "Amount +20%"
    ];


    rows.sort(
        (a, b) =>
            order.indexOf(
                a["scenario"]
            ) -
            order.indexOf(
                b["scenario"]
            )
    );


    const labels =
        rows.map(
            row =>
                row["scenario"]
        );


    /*
       robustness_summary.csv stores
       values such as:

       0.5007 -> 50.07%
    */

    const values =
        rows.map(
            row =>
                fractionToPercent(
                    row["recovery_rate_mean"]
                )
        );


    new Chart(
        document.getElementById(
            "robustnessChart"
        ),
        {

            type: "bar",

            data: {

                labels,

                datasets: [
                    {

                        label:
                            "Recovery Rate",

                        data:
                            values,

                        borderRadius: 6,

                        borderWidth: 0
                    }
                ]
            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    },

                    tooltip: {

                        callbacks: {

                            label:
                                function(context) {

                                    return (
                                        " Recovery Rate: " +
                                        formatPercent(
                                            context.raw
                                        )
                                    );

                                }

                        }

                    }

                },

                scales: {

                    y: {

                        beginAtZero: true,

                        suggestedMax: 65,

                        ticks: {

                            callback:
                                value =>
                                    value + "%"

                        }

                    }

                }

            }

        }
    );
}


/* ============================================================
   POLICY TABLE
   ============================================================ */

function renderPolicyTable(
    policyData
) {

    const order = [
        "Relaxed",
        "Current",
        "Strict"
    ];


    const rows =
        policyData
            .filter(
                row =>
                    order.includes(
                        row["policy"]
                    )
            )
            .sort(
                (a, b) =>
                    order.indexOf(
                        a["policy"]
                    ) -
                    order.indexOf(
                        b["policy"]
                    )
            );


    let html = `

        <table>

            <thead>

                <tr>

                    <th>
                        Policy
                    </th>

                    <th>
                        Recovery Rate
                    </th>

                    <th>
                        Recovered Revenue
                    </th>

                    <th>
                        Policy Changes
                    </th>

                    <th>
                        Stops
                    </th>

                </tr>

            </thead>

            <tbody>

    `;


    rows.forEach(
        row => {

            const recoveryRate =
                fractionToPercent(
                    row["recovery_rate"]
                );


            html += `

                <tr>

                    <td>

                        <strong>
                            ${row["policy"]}
                        </strong>

                    </td>

                    <td>

                        ${formatPercent(
                            recoveryRate
                        )}

                    </td>

                    <td>

                        ${formatCurrency(
                            row["recovered_revenue"]
                        )}

                    </td>

                    <td>

                        ${formatNumber(
                            row["policy_changes"]
                        )}

                    </td>

                    <td>

                        ${formatNumber(
                            row["stops"]
                        )}

                    </td>

                </tr>

            `;

        }
    );


    html += `

            </tbody>

        </table>

    `;


    document.getElementById(
        "policyTable"
    ).innerHTML = html;
}


/* ============================================================
   API STATUS
   ============================================================ */

async function checkAPI() {

    const status =
        document.querySelector(
            ".api-status"
        );


    try {

        const response =
            await fetch(
                "https://recoveryos-api-eey6.onrender.com/health"
            );


        if (!response.ok) {

            throw new Error(
                "API unavailable"
            );

        }


        status.innerHTML = `

            <span></span>

            API Connected

        `;

    }


    catch {

        status.innerHTML = `

            <span
                style="
                    background:#ef4444;
                "
            ></span>

            API Offline

        `;

    }
}


/* ============================================================
   MAIN INITIALIZATION
   ============================================================ */

async function initializeAnalytics() {

    try {

        /*
           Load all analytics CSV datasets.
        */

        const [

            strategyData,

            policyData,

            failureData,

            robustnessData

        ] = await Promise.all([

            loadCSV(
                "strategy_benchmark.csv"
            ),

            loadCSV(
                "policy_sensitivity_summary.csv"
            ),

            loadCSV(
                "policy_sensitivity_failure_reason.csv"
            ),

            loadCSV(
                "robustness_summary.csv"
            )

        ]);


        console.log(
            "Analytics datasets loaded:",
            {
                strategyData,
                policyData,
                failureData,
                robustnessData
            }
        );


        /*
           Render dashboard.
        */

        renderMetrics(
            strategyData
        );


        renderStrategyChart(
            strategyData
        );


        renderPolicyChart(
            policyData
        );


        renderFailureChart(
            failureData
        );


        renderRobustnessChart(
            robustnessData
        );


        renderPolicyTable(
            policyData
        );


        /*
           Check backend.
        */

        await checkAPI();

    }


    catch (error) {

        console.error(
            "Analytics initialization failed:",
            error
        );


        const status =
            document.querySelector(
                ".api-status"
            );


        if (status) {

            status.innerHTML = `

                <span
                    style="
                        background:#ef4444;
                    "
                ></span>

                Data Load Error

            `;

        }

    }
}


/* ============================================================
   START
   ============================================================ */

initializeAnalytics();