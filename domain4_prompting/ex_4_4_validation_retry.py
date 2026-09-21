"""4.4 Validate, then retry with the error attached.

Real scenario: extractions pass the schema and still fail downstream. Line
items do not sum to the total, and a shipping date has landed in invoice_date.

A schema removes syntax errors. Semantic errors need checks you write, and a
retry that carries three things: the document, what Claude produced, and the
exact complaint.

Some failures are not retryable at all. If the value is not in the document,
no amount of re-reading will find it.

Run it:
    python ex_4_4_validation_retry.py                     offline
    ANTHROPIC_API_KEY=sk-... python ex_4_4_validation_retry.py    real calls
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, call, get_client, recorded

EXTRACT_TOOL = {
    "name": "record_invoice",
    "description": "Record one invoice.",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_date": {"type": "string", "description": "ISO 8601"},
            "line_items": {"type": "array", "items": {
                "type": "object",
                "properties": {"description": {"type": "string"},
                               "amount": {"type": "number"}},
                "required": ["description", "amount"]}},
            "stated_total": {"type": "number"},
            "contract_end_date": {"type": ["string", "null"]},
        },
        "required": ["invoice_date", "line_items", "stated_total"],
    },
}

DOC = ("INVOICE 0412    invoice date 04/03/2026    shipped 09/03/2026\n"
       "widget 40.00\nshipping 7.90\nTOTAL 47.90\n"
       "Term: as defined in Addendum B (not attached)")


# ---------------------------------------------------------------- START HERE
def validate(record, document):
    """The checks a schema cannot do. Each error says what is wrong, precisely."""
    errors = []

    total = round(sum(i["amount"] for i in record["line_items"]), 2)
    if abs(total - record["stated_total"]) > 0.01:
        errors.append("line items sum to %.2f but stated_total is %.2f"
                      % (total, record["stated_total"]))

    printed = as_printed(record["invoice_date"])
    labelled = labelled_date(document, "invoice date")
    if printed and labelled and printed != labelled:
        # Both dates are on the page, so "is it in the document?" would pass.
        # The check that matters is whether it is the date under the right label.
        errors.append("invoice_date %s is printed as %s, but the date labelled "
                      "'invoice date' is %s" % (record["invoice_date"], printed, labelled))
    return errors


def labelled_date(document, label):
    """Find the date that follows a label, so a shipped date cannot pass as an
    invoice date just because both appear somewhere on the page."""
    match = re.search(re.escape(label) + r"\s+(\d{2}/\d{2}/\d{4})", document, re.I)
    return match.group(1) if match else None


def as_printed(iso_date):
    """Turn 2026-03-04 into 04/03/2026, the way this supplier prints it.

    Comparing an ISO string against a day-first document finds a mismatch on
    every invoice, which is a bug in the checker rather than in the extraction.
    """
    parts = iso_date.split("-")
    if len(parts) != 3:
        return None
    year, month, day = parts
    return "%s/%s/%s" % (day, month, year)


def is_retryable(errors, document):
    """New information next time, or the same answer again?

    A format or arithmetic mistake can be corrected from what is on the page.
    A value that is simply absent cannot, however many attempts you spend.
    """
    for error in errors:
        if "not stated in the document" in error or "Addendum" in document and "contract_end_date" in error:
            return False, "the source refers to a document you do not have"
    return True, "the information is on the page; the rendering was wrong"


def retry_prompt(document, failed_record, errors):
    """All three parts. Drop any one and the next attempt is guesswork."""
    return (
        "Original document:\n%s\n\n"
        "Your extraction:\n%s\n\n"
        "Validation errors:\n%s\n\n"
        "Re-extract, correcting only the listed problems. Leave every other "
        "field exactly as it is." % (document, json.dumps(failed_record, indent=2),
                                     "\n".join("- " + e for e in errors))
    )


def extract_with_retry(client, document, max_attempts=2):
    """Extract, check, and give the model the complaint rather than another try."""
    messages = [{"role": "user", "content": document}]
    for attempt in range(1, max_attempts + 1):
        reply = client.messages.create(
            model=MODEL, max_tokens=1024, tools=[EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "record_invoice"},
            messages=messages)
        record = [b.input for b in reply.content if b.type == "tool_use"][0]

        errors = validate(record, document)
        if not errors:
            return record, attempt, None

        retryable, reason = is_retryable(errors, document)
        if not retryable:
            return record, attempt, "stopped: " + reason

        messages = [{"role": "user", "content": retry_prompt(document, record, errors)}]

    return record, max_attempts, "stopped: two attempts did not fix it, send it to a human"


# ---------------------------------------------------------------- recorded replies
BAD = recorded(call("t1", "record_invoice",
                    invoice_date="2026-03-09",                 # the shipped date
                    line_items=[{"description": "widget", "amount": 40.00}],
                    stated_total=47.90,
                    contract_end_date=None))
GOOD = recorded(call("t2", "record_invoice",
                     invoice_date="2026-03-04",
                     line_items=[{"description": "widget", "amount": 40.00},
                                 {"description": "shipping", "amount": 7.90}],
                     stated_total=47.90,
                     contract_end_date=None))

if __name__ == "__main__":
    banner("4.4 validation and retry")
    record, attempts, note = extract_with_retry(get_client([BAD, GOOD]), DOC)

    print("attempt 1 produced a schema-valid record with two real mistakes:")
    print("   invoice_date 2026-03-09 (the shipped date), and one line item missing")
    print()
    print("validation caught:")
    for e in validate({"invoice_date": "2026-03-09",
                       "line_items": [{"description": "widget", "amount": 40.0}],
                       "stated_total": 47.90}, DOC):
        print("   -", e)
    print()
    print("the retry carried the document, the failed output and those errors.")
    print("attempt %d result: %s" % (attempts, json.dumps(record)))
    print("note:", note or "validated cleanly")
    print()
    print("the retry that is not worth making:")
    errors = ["contract_end_date is not stated in the document"]
    retryable, reason = is_retryable(errors, DOC)
    print("   retryable:", retryable, "-", reason)
    print("   mark the field unavailable and flag the case to fetch Addendum B.")
