"""2.1 Write tool descriptions that stop misrouting.

Claude picks a tool by reading its description. Two one-line
descriptions are two blank profiles, so it guesses.

Run it:  python ex_2_1_tool_descriptions.py
"""

THIN = [
    {"name": "get_customer", "description": "Retrieves customer information"},
    {"name": "lookup_order", "description": "Retrieves order details"},
]

# ---------------------------------------------------------------- START HERE
FULL = [
    {"name": "get_customer",
     "description": (
         "Look up a CUSTOMER account: contact details, addresses, loyalty tier. "
         "Accepts an email, a phone number, or an id like CUS-12345. "
         "Use it to verify who you are speaking to. "
         "Example: 'my email is ada@example.com'. "
         "Edge case: a name alone can match several people, so it returns all "
         "matches and you must ask for a distinguishing detail. "
         "Do NOT use it for a specific order: that is lookup_order."),
     "input_schema": {"type": "object", "properties": {
         "email": {"type": "string"}, "customer_id": {"type": "string"}}}},

    {"name": "lookup_order",
     "description": (
         "Look up ONE ORDER: items, dates, shipping status, refund eligibility. "
         "Accepts an order number like 8891 or ORD-8891. "
         "Use it for anything about a purchase. "
         "Example: 'check my order #12345', 'where is my parcel'. "
         "Edge case: an unknown number returns 'not_found', which is an answer "
         "and not a failure, so do not retry it. "
         "Do NOT use it to identify the customer: that is get_customer."),
     "input_schema": {"type": "object",
                      "properties": {"order_id": {"type": "string"}},
                      "required": ["order_id"]}},
]

REQUIRED_PARTS = ["purpose", "accepted input", "example", "edge case", "boundary"]


def score(description):
    """A crude check for the five things a production description needs."""
    d = description.lower()
    return {
        "purpose":        d.startswith("look up"),
        "accepted input": "accepts" in d,
        "example":        "example" in d,
        "edge case":      "edge case" in d,
        "boundary":       "do not use" in d,
    }


if __name__ == "__main__":
    for label, tools in (("thin", THIN), ("full", FULL)):
        print(f"--- {label} descriptions")
        for t in tools:
            got = score(t["description"])
            print(f"  {t['name']:14} " +
                  " ".join(("+" if got[p] else "-") + p for p in REQUIRED_PARTS))
    print("\nIf the descriptions are already full and selection still skews on one")
    print("word, look for a keyword rule in the system prompt overriding them.")
