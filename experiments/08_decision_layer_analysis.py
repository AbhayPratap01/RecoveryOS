import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from backend.ml_dataset import create_action_dataset
from backend.decision_engine import (
    rank_actions,
    choose_best_allowed_action,
)
from backend.policy_engine import check_policy
from backend.intervention_model import (
    get_recovery_probability,
)


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


print("\n")
print("=" * 60)
print("          RECOVERYOS")
print("       DECISION LAYER ANALYSIS")
print("=" * 60)

print(
    f"\nTotal transactions : {len(df)}"
)

print(
    f"Training transactions : {len(train_df)}"
)

print(
    f"Test transactions : {len(test_df)}"
)


# ============================================================
# CREATE ACTION TRAINING DATA
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


print("\nTraining ML recovery model...")

model.fit(
    X_train,
    y_train,
)

print("ML model ready.")


# ============================================================
# ACTIONS
# ============================================================

actions = [
    "retry",
    "payment_link",
    "reminder",
]


# ============================================================
# RESULTS
# ============================================================

results = []

rng = np.random.default_rng(42)


# ============================================================
# EVALUATION
# ============================================================

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
    # LAYER 1
    # ML ONLY
    # --------------------------------------------------------

    ml_action = max(
        probability_map,
        key=probability_map.get,
    )


    # --------------------------------------------------------
    # LAYER 2
    # DECISION ENGINE / UTILITY
    # --------------------------------------------------------

    ranked_actions = rank_actions(
        amount=transaction["amount"],
        probabilities=probability_map,
    )

    utility_action = ranked_actions[0][0]


    # --------------------------------------------------------
    # LAYER 3
    # POLICY ENGINE
    # --------------------------------------------------------

    decision = choose_best_allowed_action(
        transaction=transaction,
        probabilities=probability_map,
        policy_checker=check_policy,
    )

    final_action = decision["action"]

    preferred_action = decision["preferred_action"]


    # --------------------------------------------------------
    # Identify layer changes
    # --------------------------------------------------------

    ml_to_utility_changed = (
        ml_action != utility_action
    )

    utility_to_policy_changed = (
        utility_action != final_action
    )

    ml_to_final_changed = (
        ml_action != final_action
    )


    # --------------------------------------------------------
    # Common random number
    #
    # Same random value is used for all strategies
    # on this transaction.
    # --------------------------------------------------------

    random_value = rng.random()


    # --------------------------------------------------------
    # True simulated recovery probabilities
    #
    # These are used ONLY for evaluation.
    # The ML model does not see them.
    # --------------------------------------------------------

    ml_probability = get_recovery_probability(
        transaction,
        ml_action,
    )

    utility_probability = get_recovery_probability(
        transaction,
        utility_action,
    )

    final_probability = (
        0.0
        if final_action == "stop"
        else get_recovery_probability(
            transaction,
            final_action,
        )
    )


    # --------------------------------------------------------
    # Simulated outcomes
    # --------------------------------------------------------

    ml_recovered = int(
        ml_action != "stop"
        and random_value < ml_probability
    )

    utility_recovered = int(
        utility_action != "stop"
        and random_value < utility_probability
    )

    final_recovered = int(
        final_action != "stop"
        and random_value < final_probability
    )


    # --------------------------------------------------------
    # Classify utility impact
    # --------------------------------------------------------

    if not ml_to_utility_changed:

        utility_impact = "no_change"

    elif utility_recovered > ml_recovered:

        utility_impact = "utility_helped"

    elif utility_recovered < ml_recovered:

        utility_impact = "utility_hurt"

    else:

        utility_impact = "same_outcome"


    # --------------------------------------------------------
    # Classify policy impact
    # --------------------------------------------------------

    if not utility_to_policy_changed:

        policy_impact = "no_change"

    elif final_recovered > utility_recovered:

        policy_impact = "policy_helped"

    elif final_recovered < utility_recovered:

        policy_impact = "policy_hurt"

    else:

        policy_impact = "same_outcome"


    # --------------------------------------------------------
    # Store
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

            "utility_action":
                utility_action,

            "preferred_action":
                preferred_action,

            "final_action":
                final_action,

            "ml_probability":
                probability_map[ml_action],

            "utility_probability":
                probability_map[utility_action],

            "ml_true_probability":
                ml_probability,

            "utility_true_probability":
                utility_probability,

            "final_true_probability":
                final_probability,

            "ml_recovered":
                ml_recovered,

            "utility_recovered":
                utility_recovered,

            "final_recovered":
                final_recovered,

            "ml_to_utility_changed":
                ml_to_utility_changed,

            "utility_to_policy_changed":
                utility_to_policy_changed,

            "ml_to_final_changed":
                ml_to_final_changed,

            "utility_impact":
                utility_impact,

            "policy_impact":
                policy_impact,

            "policy_reasons": str(
                decision["rejected"]
                ),
        }
    )


results_df = pd.DataFrame(
    results
)


# ============================================================
# METRIC FUNCTION
# ============================================================

def print_metrics(
    name,
    recovered_column,
):

    recovered = (
        results_df[recovered_column].sum()
    )

    total = len(results_df)

    recovery_rate = (
        recovered / total
    )

    revenue = (
        results_df.loc[
            results_df[recovered_column] == 1,
            "amount",
        ].sum()
    )

    print(
        f"\n{name}"
    )

    print(
        f"  Transactions : {total}"
    )

    print(
        f"  Recovered    : {recovered}"
    )

    print(
        f"  Recovery Rate: "
        f"{recovery_rate * 100:.2f}%"
    )

    print(
        f"  Revenue      : "
        f"₹{revenue:,.2f}"
    )

    return recovery_rate, revenue


