"""5.2 Build an escalation decision engine.

Three triggers are real: the customer asked for a person, policy does not
cover it, the agent cannot make progress. Sentiment and self-reported
confidence are not triggers.

Run it:  python ex_5_2_escalation.py
"""
from pprint import pprint


MAX_ATTEMPTS = 3


# ---------------------------------------------------------------- START HERE
def should_escalate(case):
    """Returns (escalate, reason). Order matters: the explicit ask wins."""
    if case.get("asked_for_human"):
        return True, "customer asked for a person"
    if case.get("policy_covers") is False:
        return True, "no policy covers this request"
    if case.get("attempts", 0) >= MAX_ATTEMPTS:
        return True, f"no progress after {MAX_ATTEMPTS} attempts"
    return False, "handle it"


def match_customer(candidates):
    """Ambiguity is a question, not a guess. Picking one can refund a stranger."""
    if len(candidates) == 1:
        return {"action": "proceed", "customer": candidates[0]}
    if not candidates:
        return {"action": "ask", "question": "I could not find that account. "
                                             "What email is it under?"}
    return {"action": "ask",
            "question": "I found more than one account with that name. "
                        "Can you give me the order number?"}


if __name__ == "__main__":
    cases = [
        ("angry but fixable", {"frustrated": True, "policy_covers": True}),
        ("angry and asked for a person",
         {"frustrated": True, "asked_for_human": True, "policy_covers": True}),
        ("calm, outside policy", {"frustrated": False, "policy_covers": False}),
        ("tried three times", {"policy_covers": True, "attempts": 3}),
        ("model says 0.4 confident", {"policy_covers": True, "confidence": 0.4}),
    ]
    for label, case in cases:
        esc, why = should_escalate(case)
        print(f"{label:30} {'ESCALATE' if esc else 'handle  '}  {why}")

    print("\nFrustration alone is not a trigger; solving the problem is the")
    print("better outcome. A confidence number is not evidence either.\n")

    for cands in ([{"id": 1}], [{"id": 1}, {"id": 2}], []):
        print(f"{len(cands)} match(es) ->")
        pprint(match_customer(cands), width=74)
