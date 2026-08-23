from pathlib import Path
import os

import pandas as pd

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from backend.ml_dataset import create_action_dataset
from backend.decision_engine import choose_best_allowed_action
from backend.policy_engine import check_policy

from backend.executor import execute_action

from backend.audit import (
    create_audit_event,
    get_audit_log,
    get_transaction_audit,
)

from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
)

# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="RecoveryOS",
    description="AI-powered payment recovery decision engine",
    version="1.0.0",
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://127.0.0.1:5500"
)

ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]


app.add_middleware(
    CORSMiddleware,

    allow_origins=ALLOWED_ORIGINS,

    allow_credentials=True,

    allow_methods=[
        "GET",
        "POST",
        "OPTIONS",
    ],

    allow_headers=[
        "Content-Type",
        "Authorization",
    ],
)


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
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


CATEGORICAL_FEATURES = [
    "payment_method",
    "failure_reason",
    "action",
]


NUMERIC_FEATURES = [
    "amount",
    "customer_age_days",
    "previous_transactions",
    "previous_successes",
    "historical_success_rate",
    "attempt_number",
    "is_first_purchase",
]


ACTIONS = [
    "retry",
    "payment_link",
    "reminder",
]


# ============================================================
# LOAD DATA
# ============================================================

TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"

df = pd.read_csv(
    TRANSACTIONS_FILE
)


# ============================================================
# MODEL TRAINING
# ============================================================

def train_recovery_model(dataframe):

    print(
        "Training RecoveryOS API model..."
    )

    train_df, _ = train_test_split(
        dataframe,
        test_size=0.20,
        random_state=42,
    )


    train_actions = create_action_dataset(
        train_df,
        seed=42,
    )


    X_train = train_actions[
        FEATURES
    ]


    y_train = train_actions[
        "recovered"
    ]


    preprocessor = ColumnTransformer(
        transformers=[

            (
                "categorical",

                OneHotEncoder(
                    handle_unknown="ignore"
                ),

                CATEGORICAL_FEATURES,
            ),

            (
                "numeric",

                "passthrough",

                NUMERIC_FEATURES,
            ),
        ]
    )


    recovery_model = Pipeline(
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


    recovery_model.fit(
        X_train,
        y_train,
    )


    print(
        "RecoveryOS API model ready."
    )


    return recovery_model


model = train_recovery_model(
    df
)


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class TransactionRequest(BaseModel):

    transaction_id: str

    amount: float

    payment_method: str

    customer_age_days: int

    previous_transactions: int

    previous_successes: int

    historical_success_rate: float

    attempt_number: int

    is_first_purchase: bool

    failure_reason: str


class ExecuteRequest(BaseModel):

    transaction_id: str

    action: str


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():

    return {
        "service": "RecoveryOS",
        "version": "1.0",
        "status": "running",
        "environment": ENVIRONMENT
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "model": "ready"
    }


# ============================================================
# ANALYZE TRANSACTION
# ============================================================

@app.post("/analyze")
def analyze_transaction(
    transaction: TransactionRequest
):

    record = transaction.model_dump()

    probability_rows = []


    for action in ACTIONS:

        row = record.copy()

        row["action"] = action

        probability_rows.append(
            row
        )


    action_df = pd.DataFrame(
        probability_rows
    )[FEATURES]


    probabilities = model.predict_proba(
        action_df
    )[:, 1]


    probability_map = dict(
        zip(
            ACTIONS,
            probabilities
        )
    )


    decision = choose_best_allowed_action(
        transaction=record,
        probabilities=probability_map,
        policy_checker=check_policy,
    )


    audit = create_audit_event(
        transaction=record,
        probabilities=probability_map,
        decision=decision,
    )


    return {

        "transaction_id":
            transaction.transaction_id,

        "amount":
            transaction.amount,

        "payment_method":
            transaction.payment_method,

        "customer_age_days":
            transaction.customer_age_days,

        "previous_transactions":
            transaction.previous_transactions,

        "previous_successes":
            transaction.previous_successes,

        "historical_success_rate":
            transaction.historical_success_rate,

        "attempt_number":
            transaction.attempt_number,

        "is_first_purchase":
            transaction.is_first_purchase,

        "failure_reason":
            transaction.failure_reason,

        "probabilities": {

            action:
                round(
                    float(
                        probability_map[action]
                    ),
                    4
                )

            for action in ACTIONS

        },

        "preferred_action":
            decision["preferred_action"],

        "final_action":
            decision["action"],

        "decision_score":
            round(
                float(
                    decision["score"]
                ),
                2
            ),

        "policy":
            decision["policy"],

        "rejected_actions":
            decision["rejected"],

        "audit_id":
            audit["audit_id"],
    }


# ============================================================
# EXECUTE RECOVERY
# ============================================================

@app.post("/execute")
def execute_recovery(
    request: ExecuteRequest
):

    transaction_matches = df[
        df["transaction_id"].astype(str)
        == str(request.transaction_id)
    ]


    if transaction_matches.empty:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )


    transaction = (
        transaction_matches
        .iloc[0]
        .to_dict()
    )


    allowed_actions = [
        "retry",
        "payment_link",
        "reminder",
    ]


    if request.action not in allowed_actions:

        raise HTTPException(
            status_code=400,
            detail="Invalid recovery action"
        )


    policy = check_policy(
        transaction,
        request.action
    )


    if not policy["allowed"]:

        raise HTTPException(
            status_code=403,
            detail={
                "message":
                    "Action blocked by policy",

                "reasons":
                    policy["reasons"]
            }
        )


    execution = execute_action(
        transaction,
        request.action,
    )


    probabilities = {

        request.action:
            execution[
                "recovery_probability"
            ]

    }


    decision = {

        "preferred_action":
            request.action,

        "action":
            request.action,

        "score": 0.0,

        "policy":
            policy,

        "rejected": [],
    }


    audit = create_audit_event(
        transaction=transaction,
        probabilities=probabilities,
        decision=decision,
        execution=execution,
    )


    return {

        "transaction_id":
            request.transaction_id,

        "execution":
            execution,

        "audit_id":
            audit["audit_id"],
    }


