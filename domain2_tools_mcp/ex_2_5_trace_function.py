"""2.5 Trace a deprecated function with the built-in tools.

Grep looks inside files. Glob matches names. Follow the export chain
until no new names appear.

Run it:  python ex_2_5_trace_function.py
"""
import fnmatch, re

# A tiny fake repository: path -> contents
REPO = {
    "src/legacy/orders.ts":   "export function processLegacyOrder(o) { return o }",
    "src/legacy/index.ts":    ("export { processLegacyOrder as submitOrder }"
                               " from './orders'"),
    "src/checkout/submit.ts": ("import { submitOrder } from '../legacy'"
                               "\nsubmitOrder(cart)"),
    "src/billing/recon.ts":   ("import { processLegacyOrder } from "
                               "'../legacy/orders'\nprocessLegacyOrder(x)"),
    "src/checkout/submit.test.ts": "it('submits', () => { /* via the module */ })",
    "docs/legacy.md":         "processLegacyOrder is deprecated",
}


def grep(pattern, glob="**/*"):
    """Search file CONTENTS. This is what 'who calls this' means."""
    return {p: [l for l in c.splitlines() if re.search(pattern, l)]
            for p, c in REPO.items()
            if fnmatch.fnmatch(p, glob) and re.search(pattern, c)}


def glob_files(pattern):
    """Match file PATHS by name. A function name is rarely in a path."""
    return [p for p in REPO if fnmatch.fnmatch(p, pattern)]


# ---------------------------------------------------------------- START HERE
def trace(symbol):
    """Grep for the name, learn any aliases from the export chain, repeat."""
    names, seen, callers = [symbol], set(), {}
    while names:
        name = names.pop()
        if name in seen:
            continue
        seen.add(name)
        for path, lines in grep(rf"\b{name}\b", "src/*/*.ts").items():
            callers.setdefault(path, []).extend(lines)
            for line in lines:
                alias = re.search(rf"{name} as (\w+)", line)
                if alias:
                    names.append(alias.group(1))       # a second name to search for
    return seen, callers


if __name__ == "__main__":
    print("Glob for the function name:",
          glob_files("**/*processLegacyOrder*") or "nothing")
    print("  a function name is not a file name, which is why Glob finds nothing\n")

    names, callers = trace("processLegacyOrder")
    print("names discovered:", sorted(names))
    for path, lines in sorted(callers.items()):
        print(f"  {path}")
        for l in lines:
            print(f"      {l.strip()}")

    print("\nTests by naming convention, which never mention the symbol:")
    for p in glob_files("src/**/*.test.ts"):
        print("  ", p)
