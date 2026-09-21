"""4.4 Build a validation and retry loop.

A retry carries the document, the failed output and the exact error.
No retry finds a fact the document never had.

Run it:  python ex_4_4_validation_retry.py
"""
from decimal import Decimal

MAX_RETRIES = 2
ABSENT_MARKERS = ("on file", "see attached", "per addendum")


# ---------------------------------------------------------------- START HERE
def validate(record, document):
    """Semantic checks the schema cannot express."""
    errors = []
    items = sum(Decimal(str(i["qty"])) * Decimal(str(i["price"]))
                for i in record["line_items"])
    if abs(items - Decimal(str(record["stated_total"]))) > Decimal("0.01"):
        errors.append({"field": "line_items",
                       "error": f"items sum to {items}, stated total is "
                                f"{record['stated_total']}"})
    if record.get("due_date") and record.get("invoice_date"):
        if record["due_date"] < record["invoice_date"]:
            errors.append({"field": "due_date",
                           "error": "due_date is before invoice_date; likely swapped"})
    for field in ("po_number", "vendor"):
        value = record.get(field)
        if value and value not in document:
            errors.append({"field": field,
                           "error": f"{value!r} does not appear in the document"})
    return errors


def source_is_missing(document):
    """Some failures are not the model's fault, and no retry can fix them."""
    return any(marker in document.lower() for marker in ABSENT_MARKERS)


def retry_prompt(document, failed, errors):
    return (f"<document>{document}</document>\n"
            f"<previous_extraction>{failed}</previous_extraction>\n"
            f"<validation_errors>{errors}</validation_errors>\n"
            "Correct only the fields named in the errors. If a value is not in "
            "the document, return null rather than a plausible value.")


def extract_with_retry(document, extract, correct):
    record = extract(document)
    for attempt in range(MAX_RETRIES):
        errors = validate(record, document)
        if not errors:
            return {"status": "ok", "record": record, "attempts": attempt}
        if source_is_missing(document):
            return {"status": "incomplete", "errors": errors,
                    "action": "request the missing attachment"}
        record = correct(retry_prompt(document, record, errors))
    return {"status": "needs_review", "record": record,
            "errors": validate(record, document)}


# ---------------------------------------------------------------- stubs
DOC_OK = "Acme Ltd invoice. PO-88213. 2 x 250.00. Total 500.00."
DOC_MISSING = "Acme Ltd invoice. Approval letter on file. Total 500.00."


def extract(document):
    return {"vendor": "Acme Ltd", "po_number": "PO-88213",
            "line_items": [{"qty": 2, "price": 225}], "stated_total": 500}


def correct(prompt):
    return {"vendor": "Acme Ltd", "po_number": "PO-88213",
            "line_items": [{"qty": 2, "price": 250}], "stated_total": 500}


if __name__ == "__main__":
    first = extract(DOC_OK)
    print("first attempt errors:", validate(first, DOC_OK))

    result = extract_with_retry(DOC_OK, extract, correct)
    print("after retry         :", result["status"], "in", result["attempts"], "retry")

    print("\nmissing source      :", extract_with_retry(DOC_MISSING, extract, correct))
    print("\nRetrying that second one would produce a plausible invented date.")
