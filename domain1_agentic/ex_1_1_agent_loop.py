"""1.1 Build a multi-tool agent loop.

Real scenario: the support agent from the exam. A customer asks where an
order is and whether their address is current. Two lookups, neither one
needing the other, so Claude asks for both in the same turn.

The loop turns on one field, stop_reason, and nothing else.

Run it:
    python ex_1_1_agent_loop.py                      offline, no key needed
    ANTHROPIC_API_KEY=sk-... python ex_1_1_agent_loop.py     real API calls
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # find claude_helpers
from claude_helpers import MODEL, banner, call, get_client, recorded, say

MAX_ROUNDS = 20     # a safety net that raises an alert, not the way you normally stop

# The tool definitions Claude reads to decide what to ask for. The description is
# the part it actually chooses on, so each one says when to use it and when not to.
TOOLS = [
    {
        "name": "lookup_order",
        "description": (
            "Retrieve one order by its order number. Use when the customer asks "
            "about delivery, status or contents of a specific order. Do not use "
            "to look up a person; use get_customer for that."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string",
                                        "description": "digits only, e.g. 8891"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "get_customer",
        "description": (
            "Retrieve the customer's account record: name, address, contact "
            "details. Use to verify identity or answer questions about the "
            "account itself. Do not use for order status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"email": {"type": "string"}},
            "required": ["email"],
        },
    },
]

SYSTEM = (
    "You are a support agent. When you need several pieces of information and "
    "none depends on another, ask for them in the same turn."
)


# ---------------------------------------------------------------- your tools
def lookup_order(order_id):
    return {"order_id": order_id, "status": "in transit", "eta": "2026-09-24"}


def get_customer(email):
    return {"email": email, "address": "12 Mill Lane, Leeds", "verified": True}


RUNNERS = {"lookup_order": lookup_order, "get_customer": get_customer}


# ---------------------------------------------------------------- START HERE
def agent(client, question):
    """Send, read stop_reason, run whatever was asked for, send the results back."""
    messages = [{"role": "user", "content": question}]

    for round_number in range(1, MAX_ROUNDS + 1):
        reply = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )

        if reply.stop_reason == "end_turn":
            # Finished. Everything else below is Claude asking for something.
            answer = "".join(b.text for b in reply.content if b.type == "text")
            return answer, round_number

        if reply.stop_reason == "max_tokens":
            # The reply was cut off. Not an answer, however complete it looks.
            raise RuntimeError("reply truncated: raise max_tokens or shorten the input")

        if reply.stop_reason != "tool_use":
            # refusal, pause_turn and anything new land here rather than being
            # mistaken for a finished answer.
            raise RuntimeError("unexpected stop_reason: %s" % reply.stop_reason)

        # Keep the whole reply, text blocks included. Drop the text and the
        # tool_use ids go with it, so the results have nothing to attach to.
        messages.append({"role": "assistant", "content": reply.content})

        results = []
        for block in reply.content:
            if block.type != "tool_use":
                continue
            try:
                output = RUNNERS[block.name](**block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,     # the receipt that pairs them up
                    "content": json.dumps(output),
                })
            except Exception as exc:
                # A failure is still a result. Say so and let Claude decide.
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps({"error": str(exc)}),
                    "is_error": True,
                })

        # Every result travels in ONE user message. Splitting them across two
        # messages, or leaving one out, breaks the pairing.
        messages.append({"role": "user", "content": results})

    raise RuntimeError("hit the %d-round safety net; read the transcript" % MAX_ROUNDS)


# ---------------------------------------------------------------- recorded reply
# What Claude actually sends back. Turn one asks for both tools at once and
# includes a sentence of prose, which is why "there is text" never means "done".
SCRIPT = [
    recorded(
        say("Let me check the order and your account details."),
        call("toolu_01", "lookup_order", order_id="8891"),
        call("toolu_02", "get_customer", email="ana@example.com"),
    ),
    recorded(
        say("Order 8891 is in transit, arriving 24 September, "
            "and your address is still 12 Mill Lane, Leeds."),
    ),
]

if __name__ == "__main__":
    banner("1.1 multi-tool agent loop")
    client = get_client(SCRIPT)

    answer, rounds = agent(
        client,
        "Where is order 8891, and is the address on my account still right? "
        "My email is ana@example.com",
    )
    print("answer :", answer)
    print("rounds :", rounds, "(two tools ran inside round 1, not one per round)")
    print()
    print("Both lookups arrived in one reply, so they ran together and the")
    print("customer waited for one round trip instead of two.")
