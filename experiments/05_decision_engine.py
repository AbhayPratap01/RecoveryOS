import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from backend.ml_dataset import create_action_dataset
from backend.decision_engine import (
    choose_best_allowed_action
)
from backend.policy_engine import check_policy


# ============================================
# Load data
# ============================================

df = pd.read_csv(
    "data/transactions.csv"
)


# ============================================
# Split original transactions
# ============================================

train_df, test_df = train_test_split(
    df,
    test_size=0.20,
    random_state=42,
)


# ============================================
# Create action-level data
# ============================================

train_actions = create_action_dataset(
    train_df,
    seed=42,
)


# ============================================
# Features
# ============================================

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


# ============================================
# Preprocessor
# ============================================

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


# ============================================
# Model
# ============================================

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

# ============================================
# Test transactions
# ============================================

results = []

for _, transaction in test_df.head(1000).iterrows():

    action_rows = []

    actions = [
        "retry",
        "payment_link",
        "reminder",
    ]

    for action in actions:

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
            actions,
            probabilities,
        )
    )

    # ========================================
    # Decision engine
    # ========================================

    decision = choose_best_allowed_action(
        transaction=transaction,
        probabilities=probability_map,
        policy_checker=check_policy,
    )

    preferred_action = decision["preferred_action"]

    final_action = decision["action"]

    fallback_used = (
        preferred_action != final_action
        and final_action != "stop"
    )

    policy_rejected_actions = decision["rejected"]

    results.append(
        {
            "transaction_id":
                transaction["transaction_id"],

            "amount":
                transaction["amount"],

            "failure_reason":
                transaction["failure_reason"],

            "retry_probability":
                probability_map["retry"],

            "payment_link_probability":
                probability_map["payment_link"],

            "reminder_probability":
                probability_map["reminder"],

            "preferred_action":
                preferred_action,

            "final_action":
                final_action,

            "fallback_used":
                fallback_used,

            "policy_allowed":
                decision["policy"]["allowed"],

            "policy_rejected_actions":
                str(policy_rejected_actions),

            "policy_reasons":
                ", ".join(
                    decision["policy"]["reasons"]
                ),
        }
    )


results_df = pd.DataFrame(
    results
)


# ============================================
# Display results
# ============================================

print("\n===================================")
print("       RECOVERYOS V3")
print("      DECISION ENGINE")
print("===================================\n")

print(
    results_df[
        [
            "transaction_id",
            "amount",
            "failure_reason",
            "retry_probability",
            "payment_link_probability",
            "reminder_probability",
            "preferred_action",
            "final_action",
            "fallback_used",
        ]
    ].head(20).to_string(
        index=False
    )
)


# ============================================
# Policy metrics
# ============================================

print(
    "\n========== POLICY RESULTS =========="
)

print(
    results_df["final_action"]
    .value_counts()
)


print(
    "\n========== DECISION METRICS =========="
)

print(
    "Total transactions:",
    len(results_df)
)

print(
    "Fallbacks used:",
    results_df["fallback_used"].sum()
)

print(
    "Fallback rate:",
    f"{results_df['fallback_used'].mean():.2%}"
)

print(
    "Final stops:",
    (
        results_df["final_action"] == "stop"
    ).sum()
)


# ============================================
# Policy block reasons
# ============================================

print(
    "\n========== POLICY BLOCK REASONS =========="
)

blocked = results_df[
    results_df["final_action"] == "stop"
]

if len(blocked) == 0:

    print(
        "No transactions were stopped."
    )

else:

    print(
        blocked["policy_reasons"]
        .value_counts()
    )