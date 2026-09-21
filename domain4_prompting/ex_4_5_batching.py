"""4.5 Use the Batches API for work nobody is waiting on.

Real scenario: three jobs. A pre-merge check that blocks the merge button, a
weekly security audit, and nightly test generation.

Batch is half price and can take up to 24 hours. That makes it right for two
of those three, and wrong for the one with a developer waiting.

The custom_id is what makes a partial failure cheap: 300 of 10,000 documents
failed, and you resubmit exactly those 300.

Run it:
    python ex_4_5_batching.py
"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, get_client

# someone_waiting: is a person or a merge blocked until this returns?
# needs_tools:     does Claude have to call a tool and continue on the result?
JOBS = [
    ("pre-merge style check", True, False, "blocks the merge button"),
    ("weekly security audit", False, False, "read on Monday morning"),
    ("nightly test generation", False, False, "read the next morning"),
    ("iterative code review with tool calls", False, True, "requests related files mid-run"),
    ("live chat classification", True, False, "a customer is on the page"),
]


# ---------------------------------------------------------------- START HERE
def choose_api(someone_waiting, needs_tools_midway):
    """Two questions, and neither one is about size.

    The batch window is up to 24 hours with no promised delivery time, so the
    test is whether anybody is blocked, not how big the job is.
    """
    if needs_tools_midway:
        # A batch request is one shot. There is no way to run a tool and hand
        # the result back for Claude to continue, so the loop cannot exist.
        return "synchronous", "batch cannot execute tools mid-request"
    if someone_waiting:
        return "synchronous", "a person or a merge is blocked until it returns"
    return "batch", "half price, and nothing is waiting on it"


def build_requests(documents):
    """Each request carries your own id, echoed back on its result."""
    return [{
        "custom_id": "doc-%s" % doc["id"],          # your key, not Anthropic's
        "params": {
            "model": MODEL,
            "max_tokens": 2048,
            "system": "Extract the invoice fields.",
            "messages": [{"role": "user", "content": doc["text"]}],
        },
    } for doc in documents]


def submit_and_collect(client, documents, poll_seconds=30):
    """Submit, poll until the batch ends, then split results by custom_id."""
    requests = build_requests(documents)
    batch = client.messages.batches.create(requests=requests)

    # Submitting returns immediately with processing_status "in_progress".
    # Results do not exist until the batch ends, so you poll for that first.
    # Asking for results early is the usual mistake and it raises.
    status = client.messages.batches.retrieve(batch.id)
    while status.processing_status != "ended":
        time.sleep(poll_seconds)      # minutes, not milliseconds: it is a batch
        status = client.messages.batches.retrieve(batch.id)

    # Results stream back in no particular order, which is why custom_id
    # matters: it is the only thread from a result back to your document.
    succeeded, failed = [], {}
    for entry in client.messages.batches.results(batch.id):
        if entry.result.type == "succeeded":
            succeeded.append(entry.custom_id)
        else:
            failed[entry.custom_id] = entry.result.error.type
    return batch, status, succeeded, failed


def repair(failed):
    """Fix the cause, then resubmit only the failures. Not the whole batch."""
    plan = {}
    for custom_id, reason in failed.items():
        if reason == "invalid_request_too_long":
            plan[custom_id] = "chunk the document, then resubmit"
        elif reason in ("api_error", "overloaded_error"):
            plan[custom_id] = "resubmit unchanged; it was transient"
        else:
            plan[custom_id] = "inspect by hand"
    return plan


if __name__ == "__main__":
    banner("4.5 batch or synchronous")
    print("%-40s %-14s %s" % ("job", "api", "why"))
    print("-" * 78)
    for name, someone_waiting, needs_tools, note in JOBS:
        api, why = choose_api(someone_waiting, needs_tools)
        print("%-40s %-14s %s" % (name, api, why))
    print()

    documents = [{"id": "%04d" % i, "text": "INVOICE ..."} for i in range(1, 11)]
    failures = {"doc-0003": "invalid_request_too_long",
                "doc-0007": "overloaded_error"}
    client = get_client(batch_failures=failures)

    batch, status, ok, failed = submit_and_collect(client, documents)
    print("submitted %d documents as %s" % (len(documents), batch.id))
    print("ended: %d succeeded, %d errored"
          % (status.request_counts.succeeded, status.request_counts.errored))
    print()
    print("failures, found by the id you chose at submission:")
    for custom_id, reason in sorted(failed.items()):
        print("   %-12s %s" % (custom_id, reason))
    print()
    print("what to resubmit:")
    for custom_id, action in sorted(repair(failed).items()):
        print("   %-12s %s" % (custom_id, action))
    print()
    print("You resubmit %d of %d. Without custom_id you could not tell which"
          % (len(failed), len(documents)))
    print("documents failed, and the only repair left is rerunning all of them.")
    print()
    print("SLA arithmetic: a 36-hour promise and a 24-hour window leaves 12")
    print("hours, so submit at least every 12 hours to stay inside it.")
