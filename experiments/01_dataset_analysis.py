import pandas as pd


df = pd.read_csv("data/transactions.csv")

print("\n========== DATASET ==========")
print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")

print("\n========== COLUMNS ==========")
print(df.columns.tolist())

print("\n========== PAYMENT METHODS ==========")
print(df["payment_method"].value_counts())

print("\n========== FAILURE REASONS ==========")
print(df["failure_reason"].value_counts())

print("\n========== RECOVERY ==========")
print(df["recovered"].value_counts())

recovery_rate = df["recovered"].mean()

print(f"\nOverall recovery rate: {recovery_rate:.2%}")

total_revenue = df["amount"].sum()

recovered_revenue = df.loc[
    df["recovered"] == 1,
    "amount"
].sum()

print(f"Total transaction value: ₹{total_revenue:,.2f}")
print(f"Recovered revenue: ₹{recovered_revenue:,.2f}")

print("\n========== FAILURE PERFORMANCE ==========")

failure_stats = (
    df.groupby("failure_reason")
    .agg(
        transactions=("transaction_id", "count"),
        recovery_rate=("recovered", "mean"),
        revenue=("amount", "sum"),
    )
    .sort_values(
        "recovery_rate",
        ascending=False,
    )
)

print(failure_stats)