import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from backend.ml_dataset import create_action_dataset
from backend.decision_engine import choose_best_allowed_action
from backend.policy_engine import check_policy
from backend.intervention_model import get_recovery_probability


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv("data/transactions.csv")

train_df, test_df = train_test_split(
    df,
    test_size=0.20,
    random_state=42,
)


# ============================================================
# CREATE TRAINING DATA
# ============================================================

train_actions = create_action_dataset(
    train_df,
    seed=42,
)


# ============================================================
# FEATURES
# ============================================================

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


# ============================================================
# PREPROCESSOR
# ============================================================

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


# ============================================================
# MODEL
# ============================================================

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


print("\nTraining RecoveryOS ML model...")

model.fit(
    X_train,
    y_train,
)

print("Model ready.")


# ============================================================
# ACTIONS
# ============================================================

actions = [
    "retry",
    "payment_link",
    "reminder",
]


# ============================================================
# ANALYSIS
# ============================================================

results = []

rng = np.random.default_rng(42)


for _, transaction in test_df.iterrows():

    action_rows = []

    for action in actions:

        record = transaction.to_dict()
        record["action"] = action

        action_rows.append(record)

    action_df = pd.DataFrame(
        action_rows
    )[features]


    # --------------------------------------------------------
    # ML probabilities
    # --------------------------------------------------------

    probabilities = model.predict_proba(
        action_df
    )[:, 1]


    probability_map = dict(
        zip(
            actions,
            probabilities,
        )
    )


    # --------------------------------------------------------
    # ML ONLY decision
    # --------------------------------------------------------

    ml_action = max(
        probability_map,
        key=probability_map.get,
    )


    # --------------------------------------------------------
    # RECOVERYOS decision
    # --------------------------------------------------------

    decision = choose_best_allowed_action(
        transaction=transaction,
        probabilities=probability_map,
        policy_checker=check_policy,
    )

    recoveryos_action = decision["action"]

    preferred_action = decision["preferred_action"]


    # --------------------------------------------------------
    # Determine whether policy changed the decision
    # --------------------------------------------------------

    policy_changed = (
        ml_action != recoveryos_action
    )


    # --------------------------------------------------------
    # Simulate same transaction outcome
    #
    # Same random value is used for both strategies.
    # This makes the comparison paired and fair.
    # --------------------------------------------------------

    random_value = rng.random()


    ml_probability = (
        0.0
        if ml_action == "stop"
        else get_recovery_probability(
            transaction,
            ml_action,
        )
    )


    recoveryos_probability = (
        0.0
        if recoveryos_action == "stop"
        else get_recovery_probability(
            transaction,
            recoveryos_action,
        )
    )


    ml_recovered = int(
        ml_action != "stop"
        and random_value < ml_probability
    )


    recoveryos_recovered = int(
        recoveryos_action != "stop"
        and random_value < recoveryos_probability
    )


    # --------------------------------------------------------
    # Classify policy impact
    # --------------------------------------------------------

    if not policy_changed:

        impact = "no_change"

    elif recoveryos_recovered > ml_recovered:

        impact = "policy_helped"

    elif recoveryos_recovered < ml_recovered:

        impact = "policy_hurt"

    else:

        impact = "same_outcome"


    # --------------------------------------------------------
    # Store result
    # --------------------------------------------------------

    results.append(
        {
            "transaction_id":
                transaction["transaction_id"],

            "amount":
                transaction["amount"],

            "failure_reason":
                transaction["failure_reason"],

            "ml_action":
                ml_action,

            "ml_probability":
                probability_map[ml_action],

            "preferred_action":
                preferred_action,

            "recoveryos_action":
                recoveryos_action,

            "policy_changed":
                policy_changed,

            "ml_recovery_probability":
                ml_probability,

            "recoveryos_recovery_probability":
                recoveryos_probability,

            "ml_recovered":
                ml_recovered,

            "recoveryos_recovered":
                recoveryos_recovered,

            "impact":
                impact,

            "policy_reasons":
                ", ".join(
                    decision["policy"]["reasons"]
                ),
        }
    )


results_df = pd.DataFrame(results)


# ============================================================
# HEADER
# ============================================================

print("\n")
print("=" * 60)
print("             RECOVERYOS")
print("          POLICY IMPACT ANALYSIS")
print("=" * 60)


