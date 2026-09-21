"""4.6 Build a multi-pass review system.

The session that wrote the code defends it. A separate one does not.
And a confidence number means nothing until you check it.

Run it:  python ex_4_6_fresh_eyes.py
"""
from collections import defaultdict


# ---------------------------------------------------------------- START HERE
def review(diff, criteria, generator_reasoning=None):
    """Pass generator_reasoning=None. Anything else is self-review."""
    saw_its_own_reasoning = generator_reasoning is not None
    defects = [d for d in diff["defects"]]
    if saw_its_own_reasoning:
        # it already decided these were acceptable while writing them
        defects = [d for d in defects if d not in generator_reasoning["justified"]]
    return defects


def calibrate(labelled):
    """Compare the model's confidence against known outcomes."""
    buckets = defaultdict(lambda: [0, 0])
    for row in labelled:
        b = round(row["confidence"], 1)
        buckets[b][1] += 1
        buckets[b][0] += int(row["was_real"])
    return {b: correct / total for b, (correct, total) in sorted(buckets.items())}


def may_auto_post(confidence, calibration, threshold=0.9):
    actual = calibration.get(round(confidence, 1))
    return actual is not None and actual >= threshold


if __name__ == "__main__":
    diff = {"defects": ["removed guard", "off-by-one", "missing await"]}
    reasoning = {"justified": ["removed guard"]}   # it thought that one was fine

    print("same session  :", review(diff, "criteria", reasoning))
    print("fresh instance:", review(diff, "criteria"))

    labelled = ([{"confidence": 0.9, "was_real": True}] * 62 +
                [{"confidence": 0.9, "was_real": False}] * 38)
    cal = calibrate(labelled)
    print(f"\na score of 0.9 has actually meant {cal[0.9]:.0%} correct")
    print("auto-post at 0.9?", may_auto_post(0.9, cal))
    print("\nUntil you have checked, a confidence score is a number the model")
    print("produced, not a measurement.")
