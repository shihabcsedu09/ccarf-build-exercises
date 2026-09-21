"""3.2 Write a slash command and a skill, in the right place.

Real scenario: the team wants /review for everyone who clones the repo, and
one developer wants a private /standup nobody else maintains.

A command is a saved prompt. A skill is the richer form: a folder with a
SKILL.md and settings at the top. Where the file lives decides who gets it.

Three settings carry most of the marks. context: fork keeps a noisy skill out
of the main chat. allowed-tools decides what it can ever do. argument-hint
stops people running it empty.

This writes the real files, with real frontmatter.

Run it:
    python ex_3_2_commands_skills.py
"""
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner

# ---------------------------------------------------------------- START HERE
# Shared: committed, so every clone has it.
REVIEW_COMMAND = """---
description: Run the team's review checklist over the staged diff
allowed-tools: Bash(git diff:*), Read, Grep
argument-hint: [pull-request-number]
---
Review the staged changes for correctness, security and data loss.
Skip style; the linter owns that.

The diff:
!`git diff --staged`
"""

# Shared skill, with all three settings that matter, each fixing a real complaint.
MIGRATION_SKILL = """---
name: migration
description: Generate a database migration file from a short name
argument-hint: <migration-name>
context: fork
allowed-tools: Read, Write, Glob
---
Create a migration named $ARGUMENTS, following db/migrations/README.md.
Use the next free sequence number. Never modify an existing migration.
"""

# Private: home directory, not the repo. A different name, because a project
# skill of the same name wins and yours would silently never run.
STANDUP_COMMAND = """---
description: Draft my standup from yesterday's commits
allowed-tools: Bash(git log:*)
---
Summarise what I did yesterday in three bullets.
!`git log --author=@me --since=yesterday --oneline`
"""

# A subagent defined as a file. The tools line is the guarantee; a description
# that says "read-only" guarantees nothing.
EXPLORER_AGENT = """---
name: legacy-explorer
description: Maps an unfamiliar module and returns a summary
tools: Read, Grep, Glob
model: haiku
---
Locate entry points, data stores and scheduled jobs for the module named.
Return a structured summary: files, classes, dependencies, open questions.
"""


def frontmatter(text):
    """Read the settings block at the top of a command or skill file."""
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)[1]
    out = {}
    for line in block.strip().splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip()
    return out


def install(root):
    """Put each file where Claude Code actually looks for it."""
    (root / ".claude" / "commands").mkdir(parents=True)
    (root / ".claude" / "commands" / "review.md").write_text(REVIEW_COMMAND)
    (root / ".claude" / "skills" / "migration").mkdir(parents=True)
    (root / ".claude" / "skills" / "migration" / "SKILL.md").write_text(MIGRATION_SKILL)
    (root / ".claude" / "agents").mkdir(parents=True)
    (root / ".claude" / "agents" / "legacy-explorer.md").write_text(EXPLORER_AGENT)
    home = root / "home" / ".claude" / "commands"
    home.mkdir(parents=True)
    (home / "standup.md").write_text(STANDUP_COMMAND)


def available(root, include_home):
    """What a given person can type, which is the point of the scopes."""
    found = []
    for p in sorted((root / ".claude" / "commands").glob("*.md")):
        found.append(("/" + p.stem, "project", "shared, committed"))
    for p in sorted((root / ".claude" / "skills").glob("*/SKILL.md")):
        found.append(("/" + p.parent.name, "project skill", "shared, committed"))
    if include_home:
        for p in sorted((root / "home" / ".claude" / "commands").glob("*.md")):
            found.append(("/" + p.stem, "personal", "this machine only"))
    return found


if __name__ == "__main__":
    banner("3.2 commands, skills and where they live", api=False)
    root = pathlib.Path(tempfile.mkdtemp())
    install(root)

    print("files written:")
    for p in sorted(root.rglob("*.md")):
        print("   ", p.relative_to(root))
    print()

    print("what a teammate who cloned the repo can type:")
    for name, scope, note in available(root, include_home=False):
        print("   %-12s %-14s %s" % (name, scope, note))
    print()
    print("what the author can type, on their own machine:")
    for name, scope, note in available(root, include_home=True):
        print("   %-12s %-14s %s" % (name, scope, note))
    print()

    fm = frontmatter(MIGRATION_SKILL)
    print("the migration skill's settings, and the complaint each one answers:")
    print("   argument-hint: %-18s people ran it empty and got a placeholder file"
          % fm["argument-hint"])
    print("   context: %-23s its output was filling the main chat and"
          % fm["context"])
    print("   %-32s later answers drifted towards what it found" % "")
    print("   allowed-tools: %-18s it once ran a destructive cleanup; now it"
          % fm["allowed-tools"])
    print("   %-32s cannot run a shell command at all" % "")
    print()
    print("Only allowed-tools is a guarantee. The other two shape behaviour.")
    print()
    agent_fm = frontmatter(EXPLORER_AGENT)
    print("the subagent file: tools=%s  model=%s"
          % (agent_fm["tools"], agent_fm["model"]))
    print("   the tools line is why it cannot edit anything, whatever it is told.")
    shutil.rmtree(root, ignore_errors=True)