# ============================================================
# AUDIT
# ============================================================

@app.get("/audit")
def audit():

    return {

        "count":
            len(
                get_audit_log()
            ),

        "events":
            get_audit_log()
    }


@app.get("/audit/{transaction_id}")
def transaction_audit(
    transaction_id: str
):

    events = get_transaction_audit(
        transaction_id
    )


    if not events:

        raise HTTPException(
            status_code=404,
            detail="No audit events found"
        )


    return {

        "transaction_id":
            transaction_id,

        "events":
            events
    }


# ============================================================
# ANALYTICS
# ============================================================

@app.get("/analytics")
def get_analytics():

    transactions = pd.read_csv(
        DATA_DIR / "transactions.csv"
    )


    strategy = pd.read_csv(
        DATA_DIR / "strategy_benchmark.csv"
    )


    policy = pd.read_csv(
        DATA_DIR / "policy_sensitivity_summary.csv"
    )


    failure_reason = pd.read_csv(
        DATA_DIR / "policy_sensitivity_failure_reason.csv"
    )


    robustness = pd.read_csv(
        DATA_DIR / "robustness_summary.csv"
    )


    utility = pd.read_csv(
        DATA_DIR / "utility_sensitivity_summary.csv"
    )


    policy_optimization = pd.read_csv(
        DATA_DIR / "policy_optimization_summary.csv"
    )


    decision_layer = pd.read_csv(
        DATA_DIR / "decision_layer_analysis.csv"
    )


    # -----------------------------------------
    # OVERVIEW
    # -----------------------------------------

    total_transactions = len(
        transactions
    )


    current_policy = None


    for _, row in policy.iterrows():

        if str(
            row["policy"]
        ).lower() in [

            "current",
            "baseline",
            "default"

        ]:

            current_policy = row

            break


    if (
        current_policy is None
        and len(policy) > 0
    ):

        current_policy = policy.iloc[0]


    if current_policy is not None:

        recovery_rate = float(
            current_policy[
                "recovery_rate"
            ]
        )


        recovered_revenue = float(
            current_policy[
                "recovered_revenue"
            ]
        )


        recovered = int(
            current_policy[
                "recovered"
            ]
        )

    else:

        recovery_rate = 0

        recovered_revenue = 0

        recovered = 0


    # -----------------------------------------
    # RETURN
    # -----------------------------------------

    return {

        "overview": {

            "transactions":
                total_transactions,

            "recovery_rate":
                recovery_rate,

            "recovered":
                recovered,

            "recovered_revenue":
                recovered_revenue,
        },


        "strategy":
            strategy.to_dict(
                orient="records"
            ),


        "policy":
            policy.to_dict(
                orient="records"
            ),


        "failure_reason":
            failure_reason.to_dict(
                orient="records"
            ),


        "robustness":
            robustness.to_dict(
                orient="records"
            ),


        "utility":
            utility.to_dict(
                orient="records"
            ),


        "policy_optimization":
            policy_optimization.to_dict(
                orient="records"
            ),


        "decision_layer":
            decision_layer.to_dict(
                orient="records"
            ),
    }