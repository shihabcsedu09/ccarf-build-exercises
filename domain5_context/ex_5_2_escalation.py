"""5.2 Decide when a person has to take over.

Real scenario: the agent resolves 55% of cases at first contact against an 80%
target. It escalates straightforward damage claims and tries to handle policy
exceptions itself, which is the wrong way round.

Three triggers, and two things that look like triggers and are not.

Run it:
    python ex_5_2_escalation.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner


# ---------------------------------------------------------------- START HERE
def escalation_reason(message, policy_covers, attempts, sentiment,
                      self_reported_confidence):
    """Return why this goes to a person, or None to keep working.

    Note what is not consulted: sentiment, and the model's own confidence.
    Both are available and both are the wrong signal.
    """
    if message.get("asks_for_human"):
        # An explicit request outranks everything, including a case the agent
        # could obviously solve. Investigating first is still not doing what
        # was asked.
        return "the customer asked for a person"

    if not policy_covers:
        # Nobody delegated this decision to the agent. A competitor price match
        # when the policy only covers your own site is a decision, not a task.
        return "the policy does not cover this case"

    if attempts >= 2:
        # Stuck means the same thing failing twice, not a case that feels hard.
        return "two attempts have failed; hand over what was gathered"

    return None


def multi_match_rule(matches):
    """A lookup returning three John Smiths is not a decision to make alone."""
    if len(matches) > 1:
        return ("ask for one more identifier (email, phone or order number) "
                "before any account-specific action")
    return "proceed"


NOT_TRIGGERS = [
    ("the customer sounds angry",
     "sentiment is a feeling, not a case property. A calm customer asking for a "
     "policy exception still needs a human; a frustrated one with a routine "
     "return does not."),
    ("the model reports low confidence",
     "that number is the miscalibrated signal itself. It was confident enough "
     "to attempt the policy exception it should have escalated."),
]

CASES = [
    ("routine replacement, photo evidence, customer calm",
     dict(message={}, policy_covers=True, attempts=0, sentiment="neutral",
          self_reported_confidence=0.9)),
    ("'I want to speak to a human, do not try to fix this'",
     dict(message={"asks_for_human": True}, policy_covers=True, attempts=0,
          sentiment="neutral", self_reported_confidence=0.95)),
    ("competitor price match; policy silent on competitors",
     dict(message={}, policy_covers=False, attempts=0, sentiment="neutral",
          self_reported_confidence=0.8)),
    ("refund tool failed twice with the same error",
     dict(message={}, policy_covers=True, attempts=2, sentiment="neutral",
          self_reported_confidence=0.6)),
    ("'This is the third time I have explained this. Ridiculous.'",
     dict(message={}, policy_covers=True, attempts=0, sentiment="angry",
          self_reported_confidence=0.9)),
]

if __name__ == "__main__":
    banner("5.2 escalation triggers", api=False)
    for label, facts in CASES:
        reason = escalation_reason(**facts)
        print("%-52s %s" % (label[:50], reason or "keep working, resolve it"))
    print()
    print("the last one is the interesting case: acknowledge the frustration,")
    print("resolve the return now, and escalate only if they ask for a person.")
    print()
    print("what is deliberately not in the function:")
    for name, why in NOT_TRIGGERS:
        print("   %s" % name)
        print("      %s" % why)
    print()
    print("three matches for 'John Smith' ->", multi_match_rule(["a", "b", "c"]))
    print("one match                      ->", multi_match_rule(["a"]))
