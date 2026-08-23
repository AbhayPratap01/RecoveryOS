import pandas as pd

from backend.simulator import (
    always_retry,
    rule_based,
    simulate_outcomes,
    calculate_recovery,
)


df = pd.read_csv(
    "data/transactions.csv"
)


strategies = {
    "Always Retry": always_retry,
    "Rule Based": rule_based,
}


print("\n===================================")
print("        RECOVERYOS V1")
print("    INTERVENTION SIMULATION")
print("===================================\n")


for name, strategy in strategies.items():

    decisions = strategy(df)

    result = simulate_outcomes(
        decisions,
        seed=42,
    )

    metrics = calculate_recovery(result)

    print(name)
    print("-" * 35)

    print(
        f"Actions attempted: "
        f"{metrics['transactions_attempted']}"
    )

    print(
        f"Transactions recovered: "
        f"{metrics['transactions_recovered']}"
    )

    print(
        f"Recovery rate: "
        f"{metrics['recovery_rate']:.2%}"
    )

    print(
        f"Revenue recovered: "
        f"₹{metrics['recovered_revenue']:,.2f}"
    )

    print(
        f"Revenue attempted: "
        f"₹{metrics['attempted_revenue']:,.2f}"
    )

    print()