"""2.5 Trace a deprecated function with the built-in tools.

Real scenario: parseConfig is deprecated and you need every caller across a
monorepo. It is re-exported twice under different names, so one search is
never enough.

Grep looks inside files. Glob matches names. Read opens one file. Edit
changes one snippet and refuses when that snippet is not unique.

This builds a small real repository in a temp folder and runs the trace on it,
so the counts below are real.

Run it:
    python ex_2_5_trace_function.py
"""
import pathlib
import re
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner

REPO = {
    "src/config/parse.ts":      "export function parseConfig(raw: string) { return JSON.parse(raw); }\n",
    "src/config/index.ts":      "import { parseConfig } from './parse';\nexport { parseConfig as loadConfig };\n",
    "src/server/boot.ts":       "import { loadConfig } from '../config';\nconst cfg = loadConfig(text);\n",
    "src/jobs/nightly.ts":      "import { parseConfig } from '../config/parse';\nparseConfig(raw);\n",
    "src/legacy/shim.ts":       "export { loadConfig as readSettings } from '../config';\n",
    "src/legacy/old_boot.ts":   "import { readSettings } from './shim';\nreadSettings(text);\n",
    "src/config/parse.test.ts": "import { parseConfig } from './parse';\ntest('parses', () => parseConfig('{}'));\n",
    "docs/config.md":           "The parseConfig helper is deprecated.\n",
}


def build_repo():
    root = pathlib.Path(tempfile.mkdtemp())
    for path, text in REPO.items():
        p = root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


# ---------------------------------------------------------------- START HERE
def grep(root, pattern, glob="**/*.ts"):
    """What the Grep tool does: search file CONTENTS, return the hits."""
    hits = []
    for path in sorted(root.glob(glob)):
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if re.search(pattern, line):
                hits.append((str(path.relative_to(root)), n, line.strip()))
    return hits


def glob_files(root, pattern):
    """What the Glob tool does: match file NAMES, look at no contents at all."""
    return sorted(str(p.relative_to(root)) for p in root.glob(pattern))


def read(root, path):
    """What the Read tool does: open one file you already decided matters."""
    return (root / path).read_text()


def trace(root, symbol):
    """Grep for the name, Read what it exports, Grep again for the new names.

    One search is not enough, because each re-export renames the thing.
    """
    steps = []
    seen_names = [symbol]
    callers = []
    i = 0
    while i < len(seen_names):
        name = seen_names[i]
        i += 1
        hits = grep(root, r"\b%s\b" % re.escape(name))
        steps.append(("Grep", name, len(hits)))
        for path, line_no, line in hits:
            # An export line renames it: follow the new name too.
            m = re.search(r"as (\w+)", line)
            if m and m.group(1) not in seen_names:
                seen_names.append(m.group(1))
                steps.append(("Read", path, "found alias %s" % m.group(1)))
            elif "import" not in line and "export" not in line:
                callers.append((path, line_no, line))
    return steps, callers, seen_names


if __name__ == "__main__":
    banner("2.5 tracing with Grep, Glob and Read", api=False)
    root = build_repo()
    print("repository: %d files" % len(REPO))
    print()

    print("Glob finds files by NAME. Useful for 'where are the tests?':")
    for f in glob_files(root, "**/*.test.ts"):
        print("   ", f)
    print()

    print("Glob for the symbol name finds almost nothing, because the name")
    print("lives inside files, not in their filenames:")
    print("   ", glob_files(root, "**/*parseConfig*") or "no matches")
    print()

    steps, callers, names = trace(root, "parseConfig")
    print("Grep, then Read, then Grep again:")
    for step in steps:
        print("   ", " ".join(str(s) for s in step))
    print()
    print("names this symbol travels under:", names)
    print("real call sites:")
    for path, line_no, line in callers:
        print("   %-24s line %-3d %s" % (path, line_no, line))
    print()
    print("Stopping after the first Grep would have missed %d of %d call sites."
          % (len([c for c in callers if "parseConfig" not in c[2]]), len(callers)))
    print()
    print("When Edit fails because the snippet appears six times, the keyed")
    print("answer is Read the whole file, then Write it back with the one")
    print("change. Not replace_all, and not rewriting the code to suit the tool.")
    shutil.rmtree(root, ignore_errors=True)
