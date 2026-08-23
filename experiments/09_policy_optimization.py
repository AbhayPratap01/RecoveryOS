import hashlib
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


# ============================================================
# CONFIGURATION
# ============================================================

ACTIONS = [
    "retry",
    "payment_link",
    "reminder",
]

MAX_AUTOMATED_AMOUNT = 50000


# ============================================================
# POLICY DEFINITIONS
# ============================================================

def current_policy(transaction, action):

    reasons = []

    attempt_number = transaction["attempt_number"]
    amount = transaction["amount"]
    failure_reason = transaction["failure_reason"]

    if action == "retry":

        if attempt_number > 2:
            reasons.append(
                "maximum_retry_attempts_exceeded"
            )

        if failure_reason == "expired_card":
            reasons.append(
                "expired_card_cannot_be_retried"
            )

        if failure_reason == "authentication_failed":
            reasons.append(
                "authentication_failure_requires_new_authentication"
            )

    if action == "payment_link":

        if failure_reason == "insufficient_balance":
            reasons.append(
                "payment_link_not_preferred_for_insufficient_balance"
            )

    if action == "reminder":

        if failure_reason == "network_error":
            reasons.append(
                "temporary_network_error_should_be_retried_first"
            )

    if amount > MAX_AUTOMATED_AMOUNT:

        reasons.append(
            "high_value_transaction_requires_review"
        )

    return {
        "allowed": len(reasons) == 0,
        "reasons": reasons,
    }


def strict_policy(transaction, action):

    reasons = []

    attempt_number = transaction["attempt_number"]
    amount = transaction["amount"]
    failure_reason = transaction["failure_reason"]

    if action == "retry":

        if attempt_number > 1:
            reasons.append(
                "strict_retry_limit_exceeded"
            )

        if failure_reason == "expired_card":
            reasons.append(
                "expired_card_cannot_be_retried"
            )

        if failure_reason == "authentication_failed":
            reasons.append(
                "authentication_failure_requires_new_authentication"
            )

    if action == "payment_link":

        if failure_reason == "insufficient_balance":
            reasons.append(
                "payment_link_not_preferred_for_insufficient_balance"
            )

    if action == "reminder":

        if failure_reason == "network_error":
            reasons.append(
                "temporary_network_error_should_be_retried_first"
            )

    if amount > MAX_AUTOMATED_AMOUNT:

        reasons.append(
            "high_value_transaction_requires_review"
        )

    return {
        "allowed": len(reasons) == 0,
        "reasons": reasons,
    }


def balanced_policy(transaction, action):

    reasons = []

    attempt_number = transaction["attempt_number"]
    amount = transaction["amount"]
    failure_reason = transaction["failure_reason"]

    if action == "retry":

        if attempt_number > 2:
            reasons.append(
                "maximum_retry_attempts_exceeded"
            )

        if failure_reason == "expired_card":
            reasons.append(
                "expired_card_cannot_be_retried"
            )

        if failure_reason == "authentication_failed":
            reasons.append(
                "authentication_failure_requires_new_authentication"
            )

    if action == "reminder":

        if failure_reason == "network_error":
            reasons.append(
                "temporary_network_error_should_be_retried_first"
            )

    if amount > MAX_AUTOMATED_AMOUNT:

        reasons.append(
            "high_value_transaction_requires_review"
        )

    return {
        "allowed": len(reasons) == 0,
        "reasons": reasons,
    }


def recovery_optimized_policy(transaction, action):

    reasons = []

    attempt_number = transaction["attempt_number"]
    amount = transaction["amount"]
    failure_reason = transaction["failure_reason"]

    if action == "retry":

        if attempt_number > 3:
            reasons.append(
                "maximum_retry_attempts_exceeded"
            )

        if failure_reason == "expired_card":
            reasons.append(
                "expired_card_cannot_be_retried"
            )

        if failure_reason == "authentication_failed":
            reasons.append(
                "authentication_failure_requires_new_authentication"
            )

    if amount > MAX_AUTOMATED_AMOUNT:

        reasons.append(
            "high_value_transaction_requires_review"
        )

    return {
        "allowed": len(reasons) == 0,
        "reasons": reasons,
    }


