"""2.1 Write tool descriptions that stop misrouting.

Real scenario: the support agent has two lookups. Customers ask "check my
order #12345" and the agent calls get_customer instead.

The description is what Claude reads when it chooses. Two one-line
descriptions are two blank profiles, so it guesses. Say what each returns,
when to use it, and when to use the other one instead.

Run it:
    python ex_2_1_tool_descriptions.py                     offline
    ANTHROPIC_API_KEY=sk-... python ex_2_1_tool_descriptions.py    real calls
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, call, get_client, recorded

# Before. Both say roughly "gets a thing", and both accept an identifier.
THIN = [
    {"name": "get_customer", "description": "Retrieves customer information.",
     "input_schema": {"type": "object", "properties": {"id": {"type": "string"}},
                      "required": ["id"]}},
    {"name": "lookup_order", "description": "Retrieves order details.",
     "input_schema": {"type": "object", "properties": {"id": {"type": "string"}},
                      "required": ["id"]}},
]


# ---------------------------------------------------------------- START HERE
# After. Five things each description carries: what it returns, when to call
# it, when not to, the input format with an example, and the boundary against
# its neighbour.
FULL = [
    {
        "name": "get_customer",
        "description": (
            "Retrieve one customer's account record: name, email, postal "
            "address, account status and loyalty tier. "
            "Use when the request is about the person or the account itself, "
            "or to verify identity before an account-specific action. "
            "Do NOT use for anything about a specific order, including status, "
            "contents, delivery or refunds; use lookup_order for those. "
            "Returns one record, never a list."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string",
                          "description": "the account email, e.g. ana@example.com"},
            },
            "required": ["email"],
        },
    },
    {
        "name": "lookup_order",
        "description": (
            "Retrieve one order: status, line items, totals, delivery dates "
            "and refund eligibility. "
            "Use whenever an order number is present, or the question is about "
            "a purchase, a delivery or a return. "
            "Do NOT use to identify a person or to list somebody's orders; "
            "use get_customer for that. "
            "An order number that does not exist returns an empty result, not "
            "an error."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string",
                             "description": "digits only, e.g. 12345"},
            },
            "required": ["order_id"],
        },
    },
]


def which_tool(client, tools, question):
    """Ask Claude to handle the question and report which tool it reached for."""
    reply = client.messages.create(
        model=MODEL, max_tokens=512, tools=tools,
        system="You are a support agent. Use a tool to answer.",
        messages=[{"role": "user", "content": question}])
    for block in reply.content:
        if block.type == "tool_use":
            return block.name, block.input
    return None, None


# ---------------------------------------------------------------- recorded replies
QUESTION = "check my order #12345"
THIN_SCRIPT = [recorded(call("t1", "get_customer", id="12345"))]      # the wrong one
FULL_SCRIPT = [recorded(call("t1", "lookup_order", order_id="12345"))]

if __name__ == "__main__":
    banner("2.1 tool descriptions")
    print("question:", QUESTION)
    print()

    name, args = which_tool(get_client(THIN_SCRIPT), THIN, QUESTION)
    print("with one-line descriptions -> %s(%s)" % (name, args))
    print("   'Retrieves customer information' and 'Retrieves order details'")
    print("   are the same sentence to a reader deciding between them.")
    print()

    name, args = which_tool(get_client(FULL_SCRIPT), FULL, QUESTION)
    print("with full descriptions     -> %s(%s)" % (name, args))
    print("   'Use whenever an order number is present' settles it, and the")
    print("   'Do NOT use' line stops the drift back.")
    print()
    print("description lengths: thin %d chars, full %d chars"
          % (len(THIN[0]["description"]), len(FULL[0]["description"])))
    print("Nothing else changed: same model, same question, same schemas.")
