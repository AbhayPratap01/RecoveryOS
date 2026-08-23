import numpy as np
import pandas as pd


def generate_transactions(n=10000, seed=42):
    rng = np.random.default_rng(seed)

    payment_methods = ["card", "upi", "netbanking", "wallet"]
    failure_reasons = [
        "bank_decline",
        "insufficient_balance",
        "network_error",
        "authentication_failed",
        "expired_card",
        "gateway_error",
    ]

    data = []

    for i in range(n):
        amount = round(float(rng.lognormal(mean=7.0, sigma=0.8)), 2)
        amount = min(max(amount, 100), 50000)

        payment_method = rng.choice(payment_methods)

        customer_age_days = int(rng.integers(1, 1500))
        previous_transactions = int(rng.integers(0, 30))
        previous_successes = int(
            rng.binomial(previous_transactions, 0.75)
        )

        if previous_transactions > 0:
            historical_success_rate = (
                previous_successes / previous_transactions
            )
        else:
            historical_success_rate = 0.0

        attempt_number = int(rng.integers(1, 5))

        is_first_purchase = previous_transactions == 0

        failure_reason = rng.choice(
            failure_reasons,
            p=[
                0.25,
                0.18,
                0.15,
                0.14,
                0.10,
                0.18,
            ],
        )

        # Base probability that this failed payment can eventually
        # be recovered.
        recovery_probability = 0.30

        # Returning customers are easier to recover.
        recovery_probability += (
            historical_success_rate * 0.30
        )

        # Different failures have different recovery characteristics.
        if failure_reason == "network_error":
            recovery_probability += 0.18

        elif failure_reason == "gateway_error":
            recovery_probability += 0.15

        elif failure_reason == "bank_decline":
            recovery_probability += 0.08

        elif failure_reason == "insufficient_balance":
            recovery_probability += 0.02

        elif failure_reason == "authentication_failed":
            recovery_probability -= 0.10

        elif failure_reason == "expired_card":
            recovery_probability -= 0.15

        # Repeated attempts reduce the chance of successful recovery.
        recovery_probability -= (attempt_number - 1) * 0.08

        # First-time customers are slightly harder to recover.
        if is_first_purchase:
            recovery_probability -= 0.05

        recovery_probability = np.clip(
            recovery_probability,
            0.02,
            0.95,
        )

        recovered = int(
            rng.random() < recovery_probability
        )

        data.append(
            {
                "transaction_id": f"txn_{i+1:06d}",
                "customer_id": f"cust_{rng.integers(1, n // 3 + 1):06d}",
                "amount": amount,
                "payment_method": payment_method,
                "customer_age_days": customer_age_days,
                "previous_transactions": previous_transactions,
                "previous_successes": previous_successes,
                "historical_success_rate": round(
                    historical_success_rate, 4
                ),
                "attempt_number": attempt_number,
                "is_first_purchase": is_first_purchase,
                "failure_reason": failure_reason,
                "recovery_probability": round(
                    recovery_probability, 4
                ),
                "recovered": recovered,
            }
        )

    return pd.DataFrame(data)


if __name__ == "__main__":
    df = generate_transactions()

    df.to_csv(
        "data/transactions.csv",
        index=False,
    )

    print("Dataset generated successfully.")
    print(f"Shape: {df.shape}")
    print()
    print(df.head())