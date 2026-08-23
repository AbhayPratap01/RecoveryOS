from datetime import datetime
import uuid


AUDIT_LOG = []


def create_audit_event(
    transaction,
    probabilities,
    decision,
    execution=None,
):
    event = {
        "audit_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),

        "transaction_id": str(
            transaction["transaction_id"]
        ),

        "amount": float(
            transaction["amount"]
        ),

        "failure_reason": str(
            transaction["failure_reason"]
        ),

        "probabilities": {
            key: float(value)
            for key, value in probabilities.items()
        },

        "preferred_action": decision.get(
            "preferred_action"
        ),

        "final_action": decision.get(
            "action"
        ),

        "decision_score": float(
            decision.get("score", 0.0)
        ),

        "policy_allowed": bool(
            decision["policy"]["allowed"]
        ),

        "policy_reasons": decision[
            "policy"
        ]["reasons"],

        "rejected_actions": decision.get(
            "rejected",
            []
        ),

        "execution": execution,
    }

    AUDIT_LOG.append(event)

    return event


def get_audit_log():
    return AUDIT_LOG


def get_transaction_audit(transaction_id):

    matches = [
        event
        for event in AUDIT_LOG
        if event["transaction_id"]
        == str(transaction_id)
    ]

    return matches