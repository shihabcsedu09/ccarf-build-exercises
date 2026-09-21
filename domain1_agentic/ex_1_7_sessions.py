"""1.7 Implement session management strategies.

Resume when little changed. Start fresh when most of it moved on.
Fork to compare two ideas from one baseline.

Run it:  python ex_1_7_sessions.py
"""


# ---------------------------------------------------------------- START HERE
def choose(total_files, changed_files, comparing_two_designs=False):
    """The decision the exam asks for, in one function."""
    if comparing_two_designs:
        return "fork"
    if not changed_files:
        return "resume"
    if len(changed_files) / total_files > 0.4:
        return "fresh"
    return "resume_and_name_the_changed_files"


def resume_prompt(changed):
    head = ("These files changed since this session was saved. Re-read\n"
            "them before using anything you remember about them:")
    return head + "\n" + "\n".join(f"  - {p}" for p in changed)


def fresh_prompt(findings, still_valid, now_stale):
    return (f"Earlier investigation found:\n{findings}\n\n"
            f"Still valid: {still_valid}\n"
            f"Changed since, so re-read: {now_stale}")


if __name__ == "__main__":
    cases = [
        ("3 of 50 files changed", 50, ["a.py", "b.py", "c.py"], False),
        ("30 of 50 refactored",   50, [f"f{i}.py" for i in range(30)], False),
        ("nothing changed",       50, [], False),
        ("compare two designs",   50, [], True),
    ]
    for label, total, changed, comparing in cases:
        print(f"{label:24} -> {choose(total, changed, comparing)}")

    print("\n" + resume_prompt(["a.py", "b.py", "c.py"]))
    print("\nA fork copies the stale file contents into both branches, so it is")
    print("for comparing ideas, never for escaping stale context.")
