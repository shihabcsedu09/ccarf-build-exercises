"""4.5 Design a batch processing strategy.

Half price, up to a day, one shot per request. The arithmetic question
comes up often: deadline minus the window is your submission interval.

Run it:  python ex_4_5_batching.py
"""
from pprint import pprint


BATCH_WINDOW_HOURS = 24


# ---------------------------------------------------------------- START HERE
def use_batch(someone_is_waiting, needs_tools_midway):
    """Two questions decide it."""
    if someone_is_waiting:
        return False          # a person or a merge is blocked
    if needs_tools_midway:
        return False          # a batch item is one shot, no tool round-trips
    return True


def max_interval_hours(deadline_hours, window_hours=BATCH_WINDOW_HOURS):
    """Worst case = waiting to be submitted + the processing window."""
    return deadline_hours - window_hours


def build_requests(documents):
    """custom_id is how a result finds its row again: order is not a key."""
    return [{"custom_id": f"doc-{d['id']}", "params": {"messages": d["text"]}}
            for d in documents]


def triage(results):
    """Resubmit only what failed, and only the ones a retry can help."""
    ok, retry, dead = [], [], []
    for r in results:
        if r["type"] == "succeeded":
            ok.append(r["custom_id"])
        elif r["error"] in ("api_error", "overloaded_error", "expired"):
            retry.append(r["custom_id"])
        else:
            dead.append((r["custom_id"], r["error"]))
    return ok, retry, dead


if __name__ == "__main__":
    workloads = [
        ("interactive upload validation", True,  False),
        ("nightly archive reprocessing",  False, False),
        ("review needing a tool mid-way", False, True),
    ]
    for label, waiting, tools in workloads:
        print(f"{label:32} -> {'batch' if use_batch(waiting, tools) else 'synchronous'}")

    print(f"\na 36-hour promise -> submit every {max_interval_hours(36)} hours at most")
    print(f"a 30-hour promise -> submit every {max_interval_hours(30)} hours at most")

    print("\nrequests:")
    pprint(build_requests([{"id": 1, "text": "..."},
                           {"id": 2, "text": "..."}]), width=74)
    results = [{"custom_id": "doc-1", "type": "succeeded"},
               {"custom_id": "doc-2", "type": "errored", "error": "overloaded_error"},
               {"custom_id": "doc-3", "type": "errored",
                "error": "invalid_request_error"}]
    ok, retry, dead = triage(results)
    print(f"\nok={ok} retry={retry} needs_chunking={dead}")
    print("Resubmitting the whole batch would pay again for doc-1.")
