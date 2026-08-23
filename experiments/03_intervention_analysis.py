import pandas as pd

from backend.intervention_model import (
    ACTIONS,
    get_recovery_probability,
)


df = pd.read_csv(
    "data/transactions.csv"
)


print("\n===================================")
print("     INTERVENTION ANALYSIS")
print("===================================\n")


for failure_reason in sorted(
    df["failure_reason"].unique()
):

    subset = df[
        df["failure_reason"] == failure_reason
    ]

    print(f"\nFailure: {failure_reason}")
    print(f"Transactions: {len(subset)}")

    for action in ACTIONS:

        probabilities = subset.apply(
            lambda row: get_recovery_probability(
                row,
                action,
            ),
            axis=1,
        )

        print(
            f"  {action:<15} "
            f"{probabilities.mean():.2%}"
        )