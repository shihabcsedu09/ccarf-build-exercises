"""5.5 Build a confidence-calibrated review router.

An aggregate accuracy number hides the segment that is failing, and a raw
confidence score means nothing until it has been checked against outcomes.
Calibrate per segment, then route on the calibrated number.

Run it:  python ex_5_5_calibrated_router.py
"""
import random
from collections import defaultdict

BAND = 0.05


# ---------------------------------------------------------------- START HERE
def band(confidence):
    return round(round(confidence / BAND) * BAND, 2)


def accuracy_by_segment(rows):
    """Break the number down by document type, then by type and field."""
    b = defaultdict(lambda: [0, 0])
    for r in rows:
        for key in ((r["doc_type"],), (r["doc_type"], r["field"])):
            b[key][1] += 1
            b[key][0] += int(r["correct"])
    return {k: (hits / n, n) for k, (hits, n) in b.items()}


def calibrate(rows, by_segment=True):
    """What a reported score has actually meant. Keyed by (segment, band)
    when by_segment, otherwise by band alone."""
    b = defaultdict(lambda: [0, 0])
    for r in rows:
        key = (r["doc_type"], band(r["confidence"])) if by_segment \
            else band(r["confidence"])
        b[key][1] += 1
        b[key][0] += int(r["correct"])
    return {k: (hits / n, n) for k, (hits, n) in b.items()}


def route(doc_type, confidence, calibration, min_rows=30,
          auto_at=0.95, spot_at=0.75):
    key = (doc_type, band(confidence))
    entry = calibration.get(key) or calibration.get(band(confidence))
    if entry is None or entry[1] < min_rows:
        return "human review (not enough labelled rows to trust this band)"
    real, _ = entry
    if real >= auto_at:
        return f"auto-accept (this band has run {real:.0%})"
    if real >= spot_at:
        return f"spot check (this band has run {real:.0%})"
    return f"human review (this band has run {real:.0%})"


def sample_for_audit(rows, rate=0.02, seed=0):
    """High-confidence rows are sampled on purpose. They are the ones nobody
    would otherwise ever look at again."""
    rnd = random.Random(seed)
    return [r for r in rows if rnd.random() < rate]


if __name__ == "__main__":
    rows = ([{"doc_type": "typed_invoice", "field": "total",
              "confidence": 0.96, "correct": True}] * 900 +
            [{"doc_type": "handwritten", "field": "total",
              "confidence": 0.96, "correct": i < 60} for i in range(100)])

    seg = accuracy_by_segment(rows)
    overall = sum(r["correct"] for r in rows) / len(rows)
    print(f"overall            : {overall:.0%}   <- the number on the dashboard")
    print("typed invoices     : {:.0%} over {} rows".format(*seg[("typed_invoice",)]))
    print("handwritten        : {:.0%} over {} rows".format(*seg[("handwritten",)]))

    pooled = calibrate(rows, by_segment=False)
    per_seg = calibrate(rows, by_segment=True)

    print(f"\nboth document types report 0.96 confidence.")
    print("routed on the pooled curve:")
    print("  typed       ->", route("typed_invoice", 0.96, pooled))
    print("  handwritten ->", route("handwritten", 0.96, pooled))
    print("routed on the per-segment curve:")
    print("  typed       ->", route("typed_invoice", 0.96, per_seg))
    print("  handwritten ->", route("handwritten", 0.96, per_seg))

    print("\nunseen segment     ->", route("receipt_photo", 0.96, per_seg))
    audit = sample_for_audit(rows)
    print(f"audit sample       : {len(audit)} rows, high-confidence included")
