"""1.2 Build a hub-and-spoke research coordinator.

Every message goes through the coordinator. A missing topic is the
coordinator's decomposition problem, never the specialist's fault.

Run it:  python ex_1_2_coordinator.py
"""

SPECIALISTS = {
    "searcher": "Find sources for one subtopic. Return findings only.",
    "writer":   "Write the report from the findings given to you. Cite everything.",
}


# ---------------------------------------------------------------- START HERE
def coordinate(topic, decompose, run_specialist, max_refinements=2):
    """Split the topic, fan out, then check the draft for gaps and fill them."""
    subtopics = decompose(topic)
    findings = []
    for sub in subtopics:                       # independent: safe to run in parallel
        findings += run_specialist("searcher", sub)

    draft = run_specialist("writer", findings)

    for _ in range(max_refinements):
        gaps = [s for s in subtopics if not any(f["subtopic"] == s for f in findings)]
        if not gaps:
            break
        for gap in gaps:                        # targeted follow-up, not a full re-run
            findings += run_specialist("searcher", gap)
        draft = run_specialist("writer", findings)

    return {"subtopics": subtopics, "findings": findings, "draft": draft,
            "uncovered": [s for s in subtopics
                          if not any(f["subtopic"] == s for f in findings)]}


# ---------------------------------------------------------------- stubs
def narrow_decompose(topic):
    return ["solar", "wind"]                    # the classic failure: too narrow


def broad_decompose(topic):
    return ["solar", "wind", "geothermal", "tidal", "biomass"]


def run_specialist(role, payload):
    if role == "searcher":
        if payload == "tidal":
            return []                           # nothing found on this pass
        return [{"subtopic": payload, "claim": f"a finding about {payload}"}]
    return f"Report covering: {sorted({f['subtopic'] for f in payload})}"


if __name__ == "__main__":
    narrow = coordinate("renewable energy", narrow_decompose, run_specialist)
    print("narrow split :", narrow["draft"])

    broad = coordinate("renewable energy", broad_decompose, run_specialist)
    print("broad split  :", broad["draft"])
    print("still uncovered after refinement:", broad["uncovered"])
    print("\nThe narrow split can never mention geothermal, however good the")
    print("specialists are. That is why the coordinator owns coverage.")