POLICIES = {
    "Current": current_policy,
    "Strict": strict_policy,
    "Balanced": balanced_policy,
    "Recovery Optimized": recovery_optimized_policy,
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


print("\n==============================================")
print("        RECOVERYOS POLICY OPTIMIZATION")
print("==============================================")

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
# TRAIN RECOVERY MODEL
# ============================================================

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


print("\nTraining RecoveryOS model...")

model.fit(
    X_train,
    y_train,
)

print("Model ready.")


# ============================================================
# DETERMINISTIC OUTCOME SIMULATION
# ============================================================

def deterministic_random(transaction_id, action):

    key = (
        str(transaction_id)
        + "_"
        + action
    )

    digest = hashlib.sha256(
        key.encode()
    ).hexdigest()

    value = int(
        digest[:8],
        16
    )

    return value / 0xFFFFFFFF


def simulate_action(
    transaction,
    action,
):

    probability = get_recovery_probability(
        transaction,
        action,
    )

    random_value = deterministic_random(
        transaction["transaction_id"],
        action,
    )

    recovered = (
        random_value < probability
    )

    return int(recovered)


# ============================================================
# EVALUATE ONE POLICY
# ============================================================

def evaluate_policy(
    policy_name,
    policy_checker,
):

    records = []

    for _, transaction in test_df.iterrows():

        action_rows = []

        for action in ACTIONS:

            record = transaction.to_dict()

            record["action"] = action

            action_rows.append(record)

        action_df = pd.DataFrame(
            action_rows
        )[features]

        probabilities = model.predict_proba(
            action_df
        )[:, 1]

        probability_map = dict(
            zip(
                ACTIONS,
                probabilities,
            )
        )

        decision = choose_best_allowed_action(
            transaction=transaction,
            probabilities=probability_map,
            policy_checker=policy_checker,
        )

        final_action = decision["action"]

        if final_action == "stop":

            final_recovered = 0

        else:

            final_recovered = simulate_action(
                transaction,
                final_action,
            )

        records.append(
            {
                "transaction_id":
                    transaction["transaction_id"],

                "amount":
                    transaction["amount"],

                "failure_reason":
                    transaction["failure_reason"],

                "preferred_action":
                    decision["preferred_action"],

                "final_action":
                    final_action,

                "recovered":
                    final_recovered,

                "policy_blocked":
                    (
                        decision["preferred_action"]
                        != final_action
                    ),

                "all_actions_blocked":
                    final_action == "stop",

                "policy_reasons":
                    str(
                        decision["rejected"]
                    ),
            }
        )

    result = pd.DataFrame(records)

    actionable = (
        result["final_action"] != "stop"
    )

    recovered = (
        result["recovered"] == 1
    )

    recovered_revenue = result.loc[
        recovered,
        "amount"
    ].sum()

    attempted_revenue = result.loc[
        actionable,
        "amount"
    ].sum()

    total_recovered = recovered.sum()

    total_transactions = len(result)

    recovery_rate = (
        total_recovered
        / total_transactions
    )

    actionable_recovery_rate = (
        total_recovered
        / actionable.sum()
        if actionable.sum() > 0
        else 0
    )

    policy_changes = (
        result["policy_blocked"]
        .sum()
    )

    stops = (
        result["all_actions_blocked"]
        .sum()
    )

    return {
        "policy":
            policy_name,

        "transactions":
            total_transactions,

        "recovered":
            int(total_recovered),

        "recovery_rate":
            recovery_rate,

        "actionable_recovery_rate":
            actionable_recovery_rate,

        "recovered_revenue":
            float(recovered_revenue),

        "attempted_revenue":
            float(attempted_revenue),

        "policy_changes":
            int(policy_changes),

        "stops":
            int(stops),

        "result":
            result,
    }


# ============================================================
# RUN ALL POLICIES
# ============================================================

evaluations = []

for policy_name, policy_checker in POLICIES.items():

    print(
        f"\nEvaluating {policy_name} policy..."
    )

    evaluation = evaluate_policy(
        policy_name,
        policy_checker,
    )

    evaluations.append(
        evaluation
    )


# ============================================================
# SUMMARY
# ============================================================

summary_rows = []

for evaluation in evaluations:

    summary_rows.append(
        {
            "policy":
                evaluation["policy"],

            "transactions":
                evaluation["transactions"],

            "recovered":
                evaluation["recovered"],

            "recovery_rate":
                evaluation["recovery_rate"],

            "actionable_recovery_rate":
                evaluation[
                    "actionable_recovery_rate"
                ],

            "recovered_revenue":
                evaluation[
                    "recovered_revenue"
                ],

            "attempted_revenue":
                evaluation[
                    "attempted_revenue"
                ],

            "policy_changes":
                evaluation[
                    "policy_changes"
                ],

            "stops":
                evaluation["stops"],
        }
    )


summary_df = pd.DataFrame(
    summary_rows
)


# ============================================================
# DISPLAY POLICY COMPARISON
# ============================================================

print("\n==============================================")
print("              POLICY COMPARISON")
print("==============================================\n")

display_columns = [
    "policy",
    "recovered",
    "recovery_rate",
    "recovered_revenue",
    "policy_changes",
    "stops",
]

display_df = summary_df.copy()

display_df["recovery_rate"] = (
    display_df["recovery_rate"] * 100
).round(2)

display_df["recovered_revenue"] = (
    display_df["recovered_revenue"]
).round(2)

print(
    display_df[
        display_columns
    ].to_string(
        index=False
    )
)


# ============================================================
# FIND BEST POLICIES
# ============================================================

best_recovery = summary_df.loc[
    summary_df["recovery_rate"].idxmax()
]

best_revenue = summary_df.loc[
    summary_df["recovered_revenue"].idxmax()
]


print("\n==============================================")
print("              BEST POLICIES")
print("==============================================")

print(
    "\nBest recovery rate : "
    f"{best_recovery['policy']}"
)

print(
    "Recovery rate      : "
    f"{best_recovery['recovery_rate'] * 100:.2f}%"
)

print(
    "\nBest recovered revenue : "
    f"{best_revenue['policy']}"
)

print(
    "Recovered revenue     : "
    f"₹{best_revenue['recovered_revenue']:,.2f}"
)


# ============================================================
# COMPARE AGAINST CURRENT POLICY
# ============================================================

current = summary_df[
    summary_df["policy"] == "Current"
].iloc[0]


print("\n==============================================")
print("          IMPACT VS CURRENT POLICY")
print("==============================================")

comparison_rows = []

for _, row in summary_df.iterrows():

    recovery_difference = (
        row["recovery_rate"]
        - current["recovery_rate"]
    )

    revenue_difference = (
        row["recovered_revenue"]
        - current["recovered_revenue"]
    )

    comparison_rows.append(
        {
            "policy":
                row["policy"],

            "recovery_change":
                recovery_difference,

            "revenue_change":
                revenue_difference,

            "policy_change_difference":
                (
                    row["policy_changes"]
                    - current["policy_changes"]
                ),
        }
    )


comparison_df = pd.DataFrame(
    comparison_rows
)

comparison_df["recovery_change"] = (
    comparison_df["recovery_change"] * 100
)

print(
    comparison_df.to_string(
        index=False
    )
)


# ============================================================
# POLICY REASON ANALYSIS
# ============================================================

print("\n==============================================")
print("            POLICY BLOCK ANALYSIS")
print("==============================================")


for evaluation in evaluations:

    result = evaluation["result"]

    blocked = result[
        result["policy_blocked"]
    ]

    print(
        f"\n{evaluation['policy']}"
    )

    if len(blocked) == 0:

        print(
            "No policy overrides."
        )

        continue

    reasons = (
        blocked["policy_reasons"]
        .value_counts()
        .head(10)
    )

    print(
        reasons.to_string()
    )


# ============================================================
# FAILURE-REASON ANALYSIS
# ============================================================

print("\n==============================================")
print("        FAILURE REASON COMPARISON")
print("==============================================")


for evaluation in evaluations:

    result = evaluation["result"]

    grouped = (
        result
        .groupby("failure_reason")
        .agg(
            transactions=(
                "transaction_id",
                "count",
            ),
            recovered=(
                "recovered",
                "sum",
            ),
        )
        .reset_index()
    )

    grouped["recovery_rate"] = (
        grouped["recovered"]
        / grouped["transactions"]
    )

    print(
        f"\n--- {evaluation['policy']} ---"
    )

    print(
        grouped.to_string(
            index=False
        )
    )


# ============================================================
# SAVE RESULTS
# ============================================================

summary_df.to_csv(
    "data/policy_optimization_summary.csv",
    index=False,
)

comparison_df.to_csv(
    "data/policy_optimization_comparison.csv",
    index=False,
)


print("\n==============================================")
print("Analysis saved:")
print(
    "data/policy_optimization_summary.csv"
)
print(
    "data/policy_optimization_comparison.csv"
)
print("==============================================")