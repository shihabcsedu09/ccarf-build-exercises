"""5.1 Keep the exact values alive in a long conversation.

Real scenario: at turn 4 the customer says "a refund of 247.83 for order 8891,
placed on 3 March". By turn 30 the history has been summarised and that line
reads "the customer wants a refund for a recent order". The agent then quotes
the wrong amount, and the customer notices.

Summarisers compress meaning. Numbers, dates and order ids are exactly what
they drop. So keep those out of the part that gets compressed.

Run it:
    python ex_5_1_case_facts.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, get_client, recorded, say

CASE_FACTS = {
    "customer_id": "C-4421 (verified by email)",
    "order": "#8891, placed 2026-03-03",
    "refund_requested": "247.83",
    "stated_expectation": "the 15% loyalty discount I mentioned",
}

OLD_TURNS = [
    {"role": "user", "content": "I want a refund of 247.83 for order 8891 from 3 March."},
    {"role": "assistant", "content": "Let me look that up."},
] * 12

RECENT_TURNS = [
    {"role": "user", "content": "Any update on that refund?"},
    {"role": "assistant", "content": "Checking the payment status now."},
]

# What lookup_order really returns: 40 fields, of which the agent needs five.
RAW_ORDER = {
    "order_id": "8891", "status": "shipped", "total": 247.83,
    "expected_delivery": "2026-03-10", "product": "wireless headphones",
    "warehouse_id": "W-12", "carrier_ref": "DHL-9931", "pick_path": "A7-C3",
    "tax_breakdown": {"vat": 41.3}, "billing_address_id": 88213,
    "audit_created_by": "svc-orders", "internal_notes": "none",
}


# ---------------------------------------------------------------- START HERE
def lossy_summary(turns):
    """What a summariser does to a transcript: keeps the gist, drops the digits."""
    return "The customer asked about a refund for a recent order and we looked it up."


def build_prompt(case_facts, older_turns, recent_turns):
    """Four parts, in the order that survives both compression and caching.

    Facts first and verbatim, then the summary, then the recent turns. The
    facts never enter the part that shrinks, so they cannot be paraphrased away.
    """
    facts_block = ("## CASE FACTS (exact values, quote them, never paraphrase)\n"
                   + json.dumps(case_facts, indent=2))
    summary_block = "## SUMMARY OF EARLIER TURNS\n" + lossy_summary(older_turns)
    return ([{"role": "user", "content": facts_block + "\n\n" + summary_block}]
            + list(recent_turns))


def trim_tool_result(raw, keep=("order_id", "status", "total",
                                "product", "expected_delivery")):
    """Trim at the door. Thirty-five unused fields, repeated over six lookups,
    is what fills a window that then has to be summarised."""
    return dict((k, v) for k, v in raw.items() if k in keep)


def cache_friendly_system(policy, tools_text, volatile):
    """Static first, volatile last. A timestamp on line one changes the prefix
    on every turn, and the cache never gets a hit."""
    return [
        {"type": "text", "text": tools_text},
        {"type": "text", "text": policy, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": volatile},      # after the breakpoint
    ]


def ask(client, messages):
    """Send the assembled prompt and see which number comes back."""
    reply = client.messages.create(
        model=MODEL, max_tokens=300,
        system="You are a support agent. Quote exact amounts and order numbers.",
        messages=messages + [{"role": "user", "content":
                              "Remind me what refund we agreed and on which order."}])
    return "".join(b.text for b in reply.content if b.type == "text")


# Two recorded replies: what the model can say from each prompt.
WITHOUT_FACTS = [recorded(say(
    "You asked about a refund on a recent order. Let me pull up the details."))]
WITH_FACTS = [recorded(say(
    "A refund of 247.83 on order #8891, placed on 3 March, including the 15% "
    "loyalty discount you mentioned."))]

if __name__ == "__main__":
    banner("5.1 case facts, trimming and cache order")

    print("turn 4, what the customer said:")
    print("  ", OLD_TURNS[0]["content"])
    print("after summarising:")
    print("  ", lossy_summary(OLD_TURNS))
    print("   the amount, the order number and the date are all gone.")
    print()

    messages = build_prompt(CASE_FACTS, OLD_TURNS, RECENT_TURNS)
    print("the prompt that is actually sent:")
    print(messages[0]["content"])
    print("   ... then %d recent turns, verbatim" % len(RECENT_TURNS))
    print()
    survives = all(str(v).split(" ")[0] in messages[0]["content"]
                   for v in CASE_FACTS.values())
    print("every exact value still present at turn 30:", survives)
    print()

    no_facts = [{"role": "user", "content": "## SUMMARY OF EARLIER TURNS\n"
                 + lossy_summary(OLD_TURNS)}] + RECENT_TURNS
    print("asked at turn 30, with only the summary:")
    print("  ", ask(get_client(WITHOUT_FACTS), no_facts))
    print("asked at turn 30, with the facts block:")
    print("  ", ask(get_client(WITH_FACTS), messages))
    print()

    trimmed = trim_tool_result(RAW_ORDER)
    print("tool result: %d fields in, %d fields to the model"
          % (len(RAW_ORDER), len(trimmed)))
    print("  ", json.dumps(trimmed))
    print("   across six lookups that is %d fields of noise that never arrive."
          % ((len(RAW_ORDER) - len(trimmed)) * 6))
    print()

    system = cache_friendly_system("...14,000 tokens of refund policy...",
                                   "...tool definitions...",
                                   "Current time: 2026-09-21T10:42:17Z")
    print("system blocks, in cache order:")
    for block in system:
        marker = "  <-- breakpoint" if "cache_control" in block else ""
        print("   %-44s%s" % (block["text"][:44], marker))
    print("   volatile content sits after the breakpoint, so the cached prefix")
    print("   stays identical from turn to turn.")
