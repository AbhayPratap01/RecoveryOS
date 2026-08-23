import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
    classification_report,
)

from sklearn.model_selection import train_test_split

from backend.ml_dataset import create_action_dataset


# ============================================
# 1. Load original transactions
# ============================================

df = pd.read_csv(
    "data/transactions.csv"
)


# ============================================
# 2. Split ORIGINAL transactions
# ============================================

train_df, test_df = train_test_split(
    df,
    test_size=0.20,
    random_state=42,
)


print("\n===================================")
print("        RECOVERYOS V2.1")
print("     ML MODEL COMPARISON")
print("===================================\n")

print(
    f"Original transactions: {len(df)}"
)

print(
    f"Training transactions: {len(train_df)}"
)

print(
    f"Test transactions: {len(test_df)}"
)


# ============================================
# 3. Expand transactions into interventions
# ============================================

train_actions = create_action_dataset(
    train_df,
    seed=42,
)

test_actions = create_action_dataset(
    test_df,
    seed=123,
)


print(
    f"\nTraining action rows: {len(train_actions)}"
)

print(
    f"Test action rows: {len(test_actions)}"
)


# ============================================
# 4. Features
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

target = "recovered"


X_train = train_actions[features]
y_train = train_actions[target]

X_test = test_actions[features]
y_test = test_actions[target]


# ============================================
# 5. Feature types
# ============================================

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


# ============================================
# 6. Preprocessor
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
# 7. Models
# ============================================

models = {

    "Logistic Regression": Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=5000,
                    C=1.0,
                ),
            ),
        ]
    ),

    "Random Forest": Pipeline(
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
    ),
}


# ============================================
# 8. Train + evaluate
# ============================================

results = {}

for name, model in models.items():

    print("\n-----------------------------------")
    print(f"Training: {name}")
    print("-----------------------------------")

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(
        X_test
    )

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    precision = precision_score(
        y_test,
        predictions,
    )

    recall = recall_score(
        y_test,
        predictions,
    )

    auc = roc_auc_score(
        y_test,
        probabilities,
    )

    results[name] = {
        "model": model,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "roc_auc": auc,
    }

    print(
        f"Accuracy:  {accuracy:.4f}"
    )

    print(
        f"Precision: {precision:.4f}"
    )

    print(
        f"Recall:    {recall:.4f}"
    )

    print(
        f"ROC-AUC:   {auc:.4f}"
    )


# ============================================
# 9. Comparison
# ============================================

print("\n===================================")
print("       MODEL COMPARISON")
print("===================================\n")

for name, metrics in results.items():

    print(
        f"{name:<22}"
        f" AUC={metrics['roc_auc']:.4f}"
        f" | Precision={metrics['precision']:.4f}"
        f" | Recall={metrics['recall']:.4f}"
    )


# ============================================
# 10. Select best model by ROC-AUC
# ============================================

best_name = max(
    results,
    key=lambda name: results[name]["roc_auc"]
)

best_model = results[best_name]["model"]

print(
    f"\nBest model: {best_name}"
)


# ============================================
# 11. Sample transaction decision
# ============================================

sample_transaction = test_df.iloc[0]

sample_rows = []

for action in [
    "retry",
    "payment_link",
    "reminder",
]:

    record = sample_transaction.to_dict()

    record["action"] = action

    sample_rows.append(record)


sample = pd.DataFrame(
    sample_rows
)[features]


sample_probabilities = best_model.predict_proba(
    sample
)[:, 1]


print("\n===================================")
print("       SAMPLE DECISION")
print("===================================\n")

print(
    f"Transaction: "
    f"{sample_transaction['transaction_id']}"
)

print(
    f"Failure: "
    f"{sample_transaction['failure_reason']}"
)

print(
    f"Amount: "
    f"₹{sample_transaction['amount']:,.2f}"
)

for action, probability in zip(
    [
        "retry",
        "payment_link",
        "reminder",
    ],
    sample_probabilities,
):

    print(
        f"{action:<15}"
        f"{probability:.2%}"
    )