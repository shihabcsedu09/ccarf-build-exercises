"""3.1 Build a multi-level CLAUDE.md configuration.

Three levels, all loaded together. They stack; none overrides another.
A rule only one person has is a rule in a personal file.

Run it:  python ex_3_1_claude_md_hierarchy.py
"""

USER_LEVEL    = "~/.claude/CLAUDE.md"      # you, in every repository
PROJECT_LEVEL = "./CLAUDE.md"              # the team, committed
LOCAL_LEVEL   = "./CLAUDE.local.md"        # you, this repository, gitignored
DIR_LEVEL     = "./packages/api/CLAUDE.md" # that area of the tree


# ---------------------------------------------------------------- START HERE
def loaded_for(machine, cwd):
    """What /memory would list for this person in this directory."""
    files = []
    if machine.get("user_file"):
        files.append(USER_LEVEL)
    if machine.get("cloned_repo"):
        files.append(PROJECT_LEVEL)
        if machine.get("local_file"):
            files.append(LOCAL_LEVEL)
        if cwd.startswith("packages/api"):
            files.append(DIR_LEVEL)
    return files


def who_sees(rule_location):
    return {
        USER_LEVEL:    "only you, but in every project you open",
        PROJECT_LEVEL: "everyone who clones the repository, and CI",
        LOCAL_LEVEL:   "only you, only in this repository",
        DIR_LEVEL:     "everyone, but only inside that directory",
    }[rule_location]


def diagnose(rule_location):
    """Why does one teammate behave differently?"""
    if rule_location == USER_LEVEL:
        return ("It is in a personal file that was never committed. "
                "Move it to " + PROJECT_LEVEL)
    return "Everyone gets it."


if __name__ == "__main__":
    veteran = {"user_file": True, "cloned_repo": True, "local_file": True}
    newcomer = {"user_file": False, "cloned_repo": True, "local_file": False}

    print("veteran, editing packages/api:")
    for f in loaded_for(veteran, "packages/api/src"):
        print("   ", f, "->", who_sees(f))
    print("newcomer, editing packages/api:")
    for f in loaded_for(newcomer, "packages/api/src"):
        print("   ", f, "->", who_sees(f))

    print("\nThe error-handling rule lives in", USER_LEVEL)
    print("  ", diagnose(USER_LEVEL))
    print("\nAdvice files ask. settings.json enforces. .local means only you.")
