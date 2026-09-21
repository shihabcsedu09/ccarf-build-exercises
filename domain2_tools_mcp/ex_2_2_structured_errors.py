"""2.2 Build structured errors for all four categories.

Every failure answers three questions: what kind, could a retry work,
and what should happen instead.

Run it:  python ex_2_2_structured_errors.py
"""


def tool_error(category, retryable, message, customer_message=None, **extra):
    return {"isError": True, "errorCategory": category, "isRetryable": retryable,
            "message": message, "customerMessage": customer_message, **extra}


# ---------------------------------------------------------------- START HERE
def process_refund(order_id, amount, backend):
    """Turn one backend outcome into one structured result."""
    outcome = backend(order_id, amount)

    if outcome == "timeout":
        return tool_error("transient", True, "Payment gateway timed out.",
                          "This is taking longer than usual, let me try again.")
    if outcome == "unknown_order":
        return tool_error("validation", False, f"No order matches {order_id!r}.",
                          "I could not find that order number.")
    if outcome == "window_expired":
        return tool_error("business", False, "Return window closed.",
                          "This order passed its 30-day return window.")
    if outcome == "forbidden":
        return tool_error("permission", False, "Account lacks refund scope.",
                          "I need to pass this to a colleague.")
    return {"isError": False, "refund_id": "RF-1", "amount": amount}


def search_orders(rows):
    """A search that ran and found nothing is a SUCCESS, not an error."""
    return {"isError": False, "count": len(rows), "orders": rows}


def decide(result, attempt=0):
    """What the agent does next, driven by the metadata."""
    if not result["isError"]:
        return "continue"
    if result["isRetryable"] and attempt < 2:
        return "retry_with_backoff"
    if result["errorCategory"] == "validation":
        return "ask_for_a_better_identifier"
    if result["errorCategory"] == "business":
        return "explain_and_offer_alternative"
    return "escalate_to_human"


if __name__ == "__main__":
    for outcome in ("timeout", "unknown_order", "window_expired", "forbidden", "ok"):
        r = process_refund("8891", 40, lambda o, a, x=outcome: x)
        print(f"{outcome:15} category={r.get('errorCategory','-'):11} "
              f"retryable={str(r.get('isRetryable','-')):5} -> {decide(r)}")

    print(f"\n{'empty search':15} " + "-" * 34 +
          f" -> {decide(search_orders([]))}")
    print(f"{'timeout, 3rd try':15} " + "-" * 34 +
          f" -> {decide(process_refund('8891', 40, lambda o,a:'timeout'), attempt=2)}")
