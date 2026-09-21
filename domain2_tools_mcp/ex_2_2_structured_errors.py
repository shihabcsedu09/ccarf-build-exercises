"""2.2 Return errors the agent can act on.

Real scenario: process_refund returns the string "Operation failed" whatever
went wrong. The agent retries the refunds that policy will never allow, and
gives up on the ones that were only a timeout.

A useful error says which of four kinds it is, whether the same call could
work later, and what to do instead.

Run it:
    python ex_2_2_structured_errors.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner

# The four kinds. The agent's next move is different for every one of them.
TRANSIENT = "transient"       # timeout, rate limit, 5xx: the same call may work
VALIDATION = "validation"     # the arguments were wrong: fix them and retry once
BUSINESS = "business"         # a rule says no: explain it, never retry
PERMISSION = "permission"     # not allowed at all: stop and escalate


# ---------------------------------------------------------------- START HERE
def tool_error(category, message, retryable, do_instead=None, details=None):
    """One shape for every failure, so the agent never has to guess."""
    payload = {"error": {"category": category,
                         "retryable": retryable,
                         "message": message}}
    if do_instead:
        payload["error"]["do_instead"] = do_instead
    if details:
        payload["error"]["details"] = details
    return payload


def as_tool_result(tool_use_id, payload, is_error):
    """How the failure travels back in the Messages API: a normal tool_result,
    flagged. The call itself succeeded; the work inside it did not."""
    return {"type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": json.dumps(payload),
            "is_error": is_error}


def as_mcp_result(payload, is_error):
    """The same failure from an MCP server. isError is the machine-readable
    flag; structuredContent carries the fields."""
    return {"isError": is_error,
            "content": [{"type": "text", "text": payload["error"]["message"]
                         if is_error else "ok"}],
            "structuredContent": payload}


def process_refund(order_id, amount, world):
    """The tool itself. Every failure path returns a category, never a sentence."""
    if world.get("gateway_down"):
        return tool_error(TRANSIENT, "payment gateway timed out after 30s", True,
                          "retry with backoff; escalate if it keeps failing"), True
    if amount <= 0:
        return tool_error(VALIDATION, "amount must be greater than zero", True,
                          "correct the amount and call again"), True
    if world.get("days_since_purchase", 0) > 30:
        return tool_error(BUSINESS, "outside the 30-day returns window", False,
                          "explain the policy to the customer in plain words",
                          {"window_days": 30,
                           "days_since_purchase": world["days_since_purchase"]}), True
    if not world.get("agent_may_refund", True):
        return tool_error(PERMISSION, "this agent cannot issue refunds", False,
                          "call escalate_to_human with the case summary"), True
    return {"refunded": amount, "order_id": order_id}, False


def agent_next_move(payload):
    """What a correct agent does with each category. This is the whole payoff."""
    err = payload.get("error")
    if not err:
        return "tell the customer it is done"
    return {TRANSIENT: "retry with backoff",
            VALIDATION: "fix the arguments and retry once",
            BUSINESS: "explain the rule, do not retry",
            PERMISSION: "stop and escalate"}[err["category"]]


if __name__ == "__main__":
    banner("2.2 structured tool errors", api=False)
    cases = [
        ("gateway down", {"gateway_down": True}),
        ("negative amount", {}),
        ("past the window", {"days_since_purchase": 45}),
        ("not permitted", {"agent_may_refund": False}),
        ("all fine", {}),
    ]
    for label, world in cases:
        amount = -5 if label == "negative amount" else 47.90
        payload, failed = process_refund("8891", amount, world)
        err = payload.get("error", {})
        print("%-18s category=%-11s retryable=%-5s -> %s"
              % (label, err.get("category", "-"), err.get("retryable", "-"),
                 agent_next_move(payload)))
    print()
    print("One failure, both transports:")
    payload, failed = process_refund("8891", 47.90, {"days_since_purchase": 45})
    print("  Messages API :", json.dumps(as_tool_result("toolu_9", payload, failed))[:110], "...")
    print("  MCP server   :", json.dumps(as_mcp_result(payload, failed))[:110], "...")
    print()
    print("A search that ran and found nothing is not in this list. Zero results")
    print("is a successful answer, and marking it an error causes pointless retries.")
