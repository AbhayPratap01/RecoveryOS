import numpy as np
import pandas as pd


ACTIONS = [
    "retry",
    "payment_link",
    "reminder",
    "stop",
]


def get_recovery_probability(row, action):
    """
    Simulated ground-truth probability that a particular
    intervention successfully recovers a failed payment.

    This represents the hidden behaviour of our simulated
    merchant environment.

    RecoveryOS itself will NOT have access to these values.
    """

    if action == "stop":
        return 0.0

    # Start with a neutral probability.
    probability = 0.30

    failure = row["failure_reason"]
    history = row["historical_success_rate"]
    attempts = row["attempt_number"]
    first_purchase = row["is_first_purchase"]

    # Returning customers are generally easier to recover.
    probability += history * 0.20

    # --------------------------------------------------
    # Failure-specific intervention effectiveness
    # --------------------------------------------------

    if action == "retry":

        if failure == "network_error":
            probability += 0.35

        elif failure == "gateway_error":
            probability += 0.30

        elif failure == "bank_decline":
            probability += 0.18

        elif failure == "insufficient_balance":
            probability += 0.05

        elif failure == "authentication_failed":
            probability -= 0.10

        elif failure == "expired_card":
            probability -= 0.20

    elif action == "payment_link":

        if failure == "expired_card":
            probability += 0.35

        elif failure == "authentication_failed":
            probability += 0.20

        elif failure == "insufficient_balance":
            probability += 0.10

        elif failure == "bank_decline":
            probability += 0.08

        elif failure == "network_error":
            probability += 0.05

        elif failure == "gateway_error":
            probability += 0.05

    elif action == "reminder":

        if failure == "insufficient_balance":
            probability += 0.18

        elif failure == "authentication_failed":
            probability += 0.15

        elif failure == "expired_card":
            probability += 0.12

        elif failure == "bank_decline":
            probability += 0.05

        elif failure == "network_error":
            probability += 0.02

        elif failure == "gateway_error":
            probability += 0.02

    # Repeated attempts reduce recovery chances.
    probability -= (attempts - 1) * 0.08

    # First-time customers have slightly lower recovery likelihood.
    if first_purchase:
        probability -= 0.05

    return float(
        np.clip(probability, 0.02, 0.95)
    )