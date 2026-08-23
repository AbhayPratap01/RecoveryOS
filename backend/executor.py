import numpy as np

from backend.intervention_model import get_recovery_probability


def execute_action(transaction, action, seed=None):
    """
    Simulated execution layer.

    In the hackathon prototype, this represents the external
    payment/recovery action without moving real money.
    """

    if action == "stop":
        return {
            "status": "stopped",
            "action": "stop",
            "recovered": False,
            "recovery_probability": 0.0,
            "amount_recovered": 0.0,
            "message": "Recovery action blocked or stopped."
        }

    probability = get_recovery_probability(
        transaction,
        action
    )

    if seed is not None:
        rng = np.random.default_rng(seed)
        recovered = rng.random() < probability
    else:
        recovered = np.random.random() < probability

    amount = (
        float(transaction["amount"])
        if recovered
        else 0.0
    )

    return {
        "status": "success" if recovered else "failed",
        "action": action,
        "recovered": bool(recovered),
        "recovery_probability": float(probability),
        "amount_recovered": amount,
        "message": (
            "Payment successfully recovered."
            if recovered
            else "Recovery attempt was unsuccessful."
        )
    }