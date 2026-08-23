import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from backend.ml_dataset import create_action_dataset
from backend.intervention_model import get_recovery_probability
from backend.decision_engine import choose_best_allowed_action
from backend.policy_engine import check_policy


# ============================================================
# CONFIGURATION
# ============================================================

SEEDS = [42, 123, 456, 789, 2026]

ACTIONS = [
    "retry",
    "payment_link",
    "reminder",
]


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(
    "data/transactions.csv"
)

train_df, test_df = train_test_split(
    df,
    test_size=0.20,
    random_state=42,
)


# ============================================================
# TRAIN ML MODEL
# ============================================================

print("\nTraining RecoveryOS model...")

train_actions = create_action_dataset(
    train_df,
    seed=42,
)


features = [
    "amount",
    "payment_method",
    "customer_age_days",
    "previous_transactions",
    "previous_successes",
    "historical_success_rate",
    "attempt_number",
    "is_first_purchase",
    "failure_reason",
    "action",
]


categorical_features = [
    "payment_method",
    "failure_reason",
    "action",
]


numeric_features = [
    "amount",
    "customer_age_days",
    "previous_transactions",
    "previous_successes",
    "historical_success_rate",
    "attempt_number",
    "is_first_purchase",
]


X_train = train_actions[features]
y_train = train_actions["recovered"]


preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_features,
        ),
        (
            "numeric",
            "passthrough",
            numeric_features,
        ),
    ]
)


model = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor,
        ),
        (
            "classifier",
            RandomForestClassifier(
                n_estimators=300,
                max_depth=12,
                min_samples_leaf=10,
                random_state=42,
                n_jobs=-1,
                class_weight="balanced",
            ),
        ),
    ]
)


model.fit(
    X_train,
    y_train,
)

print("Model ready.")


# ============================================================
# STRATEGY: ALWAYS RETRY
# ============================================================

def always_retry_actions(test_data):
    return np.full(
        len(test_data),
        "retry",
        dtype=object,
    )


# ============================================================
# STRATEGY: RULE BASED
# ============================================================

def rule_based_actions(test_data):

    actions = np.full(
        len(test_data),
        "stop",
        dtype=object,
    )

    failure = test_data["failure_reason"]
    attempt = test_data["attempt_number"]

    actions[
        failure.isin(
            [
                "network_error",
                "gateway_error",
            ]
        )
    ] = "retry"

    actions[
        failure == "bank_decline"
    ] = "retry"

    actions[
        failure == "insufficient_balance"
    ] = "reminder"

    actions[
        failure == "expired_card"
    ] = "payment_link"

    actions[
        failure == "authentication_failed"
    ] = "reminder"

    actions[
        attempt >= 3
    ] = "stop"

    return actions


# ============================================================
# BUILD BATCH ML DATA
# ============================================================

def build_action_dataframe(test_data):

    frames = []

    for action in ACTIONS:

        action_df = test_data.copy()

        action_df["action"] = action

        frames.append(
            action_df[features]
        )

    return pd.concat(
        frames,
        ignore_index=True,
    )


# ============================================================
# ML ONLY - BATCH VERSION
# ============================================================

def ml_only_actions(
    test_data,
    amount_shift=0.0,
):

    evaluation_data = test_data.copy()

    if amount_shift != 0:

        evaluation_data["amount"] = (
            evaluation_data["amount"]
            * (1 + amount_shift)
        )

    action_df = build_action_dataframe(
        evaluation_data
    )

    probabilities = model.predict_proba(
        action_df
    )[:, 1]

    n = len(evaluation_data)

    probability_matrix = (
        probabilities
        .reshape(
            len(ACTIONS),
            n,
        )
        .T
    )

    best_indices = np.argmax(
        probability_matrix,
        axis=1,
    )

    actions_array = np.array(
        ACTIONS,
        dtype=object,
    )

    return actions_array[
        best_indices
    ]


# ============================================================
# RECOVERYOS - BATCH ML + DECISION ENGINE
# ============================================================

