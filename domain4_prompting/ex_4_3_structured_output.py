"""4.3 Build a structured extraction tool with a schema.

The schema guarantees the shape and never the truth. A required field
with nothing to put in it is an instruction to invent something.

Run it:  python ex_4_3_structured_output.py
"""
import json

# ---------------------------------------------------------------- START HERE
SCHEMA = {
    "name": "record_invoice",
    "description": "Record the fields extracted from one invoice.",
    "input_schema": {
        "type": "object",
        "properties": {
            # nullable, because about 30% of invoices genuinely have no PO
            "po_number": {"type": ["string", "null"],
                          "description": "as printed; null when there is none"},
            # an escape hatch, so a delivery note is not forced to be a receipt
            "document_type": {"type": "string",
                              "enum": ["invoice", "receipt", "credit_note",
                                       "other", "unclear"]},
            "document_type_detail": {"type": ["string", "null"]},
            # both numbers plus a flag, so a disagreement is visible
            "stated_total":     {"type": "number"},
            "calculated_total": {"type": "number"},
            "conflict_detected": {"type": ["string", "null"]},
        },
        "required": ["document_type", "stated_total", "calculated_total"],
    },
}


def field_is_required(schema, field):
    return field in schema["input_schema"]["required"]


def allows_null(schema, field):
    t = schema["input_schema"]["properties"][field]["type"]
    return isinstance(t, list) and "null" in t


def what_the_model_does(schema, field, value_in_document):
    """The pressure a required field creates when the document has nothing."""
    if value_in_document is not None:
        return value_in_document
    if allows_null(schema, field):
        return None                       # honest
    if field_is_required(schema, field):
        return "PO-0000"                  # invented, to satisfy the schema
    return None


def tool_choice(known_document_type):
    return ({"type": "tool", "name": "record_invoice"} if known_document_type
            else {"type": "any"})         # guarantee a call, let Claude pick


if __name__ == "__main__":
    print("po_number nullable :", allows_null(SCHEMA, "po_number"))
    print("document has no PO ->", what_the_model_does(SCHEMA, "po_number", None))

    required_schema = json.loads(json.dumps(SCHEMA))
    required_schema["input_schema"]["properties"]["po_number"]["type"] = "string"
    required_schema["input_schema"]["required"].append("po_number")
    print("same, but required ->",
          what_the_model_does(required_schema, "po_number", None))

    print("\ntool_choice, type known  :", tool_choice(True))
    print("tool_choice, type unknown:", tool_choice(False))
    print("\nThe schema cannot check that the totals are true. That is 4.4.")