# ============================================================
# BASIC METRICS
# ============================================================

total = len(results_df)

changed = results_df[
    results_df["policy_changed"]
]


helped = results_df[
    results_df["impact"] == "policy_helped"
]


hurt = results_df[
    results_df["impact"] == "policy_hurt"
]


same = results_df[
    results_df["impact"] == "same_outcome"
]


unchanged = results_df[
    results_df["impact"] == "no_change"
]


print("\n========== DECISION CHANGES ==========")

print(
    f"Total transactions        : {total}"
)

print(
    f"Policy changed decision  : {len(changed)}"
)

print(
    f"Policy did not change    : {len(unchanged)}"
)

print(
    f"Change rate              : "
    f"{len(changed) / total * 100:.2f}%"
)


# ============================================================
# POLICY IMPACT
# ============================================================

print("\n========== POLICY IMPACT ==========")

print(
    f"Policy helped            : {len(helped)}"
)

print(
    f"Policy hurt              : {len(hurt)}"
)

print(
    f"Same outcome             : {len(same)}"
)


if len(changed) > 0:

    print(
        f"Help rate among changes  : "
        f"{len(helped) / len(changed) * 100:.2f}%"
    )

    print(
        f"Hurt rate among changes  : "
        f"{len(hurt) / len(changed) * 100:.2f}%"
    )


# ============================================================
# RECOVERY COMPARISON
# ============================================================

ml_recovery_rate = (
    results_df["ml_recovered"].mean()
)

recoveryos_recovery_rate = (
    results_df["recoveryos_recovered"].mean()
)


print("\n========== RECOVERY COMPARISON ==========")

print(
    f"ML Only recovery rate    : "
    f"{ml_recovery_rate * 100:.2f}%"
)

print(
    f"RecoveryOS recovery rate : "
    f"{recoveryos_recovery_rate * 100:.2f}%"
)

print(
    f"Difference               : "
    f"{(recoveryos_recovery_rate - ml_recovery_rate) * 100:+.2f}%"
)


# ============================================================
# REVENUE COMPARISON
# ============================================================

ml_revenue = (
    results_df.loc[
        results_df["ml_recovered"] == 1,
        "amount",
    ].sum()
)


recoveryos_revenue = (
    results_df.loc[
        results_df["recoveryos_recovered"] == 1,
        "amount",
    ].sum()
)


print("\n========== REVENUE IMPACT ==========")

print(
    f"ML Only recovered revenue    : "
    f"₹{ml_revenue:,.2f}"
)

print(
    f"RecoveryOS recovered revenue : "
    f"₹{recoveryos_revenue:,.2f}"
)

print(
    f"Revenue difference            : "
    f"₹{recoveryos_revenue - ml_revenue:+,.2f}"
)


# ============================================================
# POLICY CHANGE BREAKDOWN
# ============================================================

print("\n========== POLICY CHANGE BREAKDOWN ==========")

if len(changed) > 0:

    change_table = (
        changed.groupby(
            [
                "ml_action",
                "recoveryos_action",
            ]
        )
        .size()
        .reset_index(
            name="transactions"
        )
        .sort_values(
            "transactions",
            ascending=False,
        )
    )

    print(
        change_table.to_string(
            index=False
        )
    )

else:

    print(
        "No policy-driven action changes."
    )


# ============================================================
# POLICY REASONS
# ============================================================

print("\n========== POLICY REASONS ==========")

blocked_reasons = (
    changed[
        changed["policy_reasons"] != ""
    ]["policy_reasons"]
    .value_counts()
)


if len(blocked_reasons) > 0:

    print(
        blocked_reasons.to_string()
    )

else:

    print(
        "No policy overrides occurred."
    )


# ============================================================
# FAILURE REASON IMPACT
# ============================================================

print("\n========== IMPACT BY FAILURE REASON ==========")

impact_table = (
    changed.groupby(
        [
            "failure_reason",
            "impact",
        ]
    )
    .size()
    .unstack(
        fill_value=0
    )
)


print(
    impact_table.to_string()
)


# ============================================================
# SAVE RESULTS
# ============================================================

output_path = (
    "data/policy_impact_analysis.csv"
)

results_df.to_csv(
    output_path,
    index=False,
)


print("\n")
print("=" * 60)
print(
    f"Analysis saved to: {output_path}"
)
print("=" * 60)