"""3.1 Stack CLAUDE.md, and enforce what must hold.

Real scenario: three developers say Claude follows "always add comprehensive
error handling". A fourth, who just cloned the repo, says it does not. Same
branch, same code.

Memory files stack: the home file, the project file and any folder files all
load together, and nothing overrides anything. So a rule sitting in somebody's
home file is invisible to everyone else.

Settings files are different. They override, and they enforce. Anything that
must hold whatever a developer types belongs there, not in prose.

This writes the real files so you can see both behaviours.

Run it:
    python ex_3_1_claude_md_hierarchy.py
"""
import json
import pathlib
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner

HOME_MD = """# My preferences
Always add comprehensive error handling.
Prefer named exports.
"""

PROJECT_MD = """# Orders API
## Commands
- Test: `npm test`
- Lint: `npm run lint`
## Conventions
- Services own their tables. Never query another service's table directly.
@./standards/testing.md
"""

SUBDIR_MD = """# Payments
Every amount is an integer number of cents. Never a float.
"""

IMPORTED_MD = "Tests use Vitest. One describe block per component.\n"

# The rules that must hold. Not prose: a deny list the model cannot talk past.
SETTINGS = {
    "permissions": {
        "allow": ["Bash(npm run test:*)", "Bash(git diff:*)", "Read(src/**)"],
        "deny": ["Bash(rm -rf*)", "Bash(git push --force*)", "Edit(src/payments/**)"],
    }
}


# ---------------------------------------------------------------- START HERE
def loaded_for(root, working_file, include_home):
    """Which memory files apply when Claude touches `working_file`.

    They stack, broad to specific. The home file is the one a teammate does
    not have, which is the whole bug in the scenario above.
    """
    files = []
    if include_home:
        files.append(("home", root / "home" / ".claude" / "CLAUDE.md"))
    files.append(("project", root / "CLAUDE.md"))
    folder = (root / working_file).parent
    while folder != root and folder != folder.parent:
        candidate = folder / "CLAUDE.md"
        if candidate.exists():
            files.append(("folder", candidate))
        folder = folder.parent
    return [(scope, p) for scope, p in files if p.exists()]


def resolve_imports(path, root, depth=0):
    """An @path line inlines that file. It tidies the source; it does not
    shrink the context, because the text still loads."""
    text = path.read_text()
    out = []
    for line in text.splitlines():
        if line.startswith("@") and depth < 5:
            target = (path.parent / line[1:]).resolve()
            if target.exists():
                out.append("<<inlined from %s>>" % line[1:])
                out.extend(resolve_imports(target, root, depth + 1).splitlines())
                continue
        out.append(line)
    return "\n".join(out)


def blocked_by_settings(settings, action):
    """Deny beats allow. This is the part a prompt cannot do."""
    for rule in settings["permissions"]["deny"]:
        head = rule.split("(")[0]
        inner = rule[len(head) + 1:-1].rstrip("*")
        if action.startswith(head) and inner.strip("*") in action:
            return rule
    return None


def build(root):
    (root / "home" / ".claude").mkdir(parents=True)
    (root / "home" / ".claude" / "CLAUDE.md").write_text(HOME_MD)
    (root / "CLAUDE.md").write_text(PROJECT_MD)
    (root / "standards").mkdir()
    (root / "standards" / "testing.md").write_text(IMPORTED_MD)
    (root / "src" / "payments").mkdir(parents=True)
    (root / "src" / "payments" / "CLAUDE.md").write_text(SUBDIR_MD)
    (root / "src" / "payments" / "refund.ts").write_text("// ...\n")
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text(json.dumps(SETTINGS, indent=2))


if __name__ == "__main__":
    banner("3.1 memory files stack, settings enforce", api=False)
    root = pathlib.Path(tempfile.mkdtemp())
    build(root)

    print("the developer who wrote the rule in their home file:")
    for scope, p in loaded_for(root, "src/payments/refund.ts", include_home=True):
        print("   %-8s %s" % (scope, p.relative_to(root)))
    print()
    print("the teammate who just cloned the repo:")
    for scope, p in loaded_for(root, "src/payments/refund.ts", include_home=False):
        print("   %-8s %s" % (scope, p.relative_to(root)))
    print()
    print("Same branch, same files on disk. The error-handling rule is only in")
    print("the first list, which is why one of them sees it and the other does not.")
    print("Fix: move it into the project CLAUDE.md, where a clone picks it up.")
    print()

    print("@./standards/testing.md inlines at load time:")
    for line in resolve_imports(root / "CLAUDE.md", root).splitlines()[-4:]:
        print("   ", line)
    print()

    print("what a deny rule does that a sentence cannot:")
    for action in ["Bash(npm run test)", "Bash(git push --force origin main)",
                   "Edit(src/payments/refund.ts)", "Read(src/orders/index.ts)"]:
        rule = blocked_by_settings(SETTINGS, action)
        print("   %-34s %s" % (action, ("BLOCKED by %s" % rule) if rule else "allowed"))
    print()
    print("Put advice in CLAUDE.md. Put the rules that must hold in settings.")
    shutil.rmtree(root, ignore_errors=True)