def recoveryos_actions(
    test_data,
    amount_shift=0.0,
):

    evaluation_data = test_data.copy()

    if amount_shift != 0:

        evaluation_data["amount"] = (
            evaluation_data["amount"]
            * (1 + amount_shift)
        )

    # --------------------------------------------------------
    # One batch ML prediction for ALL transactions/actions
    # --------------------------------------------------------

    action_df = build_action_dataframe(
        evaluation_data
    )

    probabilities = model.predict_proba(
        action_df
    )[:, 1]

    n = len(evaluation_data)

    probability_matrix = (
        probabilities
        .reshape(
            len(ACTIONS),
            n,
        )
        .T
    )

    # --------------------------------------------------------
    # Decision engine
    # --------------------------------------------------------

    selected_actions = []

    for i, (_, transaction) in enumerate(
        evaluation_data.iterrows()
    ):

        probability_map = {
            ACTIONS[j]:
                probability_matrix[i, j]
            for j in range(
                len(ACTIONS)
            )
        }

        decision = choose_best_allowed_action(
            transaction=transaction,
            probabilities=probability_map,
            policy_checker=check_policy,
        )

        selected_actions.append(
            decision["action"]
        )

    return np.array(
        selected_actions,
        dtype=object,
    )


# ============================================================
# PRECOMPUTE STRATEGIES
# ============================================================

print("\nPreparing strategy decisions...")

strategy_actions = {}

strategy_actions["Always Retry"] = (
    always_retry_actions(test_df)
)

strategy_actions["Rule Based"] = (
    rule_based_actions(test_df)
)


# ============================================================
# ROBUST OUTCOME SIMULATOR
# ============================================================

def simulate_strategy(
    test_data,
    actions,
    seed,
    noise_level=0.0,
    amount_shift=0.0,
):

    rng = np.random.default_rng(
        seed
    )

    result = test_data.copy()

    if amount_shift != 0:

        result["amount"] = (
            result["amount"]
            * (1 + amount_shift)
        )

    result["action"] = actions

    # --------------------------------------------------------
    # Calculate recovery probability
    # --------------------------------------------------------

    probabilities = []

    for _, row in result.iterrows():

        action = row["action"]

        if action == "stop":

            probability = 0.0

        else:

            probability = (
                get_recovery_probability(
                    row,
                    action,
                )
            )

            if noise_level > 0:

                probability += rng.normal(
                    0,
                    noise_level,
                )

                probability = np.clip(
                    probability,
                    0.0,
                    1.0,
                )

        probabilities.append(
            probability
        )

    result["probability"] = probabilities

    # --------------------------------------------------------
    # Simulate recovery
    # --------------------------------------------------------

    random_values = rng.random(
        len(result)
    )

    result["recovered"] = (
        (result["action"] != "stop")
        & (
            random_values
            < result["probability"]
        )
    ).astype(int)

    return result


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(result):

    transactions = len(result)

    recovered = int(
        result["recovered"].sum()
    )

    attempted = result[
        result["action"] != "stop"
    ]

    attempted_revenue = attempted[
        "amount"
    ].sum()

    recovered_revenue = result.loc[
        result["recovered"] == 1,
        "amount",
    ].sum()

    stops = int(
        (
            result["action"] == "stop"
        ).sum()
    )

    return {
        "transactions": transactions,

        "recovered": recovered,

        "recovery_rate": (
            recovered / transactions
            if transactions > 0
            else 0
        ),

        "recovered_revenue":
            float(recovered_revenue),

        "attempted_revenue":
            float(attempted_revenue),

        "stops":
            stops,
    }


# ============================================================
# SCENARIOS
# ============================================================

scenarios = [

    {
        "name": "Normal",
        "noise": 0.00,
        "amount_shift": 0.00,
    },

    {
        "name": "Low Noise",
        "noise": 0.05,
        "amount_shift": 0.00,
    },

    {
        "name": "High Noise",
        "noise": 0.10,
        "amount_shift": 0.00,
    },

    {
        "name": "Amount +20%",
        "noise": 0.05,
        "amount_shift": 0.20,
    },

    {
        "name": "Amount -20%",
        "noise": 0.05,
        "amount_shift": -0.20,
    },
]


# ============================================================
# MAIN EXPERIMENT
# ============================================================

all_results = []

print("\n")
print("=" * 65)
print("              RECOVERYOS")
print("       ROBUSTNESS & GENERALIZATION")
print("=" * 65)

print(
    f"\nTest transactions: {len(test_df)}"
)

print(
    f"Evaluation seeds: {SEEDS}"
)