# ============================================================
# OVERALL LAYER COMPARISON
# ============================================================

print("\n")
print("=" * 60)
print("              LAYER COMPARISON")
print("=" * 60)


ml_rate, ml_revenue = print_metrics(
    "1. ML ONLY",
    "ml_recovered",
)


utility_rate, utility_revenue = print_metrics(
    "2. ML + DECISION ENGINE",
    "utility_recovered",
)


final_rate, final_revenue = print_metrics(
    "3. RECOVERYOS FINAL",
    "final_recovered",
)


# ============================================================
# LAYER DIFFERENCES
# ============================================================

print("\n")
print("=" * 60)
print("             LAYER IMPACT")
print("=" * 60)


print(
    f"\nDecision engine recovery change:"
    f" {(utility_rate - ml_rate) * 100:+.2f}%"
)

print(
    f"Decision engine revenue change:"
    f" ₹{utility_revenue - ml_revenue:+,.2f}"
)


print(
    f"\nPolicy layer recovery change:"
    f" {(final_rate - utility_rate) * 100:+.2f}%"
)

print(
    f"Policy layer revenue change:"
    f" ₹{final_revenue - utility_revenue:+,.2f}"
)


print(
    f"\nTotal RecoveryOS change:"
    f" {(final_rate - ml_rate) * 100:+.2f}%"
)

print(
    f"Total RecoveryOS revenue change:"
    f" ₹{final_revenue - ml_revenue:+,.2f}"
)


# ============================================================
# DECISION ENGINE IMPACT
# ============================================================

utility_changes = results_df[
    results_df[
        "ml_to_utility_changed"
    ]
]


print("\n")
print("=" * 60)
print("        DECISION ENGINE IMPACT")
print("=" * 60)


print(
    f"\nML → Utility changes:"
    f" {len(utility_changes)}"
)


utility_helped = results_df[
    results_df["utility_impact"]
    == "utility_helped"
]


utility_hurt = results_df[
    results_df["utility_impact"]
    == "utility_hurt"
]


utility_same = results_df[
    results_df["utility_impact"]
    == "same_outcome"
]


print(
    f"Utility helped : {len(utility_helped)}"
)

print(
    f"Utility hurt   : {len(utility_hurt)}"
)

print(
    f"Same outcome   : {len(utility_same)}"
)


# ============================================================
# POLICY IMPACT
# ============================================================

policy_changes = results_df[
    results_df[
        "utility_to_policy_changed"
    ]
]


print("\n")
print("=" * 60)
print("           POLICY LAYER IMPACT")
print("=" * 60)


print(
    f"\nUtility → Final changes:"
    f" {len(policy_changes)}"
)


policy_helped = results_df[
    results_df["policy_impact"]
    == "policy_helped"
]


policy_hurt = results_df[
    results_df["policy_impact"]
    == "policy_hurt"
]


policy_same = results_df[
    results_df["policy_impact"]
    == "same_outcome"
]


print(
    f"Policy helped : {len(policy_helped)}"
)

print(
    f"Policy hurt   : {len(policy_hurt)}"
)

print(
    f"Same outcome  : {len(policy_same)}"
)


# ============================================================
# POLICY REASONS
# ============================================================

print("\n")
print("=" * 60)
print("             POLICY OVERRIDES")
print("=" * 60)


policy_reasons = (
    policy_changes[
        policy_changes["policy_reasons"] != ""
    ]["policy_reasons"]
    .value_counts()
)


if len(policy_reasons) > 0:

    print(
        policy_reasons.to_string()
    )

else:

    print(
        "No explicit policy overrides."
    )


# ============================================================
# ACTION TRANSITIONS
# ============================================================

print("\n")
print("=" * 60)
print("          ML → UTILITY TRANSITIONS")
print("=" * 60)


utility_transitions = (
    utility_changes
    .groupby(
        [
            "ml_action",
            "utility_action",
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


if len(utility_transitions) > 0:

    print(
        utility_transitions.to_string(
            index=False
        )
    )

else:

    print(
        "No ML → Utility changes."
    )


print("\n")
print("=" * 60)
print("          UTILITY → FINAL TRANSITIONS")
print("=" * 60)


policy_transitions = (
    policy_changes
    .groupby(
        [
            "utility_action",
            "final_action",
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


if len(policy_transitions) > 0:

    print(
        policy_transitions.to_string(
            index=False
        )
    )

else:

    print(
        "No Utility → Final changes."
    )


# ============================================================
# FAILURE REASON ANALYSIS
# ============================================================

print("\n")
print("=" * 60)
print("          IMPACT BY FAILURE REASON")
print("=" * 60)


reason_table = (
    results_df
    .groupby(
        "failure_reason"
    )
    .agg(
        transactions=(
            "transaction_id",
            "count",
        ),

        ml_recovered=(
            "ml_recovered",
            "sum",
        ),

        utility_recovered=(
            "utility_recovered",
            "sum",
        ),

        final_recovered=(
            "final_recovered",
            "sum",
        ),
    )
)


reason_table[
    "ml_rate"
] = (
    reason_table["ml_recovered"]
    / reason_table["transactions"]
)


reason_table[
    "utility_rate"
] = (
    reason_table["utility_recovered"]
    / reason_table["transactions"]
)


reason_table[
    "final_rate"
] = (
    reason_table["final_recovered"]
    / reason_table["transactions"]
)


print(
    reason_table.to_string()
)


# ============================================================
# SAVE
# ============================================================

output_path = (
    "data/decision_layer_analysis.csv"
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