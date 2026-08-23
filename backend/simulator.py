import numpy as np
import pandas as pd

from backend.intervention_model import get_recovery_probability


def always_retry(df):
    result = df.copy()
    result["action"] = "retry"
    return result


def rule_based(df):
    result = df.copy()

    result["action"] = "stop"

    result.loc[
        result["failure_reason"].isin(
            ["network_error", "gateway_error"]
        ),
        "action",
    ] = "retry"

    result.loc[
        result["failure_reason"] == "bank_decline",
        "action",
    ] = "retry"

    result.loc[
        result["failure_reason"] == "insufficient_balance",
        "action",
    ] = "reminder"

    result.loc[
        result["failure_reason"] == "expired_card",
        "action",
    ] = "payment_link"

    result.loc[
        result["failure_reason"] == "authentication_failed",
        "action",
    ] = "reminder"

    result.loc[
        result["attempt_number"] >= 3,
        "action",
    ] = "stop"

    return result


def simulate_outcomes(df, seed=42):
    """
    Simulate the result of the selected intervention.

    Each transaction receives a deterministic random number
    so that different strategies can be compared fairly.
    """

    result = df.copy()

    rng = np.random.default_rng(seed)

    random_values = rng.random(len(result))

    result["recovery_probability"] = result.apply(
        lambda row: get_recovery_probability(
            row,
            row["action"]
        ),
        axis=1,
    )

    result["recovered"] = (
        (result["action"] != "stop")
        & (
            random_values
            < result["recovery_probability"]
        )
    ).astype(int)

    return result


def calculate_recovery(df):

    actionable = df["action"] != "stop"

    recovered = (
        actionable
        & (df["recovered"] == 1)
    )

    recovered_revenue = df.loc[
        recovered,
        "amount"
    ].sum()

    attempted_revenue = df.loc[
        actionable,
        "amount"
    ].sum()

    return {
        "transactions_attempted": int(
            actionable.sum()
        ),

        "transactions_recovered": int(
            recovered.sum()
        ),

        "recovered_revenue": float(
            recovered_revenue
        ),

        "attempted_revenue": float(
            attempted_revenue
        ),

        "recovery_rate": (
            recovered.sum() / actionable.sum()
            if actionable.sum() > 0
            else 0
        ),
    }