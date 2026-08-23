import numpy as np
import pandas as pd

from backend.intervention_model import ACTIONS
from backend.intervention_model import get_recovery_probability


def create_action_dataset(
    df,
    actions=None,
    seed=42,
):
    if actions is None:
        actions = [
            "retry",
            "payment_link",
            "reminder",
        ]

    rng = np.random.default_rng(seed)

    rows = []

    for _, row in df.iterrows():

        for action in actions:

            probability = get_recovery_probability(
                row,
                action,
            )

            recovered = int(
                rng.random() < probability
            )

            record = row.to_dict()

            # These are hidden simulator values.
            # We deliberately do NOT save them.
            record.pop(
                "recovery_probability",
                None,
            )

            record.pop(
                "recovered",
                None,
            )

            record["action"] = action
            record["recovered"] = recovered

            rows.append(record)

    return pd.DataFrame(rows)