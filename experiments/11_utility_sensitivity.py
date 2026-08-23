import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from backend.ml_dataset import create_action_dataset
from backend.intervention_model import get_recovery_probability
from backend.policy_engine import check_policy


# ============================================================
# CONFIGURATION
# ============================================================

ACTIONS = [
    "retry",
    "payment_link",
    "reminder",
]

SEEDS = [
    42,
    123,
    456,
    789,
    2026,
]


# ============================================================
# UTILITY PROFILES
# ============================================================

UTILITY_PROFILES = {

    "Probability Maximizing": {
        "retry": 0.0,
        "payment_link": 0.0,
        "reminder": 0.0,
    },

    "Low Cost": {
        "retry": 0.5,
        "payment_link": 0.25,
        "reminder": 0.125,
    },

    "Current": {
        "retry": 2.0,
        "payment_link": 1.0,
        "reminder": 0.5,
    },

    "High Cost": {
        "retry": 4.0,
        "payment_link": 2.0,
        "reminder": 1.0,
    },

    "Recovery Focused": {
        "retry": 0.1,
        "payment_link": 0.05,
        "reminder": 0.025,
    },
}


FRICTION_COST = {
    "retry": 10.0,
    "payment_link": 5.0,
    "reminder": 2.0,
}


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
# BATCH ML PREDICTIONS
# ============================================================

print("\nGenerating ML probabilities...")

action_frames = []

for action in ACTIONS:

    action_df = test_df.copy()

    action_df["action"] = action

    action_frames.append(
        action_df[features]
    )


all_action_data = pd.concat(
    action_frames,
    ignore_index=True,
)


all_probabilities = model.predict_proba(
    all_action_data
)[:, 1]


n = len(test_df)


probability_matrix = (
    all_probabilities
    .reshape(
        len(ACTIONS),
        n,
    )
    .T
)


print("ML probabilities ready.")


# ============================================================
# HELPER: GET PROBABILITY MAP
# ============================================================

def get_probability_map(index):

    return {
        ACTIONS[j]:
            probability_matrix[index, j]
        for j in range(
            len(ACTIONS)
        )
    }


# ============================================================
# UTILITY DECISION
# ============================================================

def choose_by_utility(
    transaction,
    probabilities,
    action_costs,
):

    scores = {}

    amount = float(
        transaction["amount"]
    )

    for action in ACTIONS:

        recovery_probability = (
            probabilities[action]
        )

        expected_revenue = (
            amount
            * recovery_probability
        )

        score = (
            expected_revenue
            - action_costs[action]
            - FRICTION_COST[action]
        )

        scores[action] = score

    ranked = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return ranked


# ============================================================
# POLICY-AWARE DECISION
# ============================================================

def choose_with_policy(
    transaction,
    probabilities,
    action_costs,
):

    ranked = choose_by_utility(
        transaction=transaction,
        probabilities=probabilities,
        action_costs=action_costs,
    )

    preferred_action = ranked[0][0]

    rejected = []

    for action, score in ranked:

        policy = check_policy(
            transaction,
            action,
        )

        if policy["allowed"]:

            return {
                "preferred_action":
                    preferred_action,

                "final_action":
                    action,

                "score":
                    score,

                "policy_override":
                    action != preferred_action,

                "rejected":
                    rejected,
            }

        rejected.append(
            {
                "action": action,
                "reasons": policy["reasons"],
            }
        )

    return {
        "preferred_action":
            preferred_action,

        "final_action":
            "stop",

        "score":
            0.0,

        "policy_override":
            True,

        "rejected":
            rejected,
    }


# ============================================================
# SIMULATE OUTCOMES
# ============================================================

def simulate(
    actions,
    seed,
):

    rng = np.random.default_rng(
        seed
    )

    result = test_df.copy()

    result["action"] = actions

    probabilities = []

    for _, row in result.iterrows():

        action = row["action"]

        if action == "stop":

            probabilities.append(
                0.0
            )

        else:

            probabilities.append(
                get_recovery_probability(
                    row,
                    action,
                )
            )

    result["true_probability"] = (
        probabilities
    )

    random_values = rng.random(
        len(result)
    )

    result["recovered"] = (
        (result["action"] != "stop")
        &
        (
            random_values
            < result["true_probability"]
        )
    ).astype(int)

    return result


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    result,
):

    recovered = int(
        result["recovered"].sum()
    )

    transactions = len(result)

    recovered_revenue = float(
        result.loc[
            result["recovered"] == 1,
            "amount",
        ].sum()
    )

    return {
        "transactions":
            transactions,

        "recovered":
            recovered,

        "recovery_rate":
            recovered / transactions,

        "recovered_revenue":
            recovered_revenue,

        "stops":
            int(
                (
                    result["action"]
                    == "stop"
                ).sum()
            ),
    }


# ============================================================
# RUN EXPERIMENT
# ============================================================

records = []

decision_records = []


print("\n")
print("=" * 70)
print("              RECOVERYOS")
print("       UTILITY SENSITIVITY ANALYSIS")
print("=" * 70)


