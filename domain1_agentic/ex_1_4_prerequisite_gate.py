"""1.4 Put a gate in front of a financial tool.

Real scenario: the support agent may refund, but only after it has verified
who it is talking to, and never above 500 on its own.

The system prompt asks for that order. A prompt is a request, and under load
some requests are not honoured. The gate is code in the dispatch path, so the
refund tool cannot run early even when Claude asks it to.

Run it:
    python ex_1_4_prerequisite_gate.py                     offline
    ANTHROPIC_API_KEY=sk-... python ex_1_4_prerequisite_gate.py    real calls
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, call, get_client, recorded, say

TOOLS = [
    {"name": "get_customer",
     "description": "Verify who the customer is. Returns a verified customer id.",
     "input_schema": {"type": "object",
                      "properties": {"email": {"type": "string"}},
                      "required": ["email"]}},
    {"name": "process_refund",
     "description": "Refund an order. Requires a verified customer id.",
     "input_schema": {"type": "object",
                      "properties": {"order_id": {"type": "string"},
                                     "amount": {"type": "number"}},
                      "required": ["order_id", "amount"]}},
]

REFUND_LIMIT = 500.0


class Session(object):
    """State your code owns. The model cannot edit it by changing its mind."""

    def __init__(self):
        self.verified_customer = None


# ---------------------------------------------------------------- START HERE
def gate(name, arguments, session):
    """Runs before every tool. Returns None to allow, or a refusal to send back.

    This is the whole idea: one place, in code, that the model cannot talk past.
    """
    if name == "process_refund":
        if session.verified_customer is None:
            return {"error": "identity not verified",
                    "do_instead": "call get_customer first, then retry"}
        if arguments.get("amount", 0) > REFUND_LIMIT:
            return {"error": "amount %.2f is over the %.2f limit"
                             % (arguments["amount"], REFUND_LIMIT),
                    "do_instead": "call escalate_to_human with the case summary"}
    return None          # anything not named above is allowed through


def dispatch(name, arguments, session):
    """Run one tool, but only after the gate has agreed to it."""
    refusal = gate(name, arguments, session)
    if refusal is not None:
        return refusal, True                       # blocked, and Claude is told why

    if name == "get_customer":
        session.verified_customer = "C-4421"       # remember it for the gate
        return {"customer_id": session.verified_customer, "verified": True}, False
    if name == "process_refund":
        return {"refunded": arguments["amount"], "order_id": arguments["order_id"]}, False
    raise KeyError(name)


def run(client, question, session):
    """The ordinary loop from 1.1, with every tool call passing through the gate."""
    messages = [{"role": "user", "content": question}]
    attempts = []

    for _ in range(10):
        reply = client.messages.create(
            model=MODEL, max_tokens=1024, tools=TOOLS,
            system="Verify the customer before any refund. Refunds over 500 go to a human.",
            messages=messages)

        if reply.stop_reason != "tool_use":
            return "".join(b.text for b in reply.content if b.type == "text"), attempts

        messages.append({"role": "assistant", "content": reply.content})
        results = []
        for block in reply.content:
            if block.type != "tool_use":
                continue
            output, blocked = dispatch(block.name, block.input, session)
            attempts.append((block.name, "BLOCKED" if blocked else "ran"))
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": json.dumps(output), "is_error": blocked})
        messages.append({"role": "user", "content": results})

    raise RuntimeError("safety net reached")


# ---------------------------------------------------------------- recorded replies
# Claude skips verification and goes straight for the refund, which is the 12%
# of real cases the exam describes. The gate turns that into a retry.
SKIPS_VERIFICATION = [
    recorded(say("I'll refund that now."),
             call("t1", "process_refund", order_id="8891", amount=47.90)),
    recorded(say("Let me verify you first."),
             call("t2", "get_customer", email="ana@example.com")),
    recorded(call("t3", "process_refund", order_id="8891", amount=47.90)),
    recorded(say("Verified and refunded 47.90 on order 8891.")),
]

OVER_LIMIT = [
    recorded(call("t1", "get_customer", email="ana@example.com")),
    recorded(call("t2", "process_refund", order_id="9002", amount=750.00)),
    recorded(say("That refund is above my limit, so I have passed it to a colleague.")),
]

if __name__ == "__main__":
    banner("1.4 prerequisite gate")

    answer, attempts = run(get_client(SKIPS_VERIFICATION),
                           "Refund order 8891 please", Session())
    print("case 1: the model tried to refund before verifying")
    for name, outcome in attempts:
        print("   %-16s %s" % (name, outcome))
    print("  ->", answer)
    print()

    answer, attempts = run(get_client(OVER_LIMIT),
                           "Refund order 9002, it was 750", Session())
    print("case 2: verified, but the amount is over the limit")
    for name, outcome in attempts:
        print("   %-16s %s" % (name, outcome))
    print("  ->", answer)
    print()
    print("Neither refund slipped through. The prompt asked for the right order;")
    print("the gate is what made it true on the run where the model did not.")
