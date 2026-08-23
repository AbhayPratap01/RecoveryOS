import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from backend.ml_dataset import create_action_dataset
from backend.decision_engine import choose_best_allowed_action
from backend.policy_engine import check_policy
from backend.simulator import rule_based


# ============================================
# CONFIGURATION
# ============================================

TEST_SIZE = 0.20
RANDOM_STATE = 42


# ============================================
# LOAD DATA
# ============================================

df = pd.read_csv(
    "data/transactions.csv"
)


# ============================================
# TRAIN / TEST SPLIT
# ============================================

train_df, test_df = train_test_split(
    df,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
)


print("\n============================================")
print("          RECOVERYOS BENCHMARK")
print("============================================")

print(
    f"\nTotal transactions : {len(df)}"
)

print(
    f"Training transactions : {len(train_df)}"
)

print(
    f"Test transactions : {len(test_df)}"
)


# ============================================
# CREATE ACTION-LEVEL TRAINING DATA
# ============================================

train_actions = create_action_dataset(
    train_df,
    seed=42,
)


# ============================================
# CREATE ACTION-LEVEL TEST DATA
# ============================================

test_actions = create_action_dataset(
    test_df,
    seed=123,
)


# ============================================
# FEATURES
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
# PREPROCESSOR
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
# ML MODEL
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


print("\nTraining ML recovery model...")

model.fit(
    X_train,
    y_train,
)

print("ML model ready.")


# ============================================
# BUILD TEST OUTCOME LOOKUP
# ============================================

test_outcomes = {}


for _, row in test_actions.iterrows():

    key = (
        row["transaction_id"],
        row["action"],
    )

    test_outcomes[key] = {
        "recovered": int(row["recovered"]),
        "amount": float(row["amount"]),
    }


# ============================================
# AVAILABLE ACTIONS
# ============================================

actions = [
    "retry",
    "payment_link",
    "reminder",
]


# ============================================
# RESULT STORAGE
# ============================================

strategy_results = {
    "Always Retry": [],
    "Rule Based": [],
    "ML Only": [],
    "RecoveryOS": [],
}


# ============================================
# EVALUATE TEST TRANSACTIONS
# ============================================

for _, transaction in test_df.iterrows():

    transaction_id = transaction["transaction_id"]


    # ========================================
    # 1. ALWAYS RETRY
    # ========================================

    always_retry_action = "retry"


    # ========================================
    # 2. RULE BASED
    # ========================================

    rule_result = rule_based(
        pd.DataFrame([transaction])
    )

    # IMPORTANT:
    # rule_based returns a DataFrame.
    # iloc[0] gives the first ROW (Series).
    # We need the actual action value.

    if isinstance(rule_result, pd.DataFrame):

        if "action" in rule_result.columns:
            rule_action = rule_result.iloc[0]["action"]

        elif "final_action" in rule_result.columns:
            rule_action = rule_result.iloc[0]["final_action"]

        else:
            raise ValueError(
                "rule_based() output does not contain "
                "'action' or 'final_action' column."
            )

    elif isinstance(rule_result, pd.Series):

        if "action" in rule_result.index:
            rule_action = rule_result["action"]

        elif "final_action" in rule_result.index:
            rule_action = rule_result["final_action"]

        else:
            raise ValueError(
                "rule_based() Series does not contain "
                "'action' or 'final_action'."
            )

    else:

        rule_action = str(rule_result)


    # ========================================
    # 3. ML PREDICTIONS
    # ========================================

    action_rows = []


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
    # ML ONLY
    # ========================================

    ml_action = max(
        probability_map,
        key=probability_map.get,
    )


    # ========================================
    # 4. RECOVERYOS
    # ========================================

    decision = choose_best_allowed_action(
        transaction=transaction,
        probabilities=probability_map,
        policy_checker=check_policy,
    )


    recoveryos_action = decision["action"]


    # ========================================
    # RECORD OUTCOMES
    # ========================================

    strategies = {
        "Always Retry": always_retry_action,
        "Rule Based": rule_action,
        "ML Only": ml_action,
        "RecoveryOS": recoveryos_action,
    }


    for strategy, action in strategies.items():

        # ------------------------------------
        # STOP = NO RECOVERY ATTEMPT
        # ------------------------------------

        if action == "stop":

            recovered = 0
            revenue = 0.0

        else:

            outcome_key = (
                transaction_id,
                action,
            )

            outcome = test_outcomes.get(
                outcome_key
            )


            if outcome is None:

                recovered = 0
                revenue = 0.0

            else:

                recovered = outcome["recovered"]

                if recovered == 1:

                    revenue = outcome["amount"]

                else:

                    revenue = 0.0


        strategy_results[strategy].append(
            {
                "transaction_id":
                    transaction_id,

                "amount":
                    float(transaction["amount"]),

                "action":
                    action,

                "recovered":
                    recovered,

                "revenue":
                    revenue,
            }
        )


