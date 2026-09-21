#!/usr/bin/env python3
"""Run every exercise and report which ones printed their demo cleanly.

    python run_all.py            # run all thirty
    python run_all.py 3          # run domain 3 only
    python run_all.py 3.4        # run one exercise

Without ANTHROPIC_API_KEY every exercise replays a recorded reply, so this
runs offline, free and identically every time. Set the key and the same
files make real calls. Needs the anthropic package either way.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent
DOMAINS = {"1": "domain1_agentic", "2": "domain2_tools_mcp",
           "3": "domain3_claude_code", "4": "domain4_prompting",
           "5": "domain5_context"}


def files(selector=None):
    out = []
    for d, folder in sorted(DOMAINS.items()):
        for path in sorted((ROOT / folder).glob("ex_*.py")):
            num = ".".join(path.name.split("_")[1:3])
            if selector and not num.startswith(selector.rstrip(".")):
                continue
            out.append((num, path))
    return out


def main():
    selector = sys.argv[1] if len(sys.argv) > 1 else None
    chosen = files(selector)
    if not chosen:
        print(f"nothing matches {selector!r}")
        return 1
    failed = []
    for num, path in chosen:
        r = subprocess.run([sys.executable, str(path)], capture_output=True,
                           text=True)
        ok = r.returncode == 0 and r.stdout.strip()
        print(f"{'ok  ' if ok else 'FAIL'}  {num}  {path.name}")
        if not ok:
            failed.append((num, r.stderr.strip()[-400:]))
    print(f"\n{len(chosen) - len(failed)} of {len(chosen)} ran")
    for num, err in failed:
        print(f"\n--- {num}\n{err}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
