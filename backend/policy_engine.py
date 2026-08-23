MAX_RETRY_ATTEMPTS = 2
MAX_AUTOMATED_AMOUNT = 50000


def check_policy(transaction, action):

    reasons = []

    attempt_number = transaction["attempt_number"]
    amount = transaction["amount"]
    failure_reason = transaction["failure_reason"]

    # ==========================================
    # Retry-specific rules
    # ==========================================

    if action == "retry":

        if attempt_number > MAX_RETRY_ATTEMPTS:
            reasons.append(
                "maximum_retry_attempts_exceeded"
            )

        if failure_reason == "expired_card":
            reasons.append(
                "expired_card_cannot_be_retried"
            )

        if failure_reason == "authentication_failed":
            reasons.append(
                "authentication_failure_requires_new_authentication"
            )

    # ==========================================
    # Payment-link rules
    # ==========================================

    if action == "payment_link":

        if failure_reason == "insufficient_balance":
            reasons.append(
                "payment_link_not_preferred_for_insufficient_balance"
            )

    # ==========================================
    # Reminder rules
    # ==========================================

    if action == "reminder":

        if failure_reason == "network_error":
            reasons.append(
                "temporary_network_error_should_be_retried_first"
            )

    # ==========================================
    # High-value transaction
    # ==========================================

    if amount > MAX_AUTOMATED_AMOUNT:

        reasons.append(
            "high_value_transaction_requires_review"
        )

    allowed = len(reasons) == 0

    return {
        "allowed": allowed,
        "reasons": reasons,
    }