"""1.3 Pass context to a subagent, with the metadata it needs.

Real scenario: the research system again. The searcher has finished and the
writer is next. The writer is a separate call to Claude with an empty history,
so it knows only what the coordinator puts in its prompt.

Send it "write the report" and you get a confident essay about nothing. Send
it the findings, the goal and the shape of the answer and you get a report
that cites the work that was actually done.

Run it:
    python ex_1_3_context_passing.py                     offline
    ANTHROPIC_API_KEY=sk-... python ex_1_3_context_passing.py    real calls
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, get_client, recorded, say

# What the searcher produced. Each claim keeps its source and date, because
# attribution cannot be rebuilt later from memory.
FINDINGS = [
    {"claim": "Streaming revenue grew 12.1% in 2025", "subtopic": "revenue",
     "source": "IFPI Global Music Report 2026", "published": "2026-03-01"},
    {"claim": "Session-musician bookings fell 8% over two years", "subtopic": "employment",
     "source": "Musicians Union survey", "published": "2026-01-15"},
]


# ---------------------------------------------------------------- START HERE
def write_subagent_prompt(goal, findings, output_shape):
    """Everything the writer will ever know has to fit inside this string."""
    return (
        "Goal: %s\n\n"
        "Findings you must write from, and nothing else:\n%s\n\n"
        "A complete answer: %s\n"
        "If the findings do not support a claim, say so rather than filling the gap."
        % (goal, json.dumps(findings, indent=2), output_shape)
    )


def run_writer(client, prompt):
    """A subagent is just another call to Claude. New call, empty history."""
    reply = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system="You write short research reports. Cite a source for every claim.",
        messages=[{"role": "user", "content": prompt}],   # no earlier turns exist
    )
    return "".join(b.text for b in reply.content if b.type == "text")


# ---------------------------------------------------------------- recorded replies
BARE = [recorded(say(
    "Music and technology have long been intertwined, and recent years have "
    "seen considerable change across the industry. Streaming continues to grow "
    "and artists face both opportunity and disruption."))]

BRIEFED = [recorded(say(
    "Revenue: streaming revenue grew 12.1% in 2025 (IFPI Global Music Report "
    "2026, published 2026-03-01).\n"
    "Employment: session-musician bookings fell 8% over two years (Musicians "
    "Union survey, 2026-01-15).\n"
    "Gap: nothing here covers live performance, so no claim is made about it."))]

if __name__ == "__main__":
    banner("1.3 passing context to a subagent")

    bare = run_writer(get_client(BARE), "Write the report.")
    print("PROMPT: 'Write the report.'")
    print(bare)
    print()
    print("Nothing in that paragraph came from the research. It could have been")
    print("written before any of it started.")
    print()

    prompt = write_subagent_prompt(
        goal="How is AI changing music production?",
        findings=FINDINGS,
        output_shape="one short section per subtopic, each claim citing its source and date, "
                     "then an explicit list of what the findings do not cover",
    )
    briefed = run_writer(get_client(BRIEFED), prompt)
    print("PROMPT: goal + findings + the shape of a complete answer")
    print(briefed)
    print()
    print("Same model, same system prompt. The difference is %d characters of"
          % (len(prompt) - len("Write the report.")))
    print("context that the coordinator chose to include.")
