"""3.2 Create custom commands and skills.

Repository for the team, home folder for you. A personal variant of a
team command needs a different name, or it shadows theirs.

Run it:  python ex_3_2_commands_skills.py
"""

SKILL_FRONTMATTER = {
    "name": "case-review",
    "description": "Investigate one support case and summarise the findings",
    "argument-hint": "[case-id]",      # shown when someone types the command
    "context": "fork",                 # noise stays out of the main conversation
    "allowed-tools": "Read, Grep, Glob",   # lists what it may use, and pre-approves
}


# ---------------------------------------------------------------- START HERE
def where(is_shared_with_team, is_skill):
    """Decide the path from two questions."""
    base = ".claude" if is_shared_with_team else "~/.claude"
    return f"{base}/skills/<name>/SKILL.md" if is_skill else f"{base}/commands/<name>.md"


def shadows_team_command(personal_name, team_names):
    """A same-named personal copy silently replaces the team's."""
    return personal_name in team_names


def explain(setting):
    return {
        "context: fork":   "runs in its own context, so pages of output never "
                           "reach the main conversation",
        "allowed-tools":   "lists what the skill may use and pre-approves it, so "
                           "it does not stop for a prompt on every file",
        "argument-hint":   "shows the expected argument at invocation, which is "
                           "why it stops being run bare",
        "disallowed-tools":"removes the named tools while the skill is active; use "
                           "this when the requirement is 'must not be able to'",
    }[setting]


if __name__ == "__main__":
    print("team /release-notes  ->", where(True,  False))
    print("your /my-standup     ->", where(False, False))
    print("team case-review     ->", where(True,  True))

    team = ["release-notes", "commit"]
    for name in ("commit", "my-commit"):
        print(f"\npersonal '{name}' shadows the team's: {shadows_team_command(name, team)}")

    print("\nfrontmatter:")
    for k, v in SKILL_FRONTMATTER.items():
        print(f"  {k}: {v}")
    print()
    for s in ("context: fork", "allowed-tools", "argument-hint", "disallowed-tools"):
        print(f"  {s:18} {explain(s)}")
