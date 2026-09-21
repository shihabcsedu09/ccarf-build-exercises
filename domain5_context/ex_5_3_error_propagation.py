"""5.3 Build a structured error propagation system.

An error that reaches the model carries four things: what failed, what was
being attempted, what was already gathered, and what to try instead.

Run it:  python ex_5_3_error_propagation.py
"""
from pprint import pprint


TRANSIENT = ("timeout", "connection_reset", "rate_limited")


# ---------------------------------------------------------------- START HERE
def error_context(failure_type, attempted, partial, alternatives):
    return {"status": "error",
            "failure_type": failure_type,
            "attempted_action": attempted,
            "partial_results": partial,
            "alternatives": alternatives}


def empty_result(query):
    """An empty answer is a successful call. Reporting it as an error sends
    the agent looking for a fault that is not there."""
    return {"status": "success", "query": query, "results": [],
            "note": "the search ran and matched nothing"}


def call_with_retry(fn, attempted, partial, alternatives, tries=3):
    last = None
    for attempt in range(1, tries + 1):
        try:
            return fn(attempt)
        except RuntimeError as e:
            last = str(e)
            if last not in TRANSIENT:
                break                      # a permanent fault: stop retrying
    return error_context(last, attempted, partial, alternatives)


# ---------------------------------------------------------------- stubs
def flaky(attempt):
    if attempt < 3:
        raise RuntimeError("timeout")
    return {"status": "success", "results": ["invoice 42"]}


def permanent(attempt):
    raise RuntimeError("permission_denied")


if __name__ == "__main__":
    print("transient, recovers :", call_with_retry(
        flaky, "read the invoice index", {"vendors": 2}, ["cached index"]))

    print("\npermanent, reported :")
    for k, v in call_with_retry(
            permanent, "read the payroll ledger",
            {"rows_so_far": 118},
            ["ask for read access", "use last night's export"]).items():
        print(f"  {k}: {v}")

    print("\nempty but fine:")
    pprint(empty_result("invoices from 2019"), width=74)
    print("\nSilently swallowing the first one would have the agent report")
    print("a total that is missing 118 rows and say nothing about it.")
