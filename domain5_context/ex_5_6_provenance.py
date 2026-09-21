"""5.6 Carry the source with the claim, all the way through.

Real scenario: the final report says "industry sources estimate 30% adoption"
with nothing attached. The searcher had the survey name. Each step summarised
the step before it in prose, and the attribution fell out somewhere in the
middle.

Citations cannot be reconstructed at the end. They travel as fields, or they
are gone.

And when two good sources disagree, report both with their dates. Often the
disagreement is two years, not a contradiction.

Run it:
    python ex_5_6_provenance.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, get_client, recorded, say

FINDINGS = [
    {"claim": "Streaming revenue grew 12.1% in 2025",
     "source_url": "https://www.ifpi.org/global-report-2026",
     "document": "IFPI Global Music Report 2026",
     "excerpt": "streaming revenue grew 12.1% year on year",
     "published": "2026-03-01", "confidence": "well-established"},
    {"claim": "The market was worth 4bn",
     "source_url": "https://example.gov/report-2019",
     "document": "Government market review",
     "excerpt": "the sector is valued at 4bn",
     "published": "2019-06-01", "confidence": "single-source"},
    {"claim": "The market was worth 9bn",
     "source_url": "https://example.org/industry-2026",
     "document": "Industry analysis 2026",
     "excerpt": "we size the market at 9bn",
     "published": "2026-03-01", "confidence": "single-source"},
]

REQUIRED_FIELDS = ("claim", "source_url", "document", "excerpt", "published")


# ---------------------------------------------------------------- START HERE
def summarise_as_prose(findings):
    """What every step used to do. Readable, and the receipts are gone."""
    return " ".join(f["claim"] + "." for f in findings)


def summarise_keeping_fields(findings):
    """Compress the wording, keep the fields. Shorter, still attributable."""
    return [{"claim": f["claim"][:60], "source_url": f["source_url"],
             "document": f["document"], "published": f["published"],
             "confidence": f["confidence"]} for f in findings]


def attribution_survives(records):
    """The check worth running after every hop, not at the end."""
    if isinstance(records, str):
        return False, "prose: no fields left to check"
    missing = [f for f in ("source_url", "document", "published")
               if any(f not in r for r in records)]
    return (not missing), ("missing %s" % missing if missing else "intact")


def find_conflicts(findings):
    """Two sources, one metric, different numbers. Keep both, with the dates."""
    conflicts = []
    market = [f for f in findings if "market was worth" in f["claim"]]
    if len(market) > 1:
        conflicts.append({
            "metric": "market size",
            "values": [{"value": f["claim"].split()[-1], "document": f["document"],
                        "published": f["published"]} for f in market],
            "note": ("published %s apart; likely growth over time rather than a "
                     "contradiction. The coordinator decides, not this step."
                     % _years_apart(market)),
        })
    return conflicts


def _years_apart(items):
    years = sorted(int(f["published"][:4]) for f in items)
    return "%d years" % (years[-1] - years[0])


def report_section(findings, conflicts):
    """Numbers as a table, disagreements called out, nothing averaged."""
    lines = ["| claim | source | published |", "|---|---|---|"]
    for f in findings:
        lines.append("| %s | %s | %s |" % (f["claim"], f["document"], f["published"]))
    for c in conflicts:
        lines.append("")
        lines.append("Disagreement on %s: %s" % (c["metric"], c["note"]))
        for v in c["values"]:
            lines.append("  - %s (%s, %s)" % (v["value"], v["document"], v["published"]))
    return "\n".join(lines)


def synthesise(client, records):
    """The writing step. It can only cite what the records still carry."""
    reply = client.messages.create(
        model=MODEL, max_tokens=500,
        system=("Write two sentences from these findings. Cite the document and "
                "date for every claim. If a finding has no source, say so rather "
                "than writing the claim as fact."),
        messages=[{"role": "user", "content": json.dumps(records)}])
    return "".join(b.text for b in reply.content if b.type == "text")


FROM_PROSE = [recorded(say(
    "Streaming revenue grew 12.1% in 2025. I cannot attribute this claim: the "
    "input carried no source or date."))]
FROM_FIELDS = [recorded(say(
    "Streaming revenue grew 12.1% in 2025 (IFPI Global Music Report 2026, "
    "published 2026-03-01)."))]

if __name__ == "__main__":
    banner("5.6 provenance through the pipeline")
    print("what each finding carries at the start: %s" % ", ".join(REQUIRED_FIELDS))
    print()

    prose = summarise_as_prose(FINDINGS)
    ok, why = attribution_survives(prose)
    print("hop 1 summarised as prose:")
    print("  ", prose[:110])
    print("   attribution intact:", ok, "-", why)
    print()

    structured = summarise_keeping_fields(FINDINGS)
    ok, why = attribution_survives(structured)
    print("hop 1 summarised as fields:")
    print("  ", json.dumps(structured[0]))
    print("   attribution intact:", ok, "-", why)
    print()

    print("what the writer produces from each:")
    print("   from prose :", synthesise(get_client(FROM_PROSE), [{"claim": c} for c in
                                        [f["claim"] for f in FINDINGS[:1]]]))
    print("   from fields:", synthesise(get_client(FROM_FIELDS), structured[:1]))
    print()

    conflicts = find_conflicts(FINDINGS)
    print("the report:")
    print(report_section(FINDINGS[:1], conflicts))
    print()
    print("Neither figure was dropped and nothing was averaged. The reader can")
    print("see that one number is from 2019 and the other from 2026, which is")
    print("the fact that resolves the apparent contradiction.")