for profile_name, action_costs in (
    UTILITY_PROFILES.items()
):

    print(
        f"\nEvaluating: {profile_name}"
    )

    utility_actions = []
    final_actions = []

    policy_overrides = 0

    # --------------------------------------------------------
    # Make decisions once
    # --------------------------------------------------------

    for i, (_, transaction) in enumerate(
        test_df.iterrows()
    ):

        probability_map = (
            get_probability_map(i)
        )

        decision = choose_with_policy(
            transaction=transaction,
            probabilities=probability_map,
            action_costs=action_costs,
        )

        utility_actions.append(
            decision["preferred_action"]
        )

        final_actions.append(
            decision["final_action"]
        )

        if decision["policy_override"]:
            policy_overrides += 1

        decision_records.append(
            {
                "profile":
                    profile_name,

                "transaction_id":
                    transaction[
                        "transaction_id"
                    ],

                "preferred_action":
                    decision[
                        "preferred_action"
                    ],

                "final_action":
                    decision[
                        "final_action"
                    ],

                "policy_override":
                    decision[
                        "policy_override"
                    ],
            }
        )

    # --------------------------------------------------------
    # Simulate across seeds
    # --------------------------------------------------------

    seed_metrics = []

    for seed in SEEDS:

        result = simulate(
            actions=np.array(
                final_actions
            ),
            seed=seed,
        )

        metrics = calculate_metrics(
            result
        )

        seed_metrics.append(
            metrics
        )

        records.append(
            {
                "profile":
                    profile_name,

                "seed":
                    seed,

                **metrics,

                "policy_overrides":
                    policy_overrides,
            }
        )

    # --------------------------------------------------------
    # Aggregate
    # --------------------------------------------------------

    mean_recovery = np.mean(
        [
            x["recovery_rate"]
            for x in seed_metrics
        ]
    )

    std_recovery = np.std(
        [
            x["recovery_rate"]
            for x in seed_metrics
        ]
    )

    mean_revenue = np.mean(
        [
            x["recovered_revenue"]
            for x in seed_metrics
        ]
    )

    mean_stops = np.mean(
        [
            x["stops"]
            for x in seed_metrics
        ]
    )

    print(
        f"\n{profile_name}"
    )

    print(
        f"  Recovery Rate : "
        f"{mean_recovery * 100:.2f}% "
        f"+/- "
        f"{std_recovery * 100:.2f}%"
    )

    print(
        f"  Revenue       : "
        f"₹{mean_revenue:,.2f}"
    )

    print(
        f"  Policy Overrides : "
        f"{policy_overrides}"
    )

    print(
        f"  Avg Stops        : "
        f"{mean_stops:.1f}"
    )


# ============================================================
# RESULTS DATAFRAME
# ============================================================

results_df = pd.DataFrame(
    records
)


summary = (
    results_df
    .groupby("profile")
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

        recovered_mean=(
            "recovered",
            "mean",
        ),

        stops_mean=(
            "stops",
            "mean",
        ),

        policy_overrides=(
            "policy_overrides",
            "first",
        ),
    )
    .reset_index()
)


# ============================================================
# ACTION DISTRIBUTION
# ============================================================

decision_df = pd.DataFrame(
    decision_records
)


print("\n")
print("=" * 70)
print("              ACTION DISTRIBUTION")
print("=" * 70)


for profile in UTILITY_PROFILES:

    profile_data = decision_df[
        decision_df["profile"]
        == profile
    ]

    print(
        f"\n{profile}"
    )

    print(
        profile_data[
            "final_action"
        ].value_counts()
    )


# ============================================================
# BEST PROFILE
# ============================================================

best_recovery = summary.loc[
    summary[
        "recovery_rate_mean"
    ].idxmax()
]

best_revenue = summary.loc[
    summary[
        "recovered_revenue_mean"
    ].idxmax()
]


print("\n")
print("=" * 70)
print("              BEST UTILITY PROFILES")
print("=" * 70)

print(
    "\nBest recovery profile:"
)

print(
    best_recovery["profile"]
)

print(
    f"Recovery Rate: "
    f"{best_recovery['recovery_rate_mean'] * 100:.2f}%"
)


print(
    "\nBest revenue profile:"
)

print(
    best_revenue["profile"]
)

print(
    f"Recovered Revenue: "
    f"₹{best_revenue['recovered_revenue_mean']:,.2f}"
)


# ============================================================
# COMPARE AGAINST ML-ONLY
# ============================================================

ml_only_actions = []

for i in range(
    len(test_df)
):

    probabilities = (
        probability_matrix[i]
    )

    best_index = np.argmax(
        probabilities
    )

    ml_only_actions.append(
        ACTIONS[best_index]
    )


ml_results = []

for seed in SEEDS:

    result = simulate(
        actions=np.array(
            ml_only_actions
        ),
        seed=seed,
    )

    ml_results.append(
        calculate_metrics(
            result
        )
    )


ml_recovery = np.mean(
    [
        x["recovery_rate"]
        for x in ml_results
    ]
)

ml_revenue = np.mean(
    [
        x["recovered_revenue"]
        for x in ml_results
    ]
)


print("\n")
print("=" * 70)
print("              ML ONLY BASELINE")
print("=" * 70)

print(
    f"\nRecovery Rate : "
    f"{ml_recovery * 100:.2f}%"
)

print(
    f"Revenue       : "
    f"₹{ml_revenue:,.2f}"
)


# ============================================================
# SAVE
# ============================================================

results_df.to_csv(
    "data/utility_sensitivity_results.csv",
    index=False,
)

summary.to_csv(
    "data/utility_sensitivity_summary.csv",
    index=False,
)

decision_df.to_csv(
    "data/utility_sensitivity_decisions.csv",
    index=False,
)


print("\n")
print("=" * 70)
print("Analysis saved:")
print(
    "data/utility_sensitivity_results.csv"
)
print(
    "data/utility_sensitivity_summary.csv"
)
print(
    "data/utility_sensitivity_decisions.csv"
)
print("=" * 70)