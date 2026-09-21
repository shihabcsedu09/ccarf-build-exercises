"""3.4 Choose plan mode, direct execution, or phases with gates.

Ambiguity picks between the first two. Reversibility and approval
are what introduce the third.

Run it:  python ex_3_4_execution_mode.py
"""


# ---------------------------------------------------------------- START HERE
def choose_mode(approach_is_clear, reversible, approvals_needed):
    """The decision your colleagues scored 12% on."""
    if not reversible or approvals_needed > 1:
        return "phases with approval gates"
    if approach_is_clear:
        return "direct execution"
    return "plan mode, then direct execution"


PHASES = [
    ("design",  "the lead approves the plan"),
    ("dry run", "the lead reviews the diff of what WOULD change"),
    ("migrate", "runs only after that second approval"),
    ("verify",  "reconcile counts, then sign off"),
]

if __name__ == "__main__":
    tasks = [
        ("null check, clear stack trace",          True,  True,  0),
        ("logging migration, two viable designs",  False, True,  0),
        ("schema migration, cannot roll back",     True,  False, 2),
    ]
    for label, clear, reversible, approvals in tasks:
        print(f"{label:40} -> {choose_mode(clear, reversible, approvals)}")

    print("\nWhy the third one is not just 'plan mode':")
    for name, gate in PHASES:
        print(f"  {name:9} {gate}")
    print("\nA single approval at the start cannot cover a risk that only")
    print("appears at the cutover.")
