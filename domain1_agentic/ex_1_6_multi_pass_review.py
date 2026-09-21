"""1.6 Split a big job into passes.

Real scenario: the CI reviewer from the exam. A pull request touches fourteen
files. Reviewed in one call, the feedback is detailed on the first files and
thin on the last, and the same pattern gets flagged in one file and approved
in another.

Fix: one call per file, then one call that only looks across files. Each call
has a small job and gives it full attention.

Run it:
    python ex_1_6_multi_pass_review.py                     offline
    ANTHROPIC_API_KEY=sk-... python ex_1_6_multi_pass_review.py    real calls
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, call, get_client, recorded

FINDINGS_TOOL = {
    "name": "report_findings",
    "description": "Report review findings for what you were shown.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {"type": "array", "items": {
                "type": "object",
                "properties": {"file": {"type": "string"},
                               "line": {"type": "integer"},
                               "severity": {"type": "string",
                                            "enum": ["critical", "high", "medium", "low"]},
                               "issue": {"type": "string"}},
                "required": ["file", "line", "severity", "issue"]}}
        },
        "required": ["findings"],
    },
}

PER_FILE_SYSTEM = (
    "Review one file. Report only defects in the lines shown: correctness, "
    "security, data loss. Do not comment on style or on code you cannot see."
)
CROSS_FILE_SYSTEM = (
    "You are given per-file findings and the list of files in one change. "
    "Report only issues that span files: data flow, contracts that no longer "
    "match, duplicated logic. Do not repeat the per-file findings."
)


# ---------------------------------------------------------------- START HERE
def review(client, files):
    """One focused call per file, then one call about how they fit together."""
    per_file = []
    for path, diff in files:
        reply = client.messages.create(
            model=MODEL, max_tokens=1024,
            system=PER_FILE_SYSTEM,
            tools=[FINDINGS_TOOL],
            tool_choice={"type": "tool", "name": "report_findings"},
            messages=[{"role": "user", "content": "File: %s\n%s" % (path, diff)}])
        for block in reply.content:
            if block.type == "tool_use":
                per_file.extend(block.input["findings"])

    # The integration pass. It reads the findings, not the files, so it stays
    # small however many files the change touched.
    reply = client.messages.create(
        model=MODEL, max_tokens=1024,
        system=CROSS_FILE_SYSTEM,
        tools=[FINDINGS_TOOL],
        tool_choice={"type": "tool", "name": "report_findings"},
        messages=[{"role": "user", "content": json.dumps(
            {"files": [p for p, _ in files], "per_file_findings": per_file})}])
    cross = []
    for block in reply.content:
        if block.type == "tool_use":
            cross = block.input["findings"]

    return {"per_file": per_file, "cross_file": cross}


# ---------------------------------------------------------------- recorded replies
FILES = [("orders/total.py", "@@ def total(items): return sum(i.price for i in items)"),
         ("orders/api.py", "@@ def post_order(body): return save(body)"),
         ("orders/tests/test_total.py", "@@ assert total([]) == 0")]


def finding(path, line, severity, issue):
    return {"file": path, "line": line, "severity": severity, "issue": issue}


SCRIPT = [
    recorded(call("t1", "report_findings", findings=[
        finding("orders/total.py", 2, "high", "no rounding, so cents drift on large carts")])),
    recorded(call("t2", "report_findings", findings=[
        finding("orders/api.py", 1, "critical", "request body is saved without validation")])),
    recorded(call("t3", "report_findings", findings=[])),
    recorded(call("t4", "report_findings", findings=[
        finding("orders/api.py", 1, "high",
                "api.py saves a body that total.py later assumes is validated")])),
]

if __name__ == "__main__":
    banner("1.6 per-file passes, then one pass across files")
    out = review(get_client(SCRIPT), FILES)

    print("per-file findings (%d calls, one per file):" % len(FILES))
    for f in out["per_file"]:
        print("   %-28s line %-3d %-8s %s" % (f["file"], f["line"], f["severity"], f["issue"]))
    print()
    print("cross-file findings (1 call, reading the findings not the files):")
    for f in out["cross_file"]:
        print("   %-28s line %-3d %-8s %s" % (f["file"], f["line"], f["severity"], f["issue"]))
    print()
    print("The last finding needed two files at once, so no per-file pass could")
    print("have seen it. That is why the integration pass exists, and why")
    print("asking developers to split the pull request would have hidden it.")
