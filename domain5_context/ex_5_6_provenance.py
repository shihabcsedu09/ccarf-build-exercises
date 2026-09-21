"""5.6 Build a provenance-preserving synthesis pipeline.

Every claim keeps its source through every summarisation step. Two sources
that disagree are reported as two, with their dates.

Run it:  python ex_5_6_provenance.py
"""
from pprint import pprint



# ---------------------------------------------------------------- START HERE
def claim(text, url, document, excerpt, published):
    return {"claim": text, "source_url": url, "document": document,
            "excerpt": excerpt, "published": published}


def summarise(claims):
    """The summary step that usually loses attribution. Here the claim and
    its source move together, so there is nothing to lose."""
    return [{"claim": c["claim"], "source_url": c["source_url"],
             "published": c["published"]} for c in claims]


def reconcile(claims):
    """Same question, different answers. Annotate both, newest first."""
    by_topic = {}
    for c in claims:
        by_topic.setdefault(c["topic"], []).append(c)
    out = []
    for topic, group in by_topic.items():
        group.sort(key=lambda c: c["published"], reverse=True)
        if len(group) == 1:
            out.append({"topic": topic, "value": group[0]["claim"],
                        "sources": [group[0]["source_url"]]})
        else:
            out.append({"topic": topic, "conflict": True,
                        "values": [(c["claim"], c["published"],
                                    c["source_url"]) for c in group],
                        "reading": "later figure may be a trend, not a "
                                   "contradiction"})
    return out


def unsupported(draft_claims, sourced):
    """A sentence with no source does not go in the report."""
    known = {c["claim"] for c in sourced}
    return [c for c in draft_claims if c not in known]


if __name__ == "__main__":
    sourced = [
        dict(claim("EU market share reached 12%", "https://a.example/q1",
                   "Q1 market report", "share rose to 12% in Q1", "2026-04-02"),
             topic="eu_share"),
        dict(claim("EU market share reached 15%", "https://b.example/q3",
                   "Q3 market report", "share stands at 15%", "2026-10-11"),
             topic="eu_share"),
        dict(claim("Regulation takes effect in 2027", "https://c.example/reg",
                   "Directive brief", "applies from 1 Jan 2027", "2026-06-30"),
             topic="regulation"),
    ]

    print("after summarisation, each line still names its source:")
    for c in summarise(sourced):
        print("  -", c["claim"], "->", c["source_url"], c["published"])

    print("\nreconciled:")
    for r in reconcile(sourced):
        pprint(r, width=72)

    draft = ["EU market share reached 15%", "Growth is expected to continue"]
    print("\nno source, so it is cut:", unsupported(draft, sourced))
