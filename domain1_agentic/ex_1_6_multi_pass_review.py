"""1.6 Build a multi-pass code review pipeline.

One pass per file gives consistent depth. A second pass over the
findings catches what only exists between files.

Run it:  python ex_1_6_multi_pass_review.py
"""


# ---------------------------------------------------------------- START HERE
def review_pull_request(files, review_one, review_across):
    """files: {path: diff}. Returns per-file findings plus cross-file ones."""
    per_file = []
    summaries = {}
    for path, diff in files.items():          # independent: safe to run in parallel
        per_file += review_one(path, diff)
        summaries[path] = one_line(path, diff)

    cross = review_across(summaries, per_file)
    return per_file + cross


def one_line(path, diff):
    return f"{path}: {len(diff.splitlines())} changed lines"


# ---------------------------------------------------------------- stubs
def review_one(path, diff):
    if "def " in diff and "test" not in path:
        return [{"file": path, "kind": "local", "message": "new branch has no test"}]
    return []


def review_across(summaries, per_file):
    signatures = [f for f in summaries if "api.py" in f]
    callers = [f for f in summaries if "client.py" in f]
    if signatures and callers:
        return [{"file": callers[0], "kind": "cross",
                 "message": "api.py changed its signature; client.py was not updated"}]
    return []


def single_pass(files, review_one):
    """What one review of everything at once tends to produce: thorough on the
    first file, thin afterwards, and blind to anything spanning files."""
    findings = []
    for i, (path, diff) in enumerate(files.items()):
        if i < 2:
            findings += review_one(path, diff)
    return findings


if __name__ == "__main__":
    files = {f"src/mod{i}.py": "def f():\n    pass\n" for i in range(1, 6)}
    files["src/api.py"] = "def send(a, b):\n    pass\n"
    files["src/client.py"] = "def call():\n    pass\n"

    one = single_pass(files, review_one)
    many = review_pull_request(files, review_one, review_across)
    print(f"single pass : {len(one)} findings, cross-file: "
          f"{sum(1 for f in one if f['kind']=='cross')}")
    print(f"multi pass  : {len(many)} findings, cross-file: "
          f"{sum(1 for f in many if f['kind']=='cross')}")
    for f in many:
        if f["kind"] == "cross":
            print("  the pass across files found:", f["message"])
