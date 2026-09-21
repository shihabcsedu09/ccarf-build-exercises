"""3.6 Run Claude Code in a pipeline.

Real scenario: the review job hangs. The logs show it waiting for interactive
input that no runner will ever give it.

Four things a pipeline needs that an interactive session does not: run once
and exit, emit something a script can parse, carry the project's standards,
and be unable to change anything.

This writes the real workflow, the real schema and the real command line, then
parses a real result envelope. It does not call the API, so it costs nothing.

Run it:
    python ex_3_6_ci_pipeline.py
"""
import json
import os
import pathlib
import shlex
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner

# ---------------------------------------------------------------- START HERE
# The shape the next step parses. Enforced by the CLI, not requested in prose.
FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "severity": {"type": "string",
                                 "enum": ["critical", "high", "medium", "low"]},
                    "issue": {"type": "string"},
                    "fix": {"type": "string"},
                },
                "required": ["file", "line", "severity", "issue", "fix"],
            },
        }
    },
    "required": ["findings"],
}

# Rules the job cannot talk its way past, committed so they ship with the
# workflow. An allow rule left in settings.local.json never reaches the runner.
CI_SETTINGS = {
    "permissions": {
        "allow": ["Read(**)", "Grep(**)", "Glob(**)", "Bash(npm test:*)"],
        "deny": ["Edit(**)", "Write(**)", "Bash(git push:*)"],
    }
}

PROMPT = ("Review this pull request for correctness and security. "
          "Follow the standards in CLAUDE.md. Previous findings are in "
          "review-prev.json; report only new or still-unresolved issues.")


def build_command(schema_path, max_turns=25):
    """The exact argv. Every flag here answers a specific failure."""
    return [
        "claude",
        "-p", PROMPT,                     # answer once and exit; without it the job hangs
        "--output-format", "json",        # a parseable envelope, and cost fields
        "--json-schema", str(schema_path),  # the findings shape is enforced
        "--allowedTools", "Read,Grep,Glob,Bash(npm test:*)",  # only what review needs
        "--max-turns", str(max_turns),    # a run that loops cannot burn the whole job
    ]


WORKFLOW = """name: claude-review
on:
  pull_request:
    types: [opened, synchronize, ready_for_review]
jobs:
  review:
    if: github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4          # full repo, so CLAUDE.md is present
      - name: Review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          %s > review.json
      - run: node post-inline-comments.js review.json
"""


def parse_result(envelope):
    """What --output-format json gives you back, and the fields finance asks for."""
    data = json.loads(envelope)
    findings = json.loads(data["result"])["findings"]
    return {
        "findings": findings,
        "critical": [f for f in findings if f["severity"] == "critical"],
        "cost_usd": data.get("total_cost_usd"),
        "turns": data.get("num_turns"),
        "hit_the_cap": data.get("num_turns", 0) >= 25 or data.get("is_error", False),
    }


SAMPLE_ENVELOPE = json.dumps({
    "type": "result",
    "subtype": "success",
    "is_error": False,
    "num_turns": 7,
    "duration_ms": 41230,
    "total_cost_usd": 0.1832,
    "session_id": "b3f1c2e4-77aa-4c31-9d2e-6f0a1b8c9d55",
    "result": json.dumps({"findings": [
        {"file": "src/api/orders.ts", "line": 42, "severity": "critical",
         "issue": "request body saved without validation", "fix": "validate against OrderSchema"},
        {"file": "src/api/orders.ts", "line": 88, "severity": "low",
         "issue": "unused import", "fix": "remove it"}]}),
})

if __name__ == "__main__":
    banner("3.6 Claude Code in a pipeline", api=False)
    root = pathlib.Path(tempfile.mkdtemp())
    schema_path = root / "review-schema.json"
    schema_path.write_text(json.dumps(FINDINGS_SCHEMA, indent=2))
    (root / ".claude").mkdir()
    (root / ".claude" / "settings.json").write_text(json.dumps(CI_SETTINGS, indent=2))

    cmd = build_command(schema_path)
    # The schema really is written to a temp directory, but printing that
    # path would just be noise: in a repository it sits beside the workflow.
    shown = [".claude/review-schema.json" if c == str(schema_path) else c
             for c in cmd]
    print("the command the job runs:")
    print("   ", " ".join(shlex.quote(c) for c in shown))
    print()
    print("what each flag answers:")
    for flag, why in [
            ("-p", "run once and exit. Without it the job waits for a human and hangs"),
            ("--output-format json", "an envelope with cost and turn counts, not prose to scrape"),
            ("--json-schema", "findings come back with file, line, severity, fix, every time"),
            ("--allowedTools", "tests could not run when Bash was not permitted"),
            ("--max-turns", "one run in fifteen looped for 40 minutes and produced nothing")]:
        print("   %-22s %s" % (flag, why))
    print()
    print("committed permissions, so the job cannot edit or push:")
    print("   deny:", CI_SETTINGS["permissions"]["deny"])
    print()

    out = parse_result(SAMPLE_ENVELOPE)
    print("parsing a real result envelope:")
    print("   findings: %d   critical: %d   turns: %s   cost: $%.4f   hit the cap: %s"
          % (len(out["findings"]), len(out["critical"]), out["turns"],
             out["cost_usd"], out["hit_the_cap"]))
    for f in out["findings"]:
        print("     %s:%d  %-8s %s" % (f["file"], f["line"], f["severity"], f["issue"]))
    print()
    print("exit non-zero when anything critical is found:",
          "fail the build" if out["critical"] else "pass")
    print()
    print("the workflow file:")
    print(WORKFLOW % (" ".join(shlex.quote(c) for c in cmd[:6]) + " ..."))
    # shutil.which finds the real CLI. Printed with $HOME collapsed to ~,
    # so the output does not carry one machine's home directory.
    claude = shutil.which("claude")
    # Printed with $HOME collapsed to ~, so the output of this file does not
    # carry one machine's home directory. The real path is what gets run.
    shown = claude.replace(os.path.expanduser("~"), "~") if claude else None
    print("claude on this machine:", shown or "not installed")
    if claude:
        v = subprocess.run([claude, "--version"], capture_output=True, text=True, timeout=30)
        print("version:", v.stdout.strip())
    shutil.rmtree(root, ignore_errors=True)
