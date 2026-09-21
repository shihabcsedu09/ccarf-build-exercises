"""4.1 Build a review prompt with explicit criteria.

"Be conservative" gives the model nothing to check itself against.
A rule it can test does.

Run it:  python ex_4_1_explicit_criteria.py
"""

VAGUE = "Be conservative. Only report issues you are highly confident about."

# ---------------------------------------------------------------- START HERE
EXPLICIT = """Report only these:
  correctness  a path that produces a wrong result. You must be able to name
               the input that triggers it.
  security     unvalidated input reaching a query, a command or a file path.
  tests        a new branch with no test, where a test file already covers
               that function.

Skip these, always:
  - naming, formatting, import order: the linter owns them
  - a pattern already used elsewhere in the repository
  - anything you cannot name a failing input for

Severity, by example:
  critical  db.query("... WHERE id = " + req.params.id)
  major     const u = users.find(...); return u.email
  minor     catch (e) { log(e) } with no re-throw"""


def can_check(finding, criteria_are_explicit):
    """The test a model can apply to its own finding before reporting it."""
    if not criteria_are_explicit:
        return True                     # "confident enough" always passes
    return finding.get("triggering_input") is not None


def review(findings, criteria_are_explicit):
    return [f for f in findings if can_check(f, criteria_are_explicit)]


ENABLED = {"correctness": True, "security": True, "tests": True, "style": False}


def trust_recovery(category_false_positive_rates, threshold=0.4):
    """Switch off a noisy category while you fix it, rather than letting it
    poison the reader's view of the accurate ones."""
    return {c: r <= threshold for c, r in category_false_positive_rates.items()}


if __name__ == "__main__":
    findings = [
        {"message": "possible confusing naming"},                      # no input
        {"message": "maybe incomplete validation"},                    # no input
        {"message": "crashes on empty cart", "triggering_input": "cart=[]"},
        {"message": "SQL injection in /orders", "triggering_input": "id=1 OR 1=1"},
    ]
    print(f"vague prompt    : {len(review(findings, False))} findings reported")
    print(f"explicit criteria: {len(review(findings, True))} findings reported")
    for f in review(findings, True):
        print("   kept:", f["message"], "->", f["triggering_input"])

    rates = {"correctness": 0.08, "security": 0.05, "style": 0.52, "docs": 0.48}
    print("\ncategories to keep on:", trust_recovery(rates))
