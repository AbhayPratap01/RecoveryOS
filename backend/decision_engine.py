ACTION_COST = {
    "retry": 2.0,
    "payment_link": 1.0,
    "reminder": 0.5,
}

FRICTION_COST = {
    "retry": 10.0,
    "payment_link": 5.0,
    "reminder": 2.0,
}


def calculate_expected_value(
    amount,
    recovery_probability,
    action,
):
    expected_revenue = (
        amount * recovery_probability
    )

    action_cost = ACTION_COST[action]
    friction_cost = FRICTION_COST[action]

    return (
        expected_revenue
        - action_cost
        - friction_cost
    )


def rank_actions(
    amount,
    probabilities,
):
    scores = {}

    for action, probability in probabilities.items():

        scores[action] = calculate_expected_value(
            amount=amount,
            recovery_probability=probability,
            action=action,
        )

    return sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )


def choose_best_allowed_action(
    transaction,
    probabilities,
    policy_checker,
):
    ranked_actions = rank_actions(
        amount=transaction["amount"],
        probabilities=probabilities,
    )

    preferred_action = ranked_actions[0][0]

    rejected = []

    for action, score in ranked_actions:

        policy = policy_checker(
            transaction,
            action,
        )

        if policy["allowed"]:

            return {
                "preferred_action": preferred_action,
                "action": action,
                "score": score,
                "rejected": rejected,
                "policy": policy,
            }

        rejected.append(
            {
                "action": action,
                "reasons": policy["reasons"],
            }
        )

    return {
        "preferred_action": preferred_action,
        "action": "stop",
        "score": 0.0,
        "rejected": rejected,
        "policy": {
            "allowed": False,
            "reasons": [
                "all_actions_blocked"
            ],
        },
    }