for scenario in scenarios:

    scenario_name = scenario["name"]
    noise = scenario["noise"]
    amount_shift = scenario["amount_shift"]

    print("\n" + "=" * 65)
    print(
        f"SCENARIO: {scenario_name}"
    )
    print("=" * 65)

    # --------------------------------------------------------
    # ML decisions must be recomputed for amount-shift cases
    # --------------------------------------------------------

    print(
        "\nPreparing ML decisions..."
    )

    scenario_actions = {}

    scenario_actions["Always Retry"] = (
        strategy_actions["Always Retry"]
    )

    scenario_actions["Rule Based"] = (
        strategy_actions["Rule Based"]
    )

    scenario_actions["ML Only"] = (
        ml_only_actions(
            test_df,
            amount_shift=amount_shift,
        )
    )

    scenario_actions["RecoveryOS"] = (
        recoveryos_actions(
            test_df,
            amount_shift=amount_shift,
        )
    )

    for strategy_name in [
        "Always Retry",
        "Rule Based",
        "ML Only",
        "RecoveryOS",
    ]:

        actions = scenario_actions[
            strategy_name
        ]

        metrics_list = []

        for seed in SEEDS:

            result = simulate_strategy(
                test_data=test_df,
                actions=actions,
                seed=seed,
                noise_level=noise,
                amount_shift=amount_shift,
            )

            metrics = calculate_metrics(
                result
            )

            metrics_list.append(
                metrics
            )

            all_results.append(
                {
                    "scenario":
                        scenario_name,

                    "strategy":
                        strategy_name,

                    "seed":
                        seed,

                    **metrics,
                }
            )

        avg_recovery = np.mean(
            [
                x["recovery_rate"]
                for x in metrics_list
            ]
        )

        std_recovery = np.std(
            [
                x["recovery_rate"]
                for x in metrics_list
            ]
        )

        avg_revenue = np.mean(
            [
                x["recovered_revenue"]
                for x in metrics_list
            ]
        )

        avg_stops = np.mean(
            [
                x["stops"]
                for x in metrics_list
            ]
        )

        print(
            f"\n{strategy_name}"
        )

        print(
            f"  Recovery Rate : "
            f"{avg_recovery * 100:.2f}% "
            f"+/- "
            f"{std_recovery * 100:.2f}%"
        )

        print(
            f"  Revenue       : "
            f"₹{avg_revenue:,.2f}"
        )

        print(
            f"  Avg Stops     : "
            f"{avg_stops:.1f}"
        )


# ============================================================
# FINAL SUMMARY
# ============================================================

results_df = pd.DataFrame(
    all_results
)


summary = (
    results_df
    .groupby(
        [
            "scenario",
            "strategy",
        ]
    )
    .agg(
        recovery_rate_mean=(
            "recovery_rate",
            "mean",
        ),

        recovery_rate_std=(
            "recovery_rate",
            "std",
        ),

        recovered_revenue_mean=(
            "recovered_revenue",
            "mean",
        ),

        recovered_revenue_std=(
            "recovered_revenue",
            "std",
        ),

        stops_mean=(
            "stops",
            "mean",
        ),
    )
    .reset_index()
)


# ============================================================
# RECOVERYOS ADVANTAGE
# ============================================================

print("\n")
print("=" * 65)
print("             RECOVERYOS ADVANTAGE")
print("=" * 65)


for scenario in summary["scenario"].unique():

    scenario_data = summary[
        summary["scenario"] == scenario
    ]

    recoveryos_row = scenario_data[
        scenario_data["strategy"]
        == "RecoveryOS"
    ].iloc[0]

    print(
        f"\nScenario: {scenario}"
    )

    for baseline in [
        "Always Retry",
        "Rule Based",
        "ML Only",
    ]:

        baseline_row = scenario_data[
            scenario_data["strategy"]
            == baseline
        ].iloc[0]

        recovery_difference = (
            recoveryos_row[
                "recovery_rate_mean"
            ]
            -
            baseline_row[
                "recovery_rate_mean"
            ]
        )

        revenue_difference = (
            recoveryos_row[
                "recovered_revenue_mean"
            ]
            -
            baseline_row[
                "recovered_revenue_mean"
            ]
        )

        print(
            f"  vs {baseline}:"
        )

        print(
            f"    Recovery difference : "
            f"{recovery_difference * 100:+.2f}%"
        )

        print(
            f"    Revenue difference  : "
            f"₹{revenue_difference:+,.2f}"
        )


# ============================================================
# SAVE RESULTS
# ============================================================

results_df.to_csv(
    "data/robustness_results.csv",
    index=False,
)

summary.to_csv(
    "data/robustness_summary.csv",
    index=False,
)


print("\n")
print("=" * 65)
print("Analysis saved:")
print(
    "data/robustness_results.csv"
)
print(
    "data/robustness_summary.csv"
)
print("=" * 65)