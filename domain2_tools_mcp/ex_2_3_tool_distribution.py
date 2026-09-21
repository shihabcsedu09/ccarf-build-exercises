"""2.3 Give each agent only the tools its role needs.

Real scenario: to cut escalations somebody connected the CRM, billing,
shipping and loyalty servers to the support agent. It went from 4 tools to
18, and tool selection fell from 94% to 71%.

Four or five per role is the number to remember. Splitting also gives the
refund gate one door to guard instead of four.

tool_choice is a separate knob, set per request, not a property of a tool.

Run it:
    python ex_2_3_tool_distribution.py                     offline
    ANTHROPIC_API_KEY=sk-... python ex_2_3_tool_distribution.py    real calls
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, call, get_client, recorded, say


def tool(name, description):
    return {"name": name, "description": description,
            "input_schema": {"type": "object", "properties": {}, "required": []}}


# One agent holding everything. Eighteen descriptions compete at selection time.
EVERYTHING = [tool(n, "…") for n in (
    "get_customer", "lookup_order", "process_refund", "reject_refund",
    "payment_read", "payment_write", "fraud_check", "compliance_log",
    "send_email", "send_sms", "escalate_to_human", "audit_write",
    "ticket_create", "ticket_close", "get_loyalty_balance", "add_loyalty_points",
    "get_shipping_rates", "book_courier")]


# ---------------------------------------------------------------- START HERE
# Four roles, four or five tools each. Each menu is short enough to choose from,
# and coherent enough that the wrong tool is obviously wrong.
ROLES = {
    "customer": [tool("get_customer", "Identity and account record."),
                 tool("lookup_order", "One order: status, items, totals."),
                 tool("ticket_create", "Open a ticket."),
                 tool("ticket_close", "Close a ticket.")],
    "payments": [tool("payment_read", "Read a payment record."),
                 tool("fraud_check", "Run the fraud check. Required before a refund."),
                 tool("process_refund", "Refund an order, after the fraud check."),
                 tool("reject_refund", "Decline a refund with a reason.")],
    "comms":    [tool("send_email", "Email the customer."),
                 tool("send_sms", "Text the customer."),
                 tool("escalate_to_human", "Hand the case to a person, with a summary.")],
    "loyalty":  [tool("get_loyalty_balance", "Points balance for one account."),
                 tool("add_loyalty_points", "Credit points, with a reason.")],
}


def route(role, question, client):
    """Run one request against one role's short menu."""
    reply = client.messages.create(
        model=MODEL, max_tokens=512, tools=ROLES[role],
        system="You are the %s agent. Use only the tools you have." % role,
        messages=[{"role": "user", "content": question}])
    for block in reply.content:
        if block.type == "tool_use":
            return block.name
    return "answered in words"


def scoped_power(client, question):
    """When one role often needs a sliver of another's power, give it a narrow
    version rather than the whole kit. Least privilege, and still no round trip."""
    verify_only = [tool("verify_claim", "Check one fact against a source. Read only.")]
    reply = client.messages.create(
        model=MODEL, max_tokens=512, tools=verify_only,
        system="You synthesise findings. You may check a single fact.",
        messages=[{"role": "user", "content": question}])
    return [b.name for b in reply.content if b.type == "tool_use"]


# ---------------------------------------------------------------- tool_choice
def choice_examples():
    """Set per request. The same tools, four different guarantees."""
    return [
        ({"type": "auto"}, "Claude may answer in words. The default, and right for chat."),
        ({"type": "any"}, "It must call some tool, but picks which. Right when several "
                          "schemas exist and you do not know the document type."),
        ({"type": "tool", "name": "extract_invoice"},
         "It must call this one. Right when the call is the whole job."),
        ({"type": "none"}, "No tools this turn. Useful for a final summary in prose."),
    ]


if __name__ == "__main__":
    banner("2.3 tool distribution and tool_choice")
    print("one agent holding everything: %d tools" % len(EVERYTHING))
    print("split by role:", ", ".join("%s %d" % (r, len(t)) for r, t in ROLES.items()))
    print()

    script = [recorded(call("t1", "lookup_order")),
              recorded(call("t2", "fraud_check")),
              recorded(call("t3", "escalate_to_human"))]
    client = get_client(script)
    print("'where is order 8891?'        ->", route("customer", "where is order 8891?", client))
    print("'refund 47.90 on order 8891'  ->", route("payments", "refund 47.90 on order 8891", client))
    print("'customer wants a person'     ->", route("comms", "customer wants a person", client))
    print()
    print("the payments agent is the only one holding process_refund, so the")
    print("refund gate has one door to guard instead of four.")
    print()

    names = scoped_power(get_client([recorded(call("t4", "verify_claim"))]),
                         "Check whether the 12% growth figure is right.")
    print("synthesis agent, given one narrow tool ->", names)
    print("   not the whole search kit, which would pull it away from its job.")
    print()
    print("tool_choice, set per request:")
    for value, why in choice_examples():
        print("   %-42s %s" % (str(value), why))
    print()
    print("Trap: 'any' inside an agent loop means Claude can never say it is")
    print("finished, so the loop runs until the safety net catches it.")
