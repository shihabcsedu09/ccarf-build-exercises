"""1.4 Build a prerequisite gate for refunds.

A prompt asks. A gate makes the wrong order impossible.

Run it:  python ex_1_4_prerequisite_gate.py
"""
from pprint import pprint


HANDOFF_FIELDS = ["customer_id", "verification", "issue_summary",
                  "actions_attempted", "root_cause", "recommended_action"]


class Session:
    """Facts enter here only from real tool results, never from what the
    model asserted in its own text."""

    def __init__(self):
        self.verified_customer_id = None
        self.order_eligible = False
        self.max_refund = 0.0

    def record(self, tool, result):
        if tool == "get_customer" and result.get("verified"):
            self.verified_customer_id = result["customer_id"]
        if tool == "lookup_order":
            self.order_eligible = result.get("refund_eligible", False)
            self.max_refund = result.get("refundable_amount", 0.0)


# ---------------------------------------------------------------- START HERE
def gate(session, tool, args):
    """Runs before the tool does. Returns None to allow, or a refusal."""
    if tool != "process_refund":
        return None
    if not session.verified_customer_id:
        return "Call get_customer first and verify the customer."
    if args.get("customer_id") != session.verified_customer_id:
        return "customer_id does not match the verified customer."
    if not session.order_eligible:
        return "Call lookup_order and confirm the order is refundable."
    if args["amount"] > session.max_refund:
        return f"Amount exceeds the eligible {session.max_refund:.2f}."
    return None


def handoff(**fields):
    missing = [f for f in HANDOFF_FIELDS if f not in fields]
    if missing:
        raise ValueError(f"escalation is missing: {missing}")
    return fields


if __name__ == "__main__":
    s = Session()
    attempts = [
        ("no verification yet", {"customer_id": "CUS-1", "amount": 50}),
    ]
    for label, args in attempts:
        print(f"{label:24} -> {gate(s, 'process_refund', args)}")

    s.record("get_customer", {"verified": True, "customer_id": "CUS-1"})
    mine_50 = {"customer_id": "CUS-1", "amount": 50}
    print(f"{'verified, no order yet':24} -> "
          f"{gate(s, 'process_refund', mine_50)}")

    s.record("lookup_order", {"refund_eligible": True,
                              "refundable_amount": 40})
    later = [("amount too high", mine_50),
             ("someone elses id", {"customer_id": "CUS-9", "amount": 40}),
             ("within policy", {"customer_id": "CUS-1", "amount": 40})]
    for label, args in later:
        print(f"{label:24} -> {gate(s, 'process_refund', args)}")

    print("\nhandoff:")
    pprint(handoff(customer_id="CUS-1", verification="email, 10:42",
                   issue_summary="damaged item",
                   actions_attempted=["get_customer", "lookup_order"],
                   root_cause="item damaged in transit",
                   recommended_action="refund 40.00"), width=74)
