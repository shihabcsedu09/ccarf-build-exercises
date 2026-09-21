"""1.2 Build a hub-and-spoke research coordinator.

Real scenario: the research system from the exam. One coordinator, several
specialists. The coordinator splits the topic, sends each piece to a
specialist, collects what comes back and decides what happens next.

Each specialist is its own call to Claude with its own narrow prompt. They
never call each other, so everything a specialist knows arrived in the prompt
the coordinator wrote for it.

The lesson: when the report misses a whole area, the specialists did nothing
wrong. The coordinator never asked about that area.

Run it:
    python ex_1_2_coordinator.py                     offline, no key needed
    ANTHROPIC_API_KEY=sk-... python ex_1_2_coordinator.py    real API calls
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  # find claude_helpers
from claude_helpers import MODEL, banner, call, get_client, recorded, say

# The coordinator is forced to answer through this tool, so the split comes back
# as a list you can iterate, never as a paragraph you have to parse.
PLAN_TOOL = {
    "name": "submit_plan",
    "description": "Record the subtopics this research question must cover.",
    "input_schema": {
        "type": "object",
        "properties": {
            "subtopics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Every distinct area the question covers, not just the obvious ones.",
            }
        },
        "required": ["subtopics"],
    },
}

# Specialists return findings in a fixed shape so the coordinator can merge them
# and see which subtopic each claim belongs to.
FINDINGS_TOOL = {
    "name": "submit_findings",
    "description": "Record what you found for the one subtopic you were given.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "claim": {"type": "string"},
                        "source": {"type": "string"},
                        "published": {"type": "string", "description": "ISO date, or null"},
                    },
                    "required": ["claim", "source"],
                },
            }
        },
        "required": ["findings"],
    },
}


def forced_call(client, system, prompt, tool):
    """One Claude call that must answer through `tool`, returning the arguments.

    tool_choice pins the tool, so the reply cannot come back as prose that the
    next step would have to guess its way through.
    """
    reply = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": prompt}],
    )
    for block in reply.content:
        if block.type == "tool_use":
            return block.input
    raise RuntimeError("expected a tool call and got prose")


# ---------------------------------------------------------------- START HERE
def coordinate(client, topic, max_refinements=1):
    """Split the topic, send each piece out, then look for holes and fill them."""

    # Step 1. The coordinator decides the shape of the work. This call owns
    # coverage: whatever it leaves out, no specialist can put back.
    plan = forced_call(
        client,
        system=("You plan research. List every distinct area the question covers, "
                "including ones that are easy to forget. Breadth matters more "
                "than depth here."),
        prompt="Research question: %s" % topic,
        tool=PLAN_TOOL,
    )
    subtopics = plan["subtopics"]

    # Step 2. One call per subtopic. Each specialist sees only its own brief,
    # so the brief has to carry everything: the goal and what a good answer holds.
    findings = []
    for subtopic in subtopics:
        result = forced_call(
            client,
            system=("You research one subtopic and report findings. Every claim "
                    "carries its source and the date it was published. If you "
                    "find nothing, return an empty list rather than guessing."),
            prompt=("Overall question: %s\nYour subtopic, and only this one: %s"
                    % (topic, subtopic)),
            tool=FINDINGS_TOOL,
        )
        for item in result["findings"]:
            item["subtopic"] = subtopic          # keep the link back to the split
        findings.extend(result["findings"])

    # Step 3. The coordinator checks its own work before writing anything.
    # A subtopic it asked for but got nothing on is a hole worth another pass.
    for _ in range(max_refinements):
        covered = set(f["subtopic"] for f in findings)
        gaps = [s for s in subtopics if s not in covered]
        if not gaps:
            break
        for gap in gaps:                          # re-ask only about the holes
            result = forced_call(
                client,
                system="You research one subtopic. Try sources the first pass may have missed.",
                prompt="Overall question: %s\nSubtopic that returned nothing: %s" % (topic, gap),
                tool=FINDINGS_TOOL,
            )
            for item in result["findings"]:
                item["subtopic"] = gap
            findings.extend(result["findings"])

    covered = set(f["subtopic"] for f in findings)
    return {
        "subtopics": subtopics,
        "findings": findings,
        "uncovered": [s for s in subtopics if s not in covered],
    }


# ---------------------------------------------------------------- recorded replies
def plan_reply(*subtopics):
    return recorded(call("toolu_plan", "submit_plan", subtopics=list(subtopics)))


def findings_reply(subtopic, count=1):
    items = [{"claim": "a dated finding about %s" % subtopic,
              "source": "https://example.org/%s" % subtopic,
              "published": "2026-03-01"} for _ in range(count)]
    return recorded(call("toolu_find", "submit_findings", findings=items))


# A narrow split: the coordinator only thought of the two obvious areas.
NARROW = [plan_reply("solar", "wind"),
          findings_reply("solar"), findings_reply("wind")]

# A broad split: six areas, and one of them comes back empty on the first pass.
BROAD = [plan_reply("solar", "wind", "geothermal", "tidal", "biomass", "grid storage"),
         findings_reply("solar"), findings_reply("wind"), findings_reply("geothermal"),
         findings_reply("tidal", count=0), findings_reply("biomass"),
         findings_reply("grid storage"),
         findings_reply("tidal")]          # the follow-up pass finds it

if __name__ == "__main__":
    banner("1.2 hub-and-spoke coordinator")
    topic = "How is renewable energy changing electricity prices?"

    narrow = coordinate(get_client(NARROW), topic)
    print("narrow split  :", narrow["subtopics"])
    print("  areas covered:", sorted(set(f["subtopic"] for f in narrow["findings"])))
    print("  geothermal and tidal are missing, and no specialist could have added")
    print("  them, because nobody was ever asked about them.")
    print()

    broad = coordinate(get_client(BROAD), topic)
    print("broad split   :", broad["subtopics"])
    print("  findings     :", len(broad["findings"]), "across",
          len(set(f["subtopic"] for f in broad["findings"])), "areas")
    print("  still uncovered after the follow-up pass:", broad["uncovered"] or "none")
    print()
    print("Same specialists, same prompts, both times. The only thing that")
    print("changed is what the coordinator asked for in step 1.")
