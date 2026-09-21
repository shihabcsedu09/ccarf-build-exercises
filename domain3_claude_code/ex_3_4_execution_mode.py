"""3.4 Choose direct execution, plan mode, or phases with gates.

This is the objective thirteen colleagues scored worst on: seven of eight got
it wrong. The same people scored full marks on plain "plan or direct", so the
gap is the third option and what decides it.

Ambiguity chooses between the first two. Risk and approval bring in the third.

  reversible and clear            -> direct
  genuinely uncertain approach    -> plan once, then execute
  cannot be undone, or somebody
  must sign off more than once    -> phases, with a gate between each

Run it:
    python ex_3_4_execution_mode.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner


# ---------------------------------------------------------------- START HERE
def choose(reversible, approach_clear, approvals_needed):
    """Three questions, asked in this order. Scope is not one of them."""
    if approvals_needed > 1 or not reversible:
        # A single approval at the start cannot cover risk that shows up at
        # the cutover, so the gates go between the phases.
        return "multi-phase"
    if not approach_clear:
        return "plan"
    return "direct"


def commands_for(mode, task):
    """The actual command lines, which is what the question is really about."""
    if mode == "direct":
        return ["claude -p %r" % task]
    if mode == "plan":
        return ["claude --permission-mode plan      # explore and propose, change nothing",
                "# read the plan, approve it, then:",
                "claude -p %r" % task]
    return [
        "claude -p 'Phase 1: design it. Write PLAN.md. Run nothing.'",
        "#   -> a person reads PLAN.md and approves",
        "claude -p 'Phase 2: dry run against a copy. Report the numbers.'",
        "#   -> approved again, now with the numbers in hand",
        "claude -p 'Phase 3: apply it, then verify against Phase 2.'",
    ]


CASES = [
    ("Null check in one function, clear stack trace",
     dict(reversible=True, approach_clear=True, approvals_needed=0)),
    ("Rename a symbol across 40 files, mechanical",
     dict(reversible=True, approach_clear=True, approvals_needed=0)),
    ("Add Slack notifications; webhooks, bot token or app all viable",
     dict(reversible=True, approach_clear=False, approvals_needed=0)),
    ("Split the monolith; service boundaries still undecided",
     dict(reversible=True, approach_clear=False, approvals_needed=0)),
    ("Migrate the orders table; data-protection lead signs off twice",
     dict(reversible=False, approach_clear=True, approvals_needed=2)),
    ("Delete three years of archived records",
     dict(reversible=False, approach_clear=True, approvals_needed=1)),
]

# Discovery is a context decision, not an architecture one. It can appear
# alongside any of the three.
DISCOVERY_NOTE = (
    "Phase 1 will list hundreds of call sites. Hand that to an Explore "
    "subagent so the main conversation keeps its budget for the design.")

if __name__ == "__main__":
    banner("3.4 direct, plan, or phases with gates", api=False)
    print("%-52s %s" % ("task", "mode"))
    print("-" * 70)
    for task, facts in CASES:
        print("%-52s %s" % (task[:50], choose(**facts)))
    print()

    for task, facts in CASES[:1] + CASES[2:3] + CASES[4:5]:
        mode = choose(**facts)
        print("%s  ->  %s" % (task[:48], mode))
        for line in commands_for(mode, task):
            print("     ", line)
        print()

    print("Notice what did not decide anything: how many files it touches.")
    print("A 40-file rename is direct work. A one-file change with two")
    print("defensible designs deserves a plan.")
    print()
    print(DISCOVERY_NOTE)
