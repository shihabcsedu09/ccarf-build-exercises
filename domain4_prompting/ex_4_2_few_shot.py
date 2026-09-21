"""4.2 Add examples, and only where examples are the fix.

Real scenario: the agent picks the wrong tool on ambiguous requests like
"I need help with my recent purchase". Rules have not fixed it.

Two to four examples is the dose. What matters more is what each one carries:
an example that shows only the answer teaches the format, and an example that
shows the reasoning teaches the judgement you were short of.

Examples cannot fix a thin tool description or a missing gate. Those live in
different layers.

Run it:
    python ex_4_2_few_shot.py                     offline
    ANTHROPIC_API_KEY=sk-... python ex_4_2_few_shot.py    real calls
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, get_client, recorded, say

# Answer only. Teaches the shape, nothing about the decision.
THIN_EXAMPLES = """Request: "check my order #12345"  -> lookup_order
Request: "update my address"     -> get_customer
"""

# ---------------------------------------------------------------- START HERE
# Answer plus the reason. The reason is what generalises to a case you did not
# list, which is the whole point of picking hard examples.
RICH_EXAMPLES = """Request: "check my order #12345"
Choose: lookup_order
Why: an order number is present, so this is about one purchase. get_customer
would only identify the person.

Request: "I moved house, update my details"
Choose: get_customer
Why: no order is mentioned. The subject is the account itself.

Request: "my recent purchase arrived broken"
Choose: get_customer, then lookup_order
Why: ambiguous. Identify the customer first, then find the order in their
history. Guessing an order number would risk the wrong account.
"""

WHEN_EXAMPLES_HELP = [
    ("the output format keeps drifting", True, "two or three pin the shape faster than describing it"),
    ("borderline judgement calls keep flipping", True, "show the borderline case, with its reasoning"),
    ("fields come back empty though the data is there", True, "show one example that extracts them"),
    ("the agent picks the wrong tool", False, "fix the tool description; that is what it reads"),
    ("the categories were never defined", False, "write the criteria first, then add examples"),
    ("a rule must hold every time", False, "that is a gate, in code. Examples change odds"),
]


def route(client, examples, request):
    system = ("You are a support agent. Choose the tool to call and say why in "
              "one line.\n\nExamples of correct choices:\n" + examples)
    reply = client.messages.create(
        model=MODEL, max_tokens=400, system=system,
        messages=[{"role": "user", "content": request}])
    return "".join(b.text for b in reply.content if b.type == "text")


# ---------------------------------------------------------------- recorded replies
AMBIGUOUS = "I need help with my recent purchase"
THIN_SCRIPT = [recorded(say("lookup_order"))]
RICH_SCRIPT = [recorded(say(
    "get_customer first. No order number is given, so identify the customer "
    "and read their recent orders rather than guessing which purchase it is."))]

if __name__ == "__main__":
    banner("4.2 few-shot examples")
    print("request:", AMBIGUOUS)
    print()
    print("with answer-only examples:")
    print("  ", route(get_client(THIN_SCRIPT), THIN_EXAMPLES, AMBIGUOUS))
    print("   it copied the shape of the nearest example and guessed.")
    print()
    print("with examples that carry their reasoning:")
    print("  ", route(get_client(RICH_SCRIPT), RICH_EXAMPLES, AMBIGUOUS))
    print("   the third example was the ambiguous one, and its reason transfers.")
    print()
    print("examples sizes: %d chars vs %d chars"
          % (len(THIN_EXAMPLES), len(RICH_EXAMPLES)))
    print()
    print("when examples are the right fix:")
    for symptom, helps, note in WHEN_EXAMPLES_HELP:
        print("   %-44s %-4s %s" % (symptom, "yes" if helps else "no", note))
    print()
    print("Choose the cases that go wrong today. Examples of what already works")
    print("spend tokens teaching nothing.")
