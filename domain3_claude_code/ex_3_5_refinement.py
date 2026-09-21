"""3.5 Refine by showing, not by describing again.

Real scenario: you have described the transformation twice and Claude has
interpreted it differently both times. A third paragraph will not help.

Feedback has a ladder. A failing test is the top rung, because it is exact and
machine-checked. A description of the problem is the bottom rung, because
Claude has to guess what you meant before it can fix anything.

Run it:
    python ex_3_5_refinement.py                     offline
    ANTHROPIC_API_KEY=sk-... python ex_3_5_refinement.py    real calls
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, get_client, recorded, say

LADDER = [
    ("a failing test", "exact, machine-checked, and the fix is verifiable"),
    ("the real error text", "pasted whole, with the stack trace, not paraphrased"),
    ("a concrete counter-example", "'for input X it returns 3, it should be 4'"),
    ("a description", "'the parsing seems off' — now Claude guesses first"),
]


# ---------------------------------------------------------------- START HERE
def describe_again(client, requirement):
    """Round three of prose. Same ambiguity, same medium, same result."""
    return ask(client, requirement)


def show_examples(client, pairs):
    """Two or three input-output pairs remove the ambiguity that prose carries."""
    shown = "\n".join("in:  %s\nout: %s" % (a, b) for a, b in pairs)
    return ask(client, "Write the transform. These are the cases:\n" + shown +
                       "\nWrite the tests first, then the implementation.")


def paste_the_failure(client, test_output):
    """The strongest rung: hand back exactly what the runner printed."""
    return ask(client, "The suite fails:\n" + test_output +
                       "\nFix only what this failure shows.")


def interview_first(client, task):
    """For unfamiliar ground: make Claude ask before it builds, so the
    requirement you did not know to state comes out first."""
    return ask(client, "Before writing any code for: %s\nAsk me about "
                       "invalidation, staleness and what happens when it is "
                       "unavailable. Do not propose code yet." % task)


def bundle_interacting(client, issues):
    """Fixes that interact go in one message. Sent one at a time, each fix
    undoes the last."""
    listed = "\n".join("- " + i for i in issues)
    return ask(client, "These interact; fix them together so one fix does not "
                       "undo another:\n" + listed)


def ask(client, prompt):
    reply = client.messages.create(
        model=MODEL, max_tokens=800,
        system="You are pair-programming. Be concrete.",
        messages=[{"role": "user", "content": prompt}])
    return "".join(b.text for b in reply.content if b.type == "text")


# ---------------------------------------------------------------- recorded replies
SCRIPT = [
    recorded(say("I have normalised the fields and formatted the timestamps "
                 "as ISO strings where they were present.")),
    recorded(say("tests: handles epoch seconds, handles null created.\n"
                 "then: def normalise(r): return {'createdAt': iso(r['created']), "
                 "'amount': float(r['amt'].replace(',', ''))}")),
    recorded(say("The null branch returned the epoch instead of None. Fixed "
                 "that one line; the other six tests are untouched.")),
    recorded(say("Three questions: how is the cache invalidated on a permission "
                 "change, how stale may a read be, and what should happen when "
                 "the cache is down?")),
    recorded(say("Fixed together: the cursor now encodes the sort order, and "
                 "both code paths read the same default.")),
]

if __name__ == "__main__":
    banner("3.5 iterative refinement")
    client = get_client(SCRIPT)

    print("the feedback ladder, strongest first:")
    for rung, why in LADDER:
        print("   %-28s %s" % (rung, why))
    print()

    print("1. describing it a third time:")
    print("  ", describe_again(client, "Normalise the API response.")[:150])
    print("   still prose, still open to interpretation.")
    print()

    print("2. showing two input-output pairs:")
    out = show_examples(client, [
        ('{"created": 1741046400, "amt": "47.90"}', '{"createdAt": "2026-03-04", "amount": 47.9}'),
        ('{"created": null, "amt": "0"}', '{"createdAt": null, "amount": 0}')])
    print("  ", out[:150])
    print()

    print("3. pasting the actual failure:")
    print("  ", paste_the_failure(client,
          "FAIL normalise > handles null created\n  expected: None\n  received: '1970-01-01'")[:150])
    print()

    print("4. interviewing first, on unfamiliar ground:")
    print("  ", interview_first(client, "add a caching layer")[:150])
    print()

    print("5. bundling fixes that interact:")
    print("  ", bundle_interacting(client, [
        "cursor encoding breaks when the sort order changes",
        "the two code paths default the sort order differently"])[:150])
    print()
    print("Independent fixes can go one at a time. Interacting ones cannot.")