# ============================================
# CALCULATE BENCHMARK METRICS
# ============================================

benchmark = []


for strategy, records in strategy_results.items():

    result_df = pd.DataFrame(
        records
    )


    total_transactions = len(
        result_df
    )


    recovered_transactions = (
        result_df["recovered"].sum()
    )


    total_revenue = (
        result_df["amount"].sum()
    )


    recovered_revenue = (
        result_df["revenue"].sum()
    )


    recovery_rate = (
        recovered_transactions
        / total_transactions
    )


    revenue_recovery_rate = (
        recovered_revenue
        / total_revenue
    )


    benchmark.append(
        {
            "Strategy":
                strategy,

            "Transactions":
                total_transactions,

            "Recovered":
                recovered_transactions,

            "Recovery Rate":
                recovery_rate,

            "Revenue Attempted":
                total_revenue,

            "Revenue Recovered":
                recovered_revenue,

            "Revenue Recovery Rate":
                revenue_recovery_rate,
        }
    )


benchmark_df = pd.DataFrame(
    benchmark
)


# ============================================
# DISPLAY STRATEGY RESULTS
# ============================================

print("\n")
print("============================================")
print("              STRATEGY RESULTS")
print("============================================")


for _, row in benchmark_df.iterrows():

    print(
        f"\n{row['Strategy']}"
    )

    print(
        f"Transactions       : "
        f"{int(row['Transactions'])}"
    )

    print(
        f"Recovered          : "
        f"{int(row['Recovered'])}"
    )

    print(
        f"Recovery Rate      : "
        f"{row['Recovery Rate']:.2%}"
    )

    print(
        f"Revenue Attempted  : "
        f"₹{row['Revenue Attempted']:,.2f}"
    )

    print(
        f"Revenue Recovered  : "
        f"₹{row['Revenue Recovered']:,.2f}"
    )

    print(
        f"Revenue Recovery   : "
        f"{row['Revenue Recovery Rate']:.2%}"
    )


# ============================================
# RECOVERYOS ADVANTAGE
# ============================================

recoveryos_row = benchmark_df[
    benchmark_df["Strategy"]
    == "RecoveryOS"
].iloc[0]


print("\n")
print("============================================")
print("           RECOVERYOS ADVANTAGE")
print("============================================")


for strategy in [
    "Always Retry",
    "Rule Based",
    "ML Only",
]:

    baseline = benchmark_df[
        benchmark_df["Strategy"]
        == strategy
    ].iloc[0]


    revenue_difference = (
        recoveryos_row["Revenue Recovered"]
        - baseline["Revenue Recovered"]
    )


    recovery_difference = (
        recoveryos_row["Recovery Rate"]
        - baseline["Recovery Rate"]
    )


    print(
        f"\nRecoveryOS vs {strategy}"
    )


    print(
        f"Revenue difference : "
        f"₹{revenue_difference:,.2f}"
    )


    print(
        f"Recovery rate diff : "
        f"{recovery_difference:+.2%}"
    )


# ============================================
# ACTION DISTRIBUTION
# ============================================

recoveryos_records = pd.DataFrame(
    strategy_results["RecoveryOS"]
)


print("\n")
print("============================================")
print("       RECOVERYOS ACTION DISTRIBUTION")
print("============================================")


print(
    recoveryos_records[
        "action"
    ].value_counts()
)


# ============================================
# SAVE RESULTS
# ============================================

benchmark_df.to_csv(
    "data/strategy_benchmark.csv",
    index=False,
)


print("\n")
print("============================================")
print("Benchmark saved to:")
print("data/strategy_benchmark.csv")
print("============================================")