import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from backend.ml_dataset import create_action_dataset
from backend.decision_engine import choose_best_allowed_action
from backend.intervention_model import get_recovery_probability


# ============================================================
# CONFIGURATION
# ============================================================

DATA_PATH = "data/transactions.csv"

ACTIONS = [
    "retry",
    "payment_link",
    "reminder",
]

SEED = 42


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(DATA_PATH)

train_df, test_df = train_test_split(
    df,
    test_size=0.20,
    random_state=SEED,
)

print("=" * 60)
print("        RECOVERYOS")
print("   POLICY SENSITIVITY ANALYSIS")
print("=" * 60)

print()
print(f"Total transactions : {len(df)}")
print(f"Training transactions : {len(train_df)}")
print(f"Test transactions : {len(test_df)}")


# ============================================================
# CREATE ACTION-LEVEL TRAINING DATA
# ============================================================

train_actions = create_action_dataset(
    train_df,
    seed=SEED,
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


# ============================================================
# MODEL
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
                random_state=SEED,
                n_jobs=-1,
                class_weight="balanced",
            ),
        ),
    ]
)


print()
print("Training RecoveryOS model...")

model.fit(
    train_actions[features],
    train_actions["recovered"],
)

print("Model ready.")


# ============================================================
# GENERATE ML PROBABILITIES ONCE
# ============================================================

print()
print("Generating ML probabilities...")

action_records = []

for action in ACTIONS:

    temp = test_df.copy()

    temp["action"] = action

    action_records.append(
        temp[features]
    )


all_action_data = pd.concat(
    action_records,
    ignore_index=True,
)

all_probabilities = model.predict_proba(
    all_action_data
)[:, 1]


n = len(test_df)

probability_map = {
    "retry": all_probabilities[
        0:n
    ],

    "payment_link": all_probabilities[
        n:2 * n
    ],

    "reminder": all_probabilities[
        2 * n:3 * n
    ],
}

print("ML probabilities ready.")


# ============================================================
# POLICY DEFINITIONS
# ============================================================

def relaxed_policy(transaction, action):

    reasons = []

    attempt_number = transaction["attempt_number"]
    failure_reason = transaction["failure_reason"]

    # Relaxed retry limit
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

    # Relaxed policy:
    # payment links are allowed for insufficient balance.

    # Relaxed policy:
    # reminders are allowed for network errors.

    return {
        "allowed": len(reasons) == 0,
        "reasons": reasons,
    }


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

    if amount > 50000:

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

        if failure_reason in [
            "expired_card",
            "authentication_failed",
            "bank_decline",
        ]:
            reasons.append(
                "failure_reason_not_safe_for_retry"
            )

    if action == "payment_link":

        if failure_reason in [
            "insufficient_balance",
            "authentication_failed",
        ]:
            reasons.append(
                "payment_link_restricted"
            )

    if action == "reminder":

        if failure_reason in [
            "network_error",
            "gateway_error",
        ]:
            reasons.append(
                "reminder_not_allowed_for_temporary_failure"
            )

    if amount > 50000:

        reasons.append(
            "high_value_transaction_requires_review"
        )

    return {
        "allowed": len(reasons) == 0,
        "reasons": reasons,
    }


# ============================================================
# EVALUATE POLICY
# ============================================================

