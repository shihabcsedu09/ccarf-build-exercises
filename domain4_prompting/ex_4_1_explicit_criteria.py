"""4.1 Replace vague instructions with criteria Claude can check.

Real scenario: the comment reviewer is told to "check that comments are
accurate and up to date". It flags TODO markers, and misses comments that
describe behaviour the code no longer has.

"Accurate" is not a test. "Contradicts what the code does" is. Name the
categories, define each one, say what not to flag, then lock the vocabulary
with an enum so a sixth severity cannot appear.

Run it:
    python ex_4_1_explicit_criteria.py                     offline
    ANTHROPIC_API_KEY=sk-... python ex_4_1_explicit_criteria.py    real calls
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, call, get_client, recorded, say

VAGUE = "Review the comments. Check they are accurate and up to date. Be conservative."

# ---------------------------------------------------------------- START HERE
EXPLICIT = """You review code comments.

Flag a comment ONLY when the behaviour it describes contradicts what the code does.

Do NOT flag: TODO and FIXME markers, short descriptions, comments that are
merely brief, or anything about formatting.

Severity, choose exactly one:
  CRITICAL  the comment claims a safety or security property the code lacks
            e.g. "# input is sanitised here" above code that sanitises nothing
  MEDIUM    the comment states a different return value or side effect
  LOW       the comment is stale but harmless

If two severities fit, choose the lower one.
Categories currently switched off because they are over half wrong: style, naming.
"""

# The enum is the second half of the fix. Criteria tell Claude what to decide;
# the enum stops the vocabulary drifting once it has decided.
REPORT_TOOL = {
    "name": "report_comment_findings",
    "description": "Report comments whose claims contradict the code.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {"type": "array", "items": {
                "type": "object",
                "properties": {
                    "line": {"type": "integer"},
                    "severity": {"type": "string",
                                 "enum": ["CRITICAL", "MEDIUM", "LOW"]},
                    "why": {"type": "string",
                            "description": "what the comment claims, and what the code does"},
                },
                "required": ["line", "severity", "why"]}}
        },
        "required": ["findings"],
    },
}

CODE = '''def save_user(raw):
    # input is sanitised here before it reaches the database
    db.execute("INSERT INTO users VALUES (" + raw + ")")

    # TODO: add pagination
    return True   # returns the new user id
'''


def review(client, system, with_schema):
    kwargs = dict(model=MODEL, max_tokens=800, system=system,
                  messages=[{"role": "user", "content": CODE}])
    if with_schema:
        kwargs["tools"] = [REPORT_TOOL]
        kwargs["tool_choice"] = {"type": "tool", "name": "report_comment_findings"}
    reply = client.messages.create(**kwargs)
    for block in reply.content:
        if block.type == "tool_use":
            return block.input["findings"]
    return [{"line": 0, "severity": "-", "why":
             "".join(b.text for b in reply.content if b.type == "text")}]


# ---------------------------------------------------------------- recorded replies
VAGUE_SCRIPT = [recorded(say(
    "Line 5 has an unresolved TODO which should be tracked. "
    "The docstring is missing. Severity: important."))]

EXPLICIT_SCRIPT = [recorded(call("t1", "report_comment_findings", findings=[
    {"line": 2, "severity": "CRITICAL",
     "why": "claims input is sanitised; the query concatenates raw input directly"},
    {"line": 6, "severity": "MEDIUM",
     "why": "claims it returns the new user id; it returns True"}]))]

if __name__ == "__main__":
    banner("4.1 explicit criteria")
    print("the code under review has three comments: one false safety claim,")
    print("one TODO, and one wrong return description.")
    print()

    print("vague instruction:", VAGUE)
    for f in review(get_client(VAGUE_SCRIPT), VAGUE, with_schema=False):
        print("   ->", f["why"][:120])
    print("   it flagged the TODO, invented a severity word, and missed the")
    print("   comment that claims the input is sanitised.")
    print()

    print("explicit criteria, plus an enum:")
    for f in review(get_client(EXPLICIT_SCRIPT), EXPLICIT, with_schema=True):
        print("   line %-3d %-9s %s" % (f["line"], f["severity"], f["why"]))
    print()
    print("Every finding is now checkable against the rule that produced it,")
    print("and the severity can only be one of three words.")
