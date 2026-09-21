"""3.6 Set up a CI pipeline with Claude Code.

-p stops the hang. A schema makes the output parseable. --max-turns
bounds a loop. Deny rules are the only part that survives a hostile PR.

Run it:  python ex_3_6_ci_pipeline.py
"""
import json

# ---------------------------------------------------------------- START HERE
def build_command(prompt_file, schema_file, max_turns=30):
    """The flags that matter, in the order they solve problems."""
    return [
        "claude", "-p", f"$(cat {prompt_file})",   # -p: answer once and exit
        "--output-format", "json",                 # a result envelope, not prose
        "--json-schema", schema_file,              # findings a script can post
        "--max-turns", str(max_turns),             # a loop cannot run forever
    ]


SETTINGS = {                                       # .claude/settings.json, committed
    "permissions": {
        "allow": ["Read", "Grep", "Glob", "Bash(git diff:*)"],
        "deny":  ["Edit", "Write", "Bash(git push:*)"],
    }
}


def is_allowed(tool, settings):
    """Deny wins, and it runs before the tool does, so a prompt injected
    into a pull request cannot argue with it."""
    perms = settings["permissions"]
    if any(tool.startswith(d.split("(")[0]) for d in perms["deny"]):
        return False
    return any(tool.startswith(a.split("(")[0]) for a in perms["allow"])


def read_result(envelope):
    """What the job checks before posting anything."""
    if envelope.get("is_error"):
        return "fail the job"
    if envelope["num_turns"] >= 30:
        return "hit the turn cap: post findings but flag the run"
    return f"post {len(envelope['structured_output']['findings'])} findings"


if __name__ == "__main__":
    for part in build_command("prompts/review.md", ".github/schema.json"):
        print("   ", part)

    print("\npermission checks:")
    for tool in ("Read", "Grep", "Edit", "Bash(git push --force)"):
        print(f"  {tool:24} {'allowed' if is_allowed(tool, SETTINGS) else 'DENIED'}")

    print("\nresult envelopes:")
    for env in ({"is_error": False, "num_turns": 12,
                 "structured_output": {"findings": [1, 2, 3]}},
                {"is_error": False, "num_turns": 30,
                 "structured_output": {"findings": [1]}},
                {"is_error": True, "num_turns": 4}):
        head = f"turns={env['num_turns']:<3} error={str(env['is_error']):5}"
        print(f"  {head} -> {read_result(env)}")
