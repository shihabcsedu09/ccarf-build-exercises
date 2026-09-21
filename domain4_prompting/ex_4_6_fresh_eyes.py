"""4.6 Review with an instance that never saw the reasoning.

Real scenario: Claude writes a change, and asked to review it, approves it.
The trace shows it considered the edge case during generation and decided its
approach was fine. Asked again, it reaches the same conclusion, because the
same justification is still in front of it.

A second call with none of that history finds the bug, the way a colleague
does.

Run it:
    python ex_4_6_fresh_eyes.py                     offline
    ANTHROPIC_API_KEY=sk-... python ex_4_6_fresh_eyes.py    real calls
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, get_client, recorded, say

REVIEW_CRITERIA = """Report correctness, security and data-loss defects only.
Skip style and naming. For each finding give the line and what goes wrong.
If the code is correct, say so in one line."""

CODE = '''def apply_discount(total, percent):
    # percent is always 0-100 here
    return total - (total * percent / 100)
'''


# ---------------------------------------------------------------- START HERE
def self_review(client, generation_history):
    """The trap. The reviewer inherits every justification the author made."""
    messages = list(generation_history) + [
        {"role": "user", "content": "Now review what you wrote for bugs."}]
    reply = client.messages.create(model=MODEL, max_tokens=600, messages=messages)
    return "".join(b.text for b in reply.content if b.type == "text")


def independent_review(client, code, criteria, existing_tests=""):
    """A new call. It gets the code and the standard, and nothing else.

    No generation history, so there is nothing to defend. Give it the tests
    and any previous findings so it does not repeat what is already known.
    """
    content = "Review this code:\n\n%s" % code
    if existing_tests:
        content += "\n\nExisting tests:\n%s" % existing_tests
    reply = client.messages.create(
        model=MODEL, max_tokens=600,
        system=criteria,                       # the standard, not the story
        messages=[{"role": "user", "content": content}])
    return "".join(b.text for b in reply.content if b.type == "text")


WHAT_THE_REVIEWER_GETS = [
    ("the code or output, as it stands", True),
    ("the requirements and the review standard", True),
    ("existing tests and previous findings", True),
    ("the author's reasoning or justifications", False),
    ("the conversation that produced the code", False),
]

# Three passes with a vote is not the same thing. It only keeps findings that
# recur, and a subtle bug that one pass happens to notice is dropped as noise.
VOTING_WARNING = (
    "Running three passes and keeping findings that appear twice deletes the "
    "rare real bug, which is the one you most wanted.")

# ---------------------------------------------------------------- recorded replies
GENERATION_HISTORY = [
    {"role": "user", "content": "Write apply_discount."},
    {"role": "assistant", "content":
        "Here it is. I considered negative percentages and concluded the "
        "caller guarantees 0-100, so a guard would be dead code."},
]

SELF = [recorded(say("Looks correct. The comment documents the precondition, "
                     "and the caller guarantees the range, so no guard is needed."))]
INDEPENDENT = [recorded(say(
    "line 3: percent is not validated. A percent above 100 returns a negative "
    "total, and a negative percent increases the charge. The comment asserts a "
    "precondition that nothing enforces."))]

if __name__ == "__main__":
    banner("4.6 fresh eyes")
    print("the code:")
    print(CODE)

    print("same session, asked to review its own work:")
    print("  ", self_review(get_client(SELF), GENERATION_HISTORY))
    print()
    print("a new call, given the code and the standard only:")
    print("  ", independent_review(get_client(INDEPENDENT), CODE, REVIEW_CRITERIA))
    print()
    print("what the reviewer should and should not receive:")
    for item, give in WHAT_THE_REVIEWER_GETS:
        print("   %-44s %s" % (item, "give it" if give else "never"))
    print()
    print(VOTING_WARNING)
    print()
    print("In Claude Code this is two processes, not one conversation:")
    print("   claude -p 'implement the change'")
    print("   claude -p 'review the diff against the standards in CLAUDE.md'")
