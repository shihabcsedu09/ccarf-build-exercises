"""4.3 Get JSON you can rely on.

Real scenario: the invoice extractor asks for JSON in the prompt. About 4% of
replies arrive wrapped in a code fence or behind a sentence, and the loader
rejects them.

Put the shape in a tool's input_schema and force the call. The API constrains
the arguments, so there is no prose to strip.

The schema guarantees the shape and never the truth. And a required field with
nothing to fill it is an instruction to invent something.

Run it:
    python ex_4_3_structured_output.py                     offline
    ANTHROPIC_API_KEY=sk-... python ex_4_3_structured_output.py    real calls
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, call, get_client, recorded, say

# ---------------------------------------------------------------- START HERE
EXTRACT_TOOL = {
    "name": "record_invoice",
    "description": "Record the fields extracted from one invoice.",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},
            "issue_date": {"type": "string",
                           "description": "ISO 8601, e.g. 2026-03-04"},

            # Nullable, because about 30% of invoices genuinely have no PO.
            # Required with no source value is how PO-0000 gets invented.
            "po_number": {"type": ["string", "null"],
                          "description": "as printed; null when the invoice has none"},

            # An escape hatch, so a delivery note is not forced to be a receipt.
            "document_type": {"type": "string",
                              "enum": ["invoice", "receipt", "credit_note",
                                       "other", "unclear"]},
            "document_type_detail": {"type": ["string", "null"],
                                     "description": "fill in when type is other or unclear"},

            # Both numbers and a flag, so a disagreement is visible instead of
            # being quietly resolved in one direction.
            "stated_total": {"type": "number", "description": "as printed"},
            "calculated_total": {"type": "number", "description": "sum the line items yourself"},
            "conflict_detected": {"type": ["string", "null"]},
        },
        "required": ["invoice_number", "issue_date", "document_type",
                     "stated_total", "calculated_total"],
    },
}


def extract(client, document):
    """Force the tool, then read the arguments. Nothing to parse, nothing to strip."""
    reply = client.messages.create(
        model=MODEL, max_tokens=1024,
        system=("Extract the invoice. Copy values as printed. Use null where "
                "the document does not state a value; never infer one."),
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "record_invoice"},
        messages=[{"role": "user", "content": document}])
    for block in reply.content:
        if block.type == "tool_use":
            return block.input
    raise RuntimeError("expected a tool call")


def shape_is_valid(record):
    """What the schema already guarantees, so you never write this check."""
    required = EXTRACT_TOOL["input_schema"]["required"]
    return all(k in record for k in required)


def truth_checks(record):
    """What the schema cannot guarantee, so you do write these."""
    problems = []
    if abs(record["stated_total"] - record["calculated_total"]) > 0.01:
        problems.append("totals disagree: stated %.2f, line items %.2f"
                        % (record["stated_total"], record["calculated_total"]))
    if record.get("po_number") in ("PO-0000", "N/A", ""):
        problems.append("po_number looks invented: %r" % record["po_number"])
    return problems


DOC = ("INVOICE INV-2026-0412   date 04/03/2026\n"
       "2 x widget @ 20.00 = 40.00\nshipping 7.90\n"
       "TOTAL 520.00\n(no purchase order reference)")

# ---------------------------------------------------------------- recorded replies
PROMPT_ONLY = [recorded(say('Here is the JSON you asked for:\n```json\n'
                            '{"invoice_number": "INV-2026-0412"}\n```'))]

FORCED = [recorded(call("t1", "record_invoice",
                        invoice_number="INV-2026-0412",
                        issue_date="2026-03-04",
                        po_number=None,
                        document_type="invoice",
                        document_type_detail=None,
                        stated_total=520.00,
                        calculated_total=47.90,
                        conflict_detected="line items sum to 47.90, invoice states 520.00"))]

if __name__ == "__main__":
    banner("4.3 structured output")
    print("asking for JSON in the prompt:")
    reply = get_client(PROMPT_ONLY).messages.create(
        model=MODEL, max_tokens=400,
        system="Reply with JSON only.",
        messages=[{"role": "user", "content": DOC}])
    raw = "".join(b.text for b in reply.content if b.type == "text")
    print("  ", raw.replace("\n", " ")[:90])
    try:
        json.loads(raw)
        print("   parsed fine")
    except ValueError as exc:
        print("   json.loads failed:", exc)
    print()

    record = extract(get_client(FORCED), DOC)
    print("forcing the tool call:")
    print("  ", json.dumps(record))
    print("   shape valid without checking:", shape_is_valid(record))
    print()
    print("what the schema could not tell you:")
    for problem in truth_checks(record):
        print("   -", problem)
    print()
    print("po_number is null because the invoice has none. Marking it required")
    print("is what produces PO-0000 in the 30% of invoices without one.")