def evaluate_policy(
    policy_name,
    policy_checker,
    seed=42,
):

    decisions = []

    for i, (_, transaction) in enumerate(
        test_df.iterrows()
    ):

        probabilities = {
            "retry":
                probability_map["retry"][i],

            "payment_link":
                probability_map["payment_link"][i],

            "reminder":
                probability_map["reminder"][i],
        }

        decision = choose_best_allowed_action(
            transaction=transaction,
            probabilities=probabilities,
            policy_checker=policy_checker,
        )

        record = transaction.to_dict()

        record["preferred_action"] = (
            decision["preferred_action"]
        )

        record["final_action"] = (
            decision["action"]
        )

        record["policy_allowed"] = (
            decision["policy"]["allowed"]
        )

        record["policy_reasons"] = str(
            decision["policy"]["reasons"]
        )

        record["rejected"] = str(
            decision["rejected"]
        )

        decisions.append(record)

    result = pd.DataFrame(decisions)

    # ========================================================
    # Deterministic outcome simulation
    # ========================================================

    rng = np.random.default_rng(seed)

    random_values = rng.random(
        len(result)
    )

    result["recovery_probability"] = [
        get_recovery_probability(
            row,
            row["final_action"]
        )
        if row["final_action"] != "stop"
        else 0.0
        for _, row in result.iterrows()
    ]

    result["recovered"] = (
        (result["final_action"] != "stop")
        &
        (
            random_values
            < result["recovery_probability"]
        )
    ).astype(int)

    # ========================================================
    # Metrics
    # ========================================================

    actionable = (
        result["final_action"] != "stop"
    )

    recovered = (
        actionable
        & (result["recovered"] == 1)
    )

    transactions = len(result)

    recovered_count = int(
        recovered.sum()
    )

    recovery_rate = (
        recovered_count / transactions
        if transactions > 0
        else 0
    )

    recovered_revenue = float(
        result.loc[
            recovered,
            "amount"
        ].sum()
    )

    policy_changes = int(
        (
            result["preferred_action"]
            != result["final_action"]
        ).sum()
    )

    stops = int(
        (
            result["final_action"]
            == "stop"
        ).sum()
    )

    return {
        "policy": policy_name,

        "transactions": transactions,

        "recovered": recovered_count,

        "recovery_rate": recovery_rate,

        "recovered_revenue":
            recovered_revenue,

        "policy_changes":
            policy_changes,

        "stops":
            stops,

        "decisions":
            result,
    }

    # --------------------------------------------------------
    # Deterministic outcome simulation
    # --------------------------------------------------------

    rng = np.random.default_rng(seed)

    random_values = rng.random(
        len(result)
    )

    result["recovery_probability"] = [
        get_recovery_probability(
            row,
            row["final_action"]
        )
        if row["final_action"] != "stop"
        else 0.0
        for _, row in result.iterrows()
    ]

    result["recovered"] = (
        (result["final_action"] != "stop")
        &
        (
            random_values
            < result["recovery_probability"]
        )
    ).astype(int)

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    actionable = (
        result["final_action"] != "stop"
    )

    recovered = (
        actionable
        & (result["recovered"] == 1)
    )

    transactions = len(result)

    recovered_count = int(
        recovered.sum()
    )

    recovery_rate = (
        recovered_count / transactions
        if transactions > 0
        else 0
    )

    recovered_revenue = float(
        result.loc[
            recovered,
            "amount"
        ].sum()
    )

    policy_changes = int(
        (
            result["preferred_action"]
            != result["final_action"]
        ).sum()
    )

    stops = int(
        (result["final_action"] == "stop").sum()
    )

    return {
        "policy": policy_name,
        "transactions": transactions,
        "recovered": recovered_count,
        "recovery_rate": recovery_rate,
        "recovered_revenue": recovered_revenue,
        "policy_changes": policy_changes,
        "stops": stops,
        "decisions": result,
    }


# ============================================================
# RUN POLICIES
# ============================================================

print()
print("Evaluating Relaxed policy...")
relaxed = evaluate_policy(
    "Relaxed",
    relaxed_policy,
    seed=SEED,
)

print("Evaluating Current policy...")
current = evaluate_policy(
    "Current",
    current_policy,
    seed=SEED,
)

print("Evaluating Strict policy...")
strict = evaluate_policy(
    "Strict",
    strict_policy,
    seed=SEED,
)


# ============================================================
# RESULTS TABLE
# ============================================================

summary = pd.DataFrame(
    [
        {
            "policy": relaxed["policy"],
            "recovered": relaxed["recovered"],
            "recovery_rate":
                relaxed["recovery_rate"] * 100,
            "recovered_revenue":
                relaxed["recovered_revenue"],
            "policy_changes":
                relaxed["policy_changes"],
            "stops":
                relaxed["stops"],
        },

        {
            "policy": current["policy"],
            "recovered": current["recovered"],
            "recovery_rate":
                current["recovery_rate"] * 100,
            "recovered_revenue":
                current["recovered_revenue"],
            "policy_changes":
                current["policy_changes"],
            "stops":
                current["stops"],
        },

        {
            "policy": strict["policy"],
            "recovered": strict["recovered"],
            "recovery_rate":
                strict["recovery_rate"] * 100,
            "recovered_revenue":
                strict["recovered_revenue"],
            "policy_changes":
                strict["policy_changes"],
            "stops":
                strict["stops"],
        },
    ]
)


