"""5.1 Build a persistent case facts context manager.

Summarisation rounds numbers and drops identifiers. Anything a decision
depends on lives in a block that is re-stated verbatim, never summarised.

Run it:  python ex_5_1_case_facts.py
"""

KEEP = ("order_id", "amount", "currency", "order_date", "policy_window_days")


# ---------------------------------------------------------------- START HERE
class CaseFacts:
    """A small block restated in full on every turn."""

    def __init__(self):
        self.facts = {}

    def record(self, **kv):
        self.facts.update(kv)

    def block(self):
        rows = "\n".join(f"  {k}: {v}" for k, v in self.facts.items())
        return f"<case_facts>\n{rows}\n</case_facts>"


def trim(tool_result):
    """A 40-field order record is 5 fields of decision-relevant data."""
    return {k: v for k, v in tool_result.items() if k in KEEP}


def summarise(text):
    """What a rounding summariser does to a transcript. Not malice, just loss."""
    return (text.replace("187.43", "about $190")
                .replace("ORD-88213", "the order")
                .replace("2026-08-14", "last month"))


def order_findings(findings):
    """Lost in the middle: the decisive fact goes first, not in the pile."""
    return sorted(findings, key=lambda f: -f["relevance"])


if __name__ == "__main__":
    raw = {"order_id": "ORD-88213", "amount": 187.43, "currency": "USD",
           "order_date": "2026-08-14", "policy_window_days": 30,
           "warehouse_bay": "B12", "picker_id": 7741, "carrier_scac": "UPSN",
           "gift_wrap": False, "marketing_source": "email-aug"}
    print("tool result fields:", len(raw), "-> kept:", len(trim(raw)))

    facts = CaseFacts()
    facts.record(**trim(raw))
    print("\n" + facts.block())

    turn = "Customer disputes ORD-88213 for 187.43 placed 2026-08-14."
    print("\nafter summarisation:", summarise(turn))
    print("the facts block still says:", facts.facts["amount"],
          facts.facts["order_id"])

    found = [{"text": "refund window is 30 days", "relevance": 9},
             {"text": "warehouse note", "relevance": 2},
             {"text": "order is 38 days old", "relevance": 10}]
    print("\nordered for the prompt:")
    for f in order_findings(found):
        print("  -", f["text"])
