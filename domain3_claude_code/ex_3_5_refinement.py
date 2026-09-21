"""3.5 Practise the refinement techniques.

Four situations, four different answers. Picking the technique that
fits a different situation is the exam's favourite wrong answer.

Run it:  python ex_3_5_refinement.py
"""


# ---------------------------------------------------------------- START HERE
def technique(you_know_the_target, prose_keeps_being_misread,
              problems_interact, domain_is_unfamiliar):
    if domain_is_unfamiliar:
        return "interview: let Claude ask you questions, then write SPEC.md"
    if problems_interact:
        return "one message describing all the problems together"
    if prose_keeps_being_misread:
        return "show two or three before-and-after examples"
    if you_know_the_target:
        return "write the tests first, then iterate on the failures"
    return "describe it once more, then reassess"


EXAMPLE_PAIR = """Transform these API responses. Examples:

IN  {"user_id": 1, "created": 1735689600}
OUT {"id": "1", "createdAt": "2025-01-01T00:00:00Z"}

IN  {"user_id": 2, "created": null}
OUT {"id": "2", "createdAt": null}          <- the absent case, shown"""

INTERACTING = """Three problems interact, so fix them together:
1. pagination uses the wrong offset
2. results are sorted before filtering
3. duplicates are removed before the sort

Required order: filter, de-duplicate, sort, paginate."""

if __name__ == "__main__":
    cases = [
        ("prose keeps being misread",  False, True,  False, False),
        ("you know exactly what is correct", True, False, False, False),
        ("three bugs undo each other", False, False, True,  False),
        ("a domain you do not know",   False, False, False, True),
    ]
    for label, known, misread, interact, unfamiliar in cases:
        print(f"{label:34} -> {technique(known, misread, interact, unfamiliar)}")

    print("\n--- showing beats describing ---\n" + EXAMPLE_PAIR)
    print("\n--- interacting problems go in one message ---\n" + INTERACTING)
