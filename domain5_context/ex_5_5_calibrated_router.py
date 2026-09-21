"""5.5 Route work to reviewers on a number that means something.

Real scenario: extraction is "97% accurate" and leadership wants to stop
reviewing anything the model is confident about. Reviewers can check 500 of
4,000 documents a day, and today every tenth one is sampled at random.

97% is an average. Averages hide the document type that is wrong four times
in ten. And a confidence score means nothing until it has been checked
against labelled data.

Segment, calibrate, route, then keep sampling what you automated.

Run it:
    python ex_5_5_calibrated_router.py
"""
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner

# A labelled set: what the model said, how sure it said it was, and the truth.
# Read the handwritten rows carefully: the wrong ones are just as confident as
# the right ones. That is what an uncalibrated score looks like, and no
# threshold can rescue it.
LABELLED = (
    [{"type": "typed_invoice", "confidence": 0.97, "correct": True}] * 570
    + [{"type": "typed_invoice", "confidence": 0.80, "correct": False}] * 6
    + [{"type": "scanned_receipt", "confidence": 0.97, "correct": True}] * 240
    + [{"type": "scanned_receipt", "confidence": 0.85, "correct": False}] * 24
    + [{"type": "handwritten", "confidence": 0.98, "correct": True}] * 96
    + [{"type": "handwritten", "confidence": 0.98, "correct": False}] * 64
)


# ---------------------------------------------------------------- START HERE
def overall_accuracy(rows):
    """The number that gets quoted, and the one that hides the problem."""
    return sum(1 for r in rows if r["correct"]) / float(len(rows))


def accuracy_by_type(rows):
    """Segment first. This is the step that makes the average honest."""
    out = {}
    for r in rows:
        bucket = out.setdefault(r["type"], [0, 0])
        bucket[1] += 1
        if r["correct"]:
            bucket[0] += 1
    return dict((k, v[0] / float(v[1])) for k, v in out.items())


def calibrate(rows, target_accuracy=0.99):
    """Does 'confident' mean 'right' for this document type?

    A threshold is only meaningful once you have checked what the score
    predicts, per segment. Types that cannot reach the target do not get one.
    """
    thresholds = {}
    for doc_type in set(r["type"] for r in rows):
        segment = [r for r in rows if r["type"] == doc_type]
        best = None
        for cut in [0.90, 0.92, 0.94, 0.95, 0.96, 0.98, 0.99]:
            above = [r for r in segment if r["confidence"] >= cut]
            if not above:
                continue
            if sum(1 for r in above if r["correct"]) / float(len(above)) >= target_accuracy:
                best = cut
                break
        thresholds[doc_type] = best        # None means: never automate this type
    return thresholds


def route(document, thresholds, sample_rate=0.05, rng=random):
    """Three ways to a reviewer, and only one of them is the threshold."""
    cut = thresholds.get(document["type"])

    if document.get("ambiguous_source"):
        # A contradictory or unreadable source is a reason on its own, whatever
        # the score says.
        return "human: source is ambiguous"
    if cut is None:
        return "human: this type has never met the accuracy bar"
    if document["confidence"] < cut:
        return "human: below the calibrated threshold for its type"
    if rng.random() < sample_rate:
        # Keep measuring the part you automated, or a new failure pattern
        # arrives invisibly.
        return "auto, sampled for audit"
    return "auto"


if __name__ == "__main__":
    banner("5.5 calibrated routing", api=False)
    print("the number in the slide deck: %.1f%% accurate" % (overall_accuracy(LABELLED) * 100))
    print()
    print("the same set, split by document type:")
    for doc_type, acc in sorted(accuracy_by_type(LABELLED).items()):
        print("   %-18s %.1f%%" % (doc_type, acc * 100))
    print("   handwritten is wrong 4 times in 10 and the average never showed it.")
    print()

    thresholds = calibrate(LABELLED)
    print("calibrated thresholds, per type:")
    for doc_type, cut in sorted(thresholds.items()):
        print("   %-18s %s" % (doc_type, ("%.2f" % cut) if cut else "no threshold reaches 99%"))
    print()

    rng = random.Random(7)
    incoming = [
        {"type": "typed_invoice", "confidence": 0.99},
        {"type": "typed_invoice", "confidence": 0.84},
        {"type": "scanned_receipt", "confidence": 0.99},
        {"type": "handwritten", "confidence": 0.99},
        {"type": "typed_invoice", "confidence": 0.99, "ambiguous_source": True},
    ]
    print("routing decisions:")
    for doc in incoming:
        print("   %-16s conf %.2f  %s%s"
              % (doc["type"], doc["confidence"],
                 route(doc, thresholds, rng=rng),
                 "  (contradictory scan)" if doc.get("ambiguous_source") else ""))
    print()
    print("A handwritten document at 0.99 still goes to a person, because on")
    print("that type the score has never predicted correctness.")
