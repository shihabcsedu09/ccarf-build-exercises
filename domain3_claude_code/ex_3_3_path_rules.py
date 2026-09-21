"""3.3 Scope rules to file paths with a glob.

Real scenario: tests sit next to the code they test, in fifty directories.
The team wants one set of test conventions to apply wherever a test file is,
and a 1,100-line memory file is loading Terraform guidance into every session.

A rules file with a paths glob loads only when Claude touches a matching file.
One file, one pattern, and it keeps working as the tree changes.

Run it:
    python ex_3_3_path_rules.py
"""
import fnmatch
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner

# ---------------------------------------------------------------- START HERE
RULES = {
    # No paths line: loads every session, like a section of CLAUDE.md.
    "style.md": ("", "Prefer named exports. Keep functions under 40 lines."),

    # Follows the FILE TYPE, wherever in the tree it lives. This is the one
    # that replaces fifty per-directory memory files.
    "testing.md": ('paths:\n  - "**/*.test.tsx"\n  - "**/*.spec.ts"',
                   "Tests use Vitest. One describe per component. Never mock the "
                   "module under test."),

    # Follows an AREA. Right when the convention belongs to a folder.
    "api-conventions.md": ('paths:\n  - "src/api/**"',
                           "Handlers stay thin. All database access goes through a service."),

    # 300 lines that used to sit in the root memory file and loaded for everyone.
    "terraform.md": ('paths:\n  - "**/*.tf"',
                     "Pin provider versions. State lives in the shared backend."),
}

TREE = [
    "src/components/Button.tsx",
    "src/components/Button.test.tsx",
    "src/api/orders.ts",
    "src/api/orders.spec.ts",
    "infra/prod/main.tf",
    "docs/readme.md",
]


def write_rules(root):
    d = root / ".claude" / "rules"
    d.mkdir(parents=True)
    for name, (paths_block, body) in RULES.items():
        front = "---\n%s\n---\n" % paths_block if paths_block else "---\n---\n"
        (d / name).write_text(front + body + "\n")
    return d


def globs_of(rule_text):
    """Read the paths list out of the frontmatter."""
    if "paths:" not in rule_text:
        return []
    block = rule_text.split("---")[1]
    return [line.split("- ")[1].strip().strip('"')
            for line in block.splitlines() if line.strip().startswith("- ")]


def rules_for(rules_dir, working_file):
    """Which rule files load when Claude touches this path."""
    loaded = []
    for path in sorted(rules_dir.glob("*.md")):
        patterns = globs_of(path.read_text())
        if not patterns:
            loaded.append((path.name, "always"))
        elif any(fnmatch.fnmatch(working_file, p) for p in patterns):
            loaded.append((path.name, "matched"))
    return loaded


if __name__ == "__main__":
    banner("3.3 path-scoped rules", api=False)
    root = pathlib.Path(tempfile.mkdtemp())
    rules_dir = write_rules(root)

    print("rule files:", ", ".join(sorted(RULES)))
    print()
    for f in TREE:
        loaded = rules_for(rules_dir, f)
        print("%-34s %s" % (f, ", ".join("%s (%s)" % r for r in loaded)))
    print()
    print("Button.test.tsx and orders.spec.ts sit in different folders and still")
    print("get the same testing rules, because the glob follows the file type.")
    print("Per-directory memory files could not do that without a copy in every")
    print("folder, and a new folder would silently miss it.")
    print()
    print("Terraform guidance loaded for 1 of %d files instead of all of them."
          % len(TREE))
    shutil.rmtree(root, ignore_errors=True)