# ============================================================
# DISPLAY
# ============================================================

print()
print("=" * 60)
print("              POLICY COMPARISON")
print("=" * 60)

print(
    summary.to_string(
        index=False,
        formatters={
            "recovery_rate":
                "{:.2f}".format,

            "recovered_revenue":
                "₹{:,.2f}".format,
        },
    )
)


# ============================================================
# IMPACT VS CURRENT
# ============================================================

current_rate = current["recovery_rate"]
current_revenue = current["recovered_revenue"]

impact_rows = []

for result in [
    relaxed,
    current,
    strict,
]:

    impact_rows.append(
        {
            "policy":
                result["policy"],

            "recovery_change":
                (
                    result["recovery_rate"]
                    - current_rate
                ) * 100,

            "revenue_change":
                (
                    result["recovered_revenue"]
                    - current_revenue
                ),

            "policy_change_difference":
                (
                    result["policy_changes"]
                    - current["policy_changes"]
                ),
        }
    )


impact_df = pd.DataFrame(
    impact_rows
)


print()
print("=" * 60)
print("          IMPACT VS CURRENT POLICY")
print("=" * 60)

print(
    impact_df.to_string(
        index=False,
        formatters={
            "recovery_change":
                "{:+.2f}%".format,

            "revenue_change":
                "₹{:+,.2f}".format,
        },
    )
)


# ============================================================
# POLICY OVERRIDES
# ============================================================

print()
print("=" * 60)
print("              POLICY OVERRIDES")
print("=" * 60)

for result in [
    relaxed,
    current,
    strict,
]:

    print()
    print(result["policy"])

    decisions = result["decisions"]

    overrides = decisions[
        decisions["preferred_action"]
        != decisions["final_action"]
    ]

    if len(overrides) == 0:

        print("No policy overrides.")

    else:

        print(
            overrides[
                "policy_reasons"
            ]
            .value_counts()
            .head(10)
            .to_string()
        )


# ============================================================
# FAILURE REASON ANALYSIS
# ============================================================

print()
print("=" * 60)
print("          FAILURE REASON COMPARISON")
print("=" * 60)


failure_tables = []

for result in [
    relaxed,
    current,
    strict,
]:

    temp = result["decisions"].copy()

    grouped = (
        temp.groupby(
            "failure_reason"
        )
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

    grouped["policy"] = result["policy"]

    failure_tables.append(
        grouped
    )


failure_df = pd.concat(
    failure_tables,
    ignore_index=True,
)


print(
    failure_df.to_string(
        index=False,
        formatters={
            "recovery_rate":
                "{:.4f}".format,
        },
    )
)


# ============================================================
# SAVE RESULTS
# ============================================================

summary.to_csv(
    "data/policy_sensitivity_summary.csv",
    index=False,
)

impact_df.to_csv(
    "data/policy_sensitivity_impact.csv",
    index=False,
)

failure_df.to_csv(
    "data/policy_sensitivity_failure_reason.csv",
    index=False,
)


# Save detailed decisions
all_decisions = []

for result in [
    relaxed,
    current,
    strict,
]:

    temp = result["decisions"].copy()

    temp["policy"] = result["policy"]

    all_decisions.append(
        temp
    )


decisions_df = pd.concat(
    all_decisions,
    ignore_index=True,
)


decisions_df.to_csv(
    "data/policy_sensitivity_decisions.csv",
    index=False,
)


# ============================================================
# FINAL MESSAGE
# ============================================================

print()
print("=" * 60)
print("Analysis saved:")
print("data/policy_sensitivity_summary.csv")
print("data/policy_sensitivity_impact.csv")
print("data/policy_sensitivity_failure_reason.csv")
print("data/policy_sensitivity_decisions.csv")
print("=" * 60)