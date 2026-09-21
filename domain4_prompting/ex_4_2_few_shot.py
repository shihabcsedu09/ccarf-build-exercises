"""4.2 Add few-shot examples that do not leak.

The model copies everything in an example, not only the part you meant.

Run it:  python ex_4_2_few_shot.py
"""

LEAKY = [      # three examples, one vendor, a purchase order every time
    {"vendor": "Northwind Supply", "po_number": "PO-2024-0113"},
    {"vendor": "Northwind Supply", "po_number": "PO-2024-0114"},
    {"vendor": "Northwind Supply", "po_number": "PO-2024-0115"},
]

# ---------------------------------------------------------------- START HERE
GOOD = [       # three vendors, three formats, and one absent value shown
    {"vendor": "Acme Ltd",    "po_number": "PO-88213"},
    {"vendor": "Moller AS",   "po_number": None},          # the empty case
    {"vendor": "Globex GmbH", "po_number": "4500221"},      # a different format
]


def constants(examples):
    """Anything identical across every example is what gets copied."""
    keys = examples[0].keys()
    return {k: examples[0][k] for k in keys
            if all(e[k] == examples[0][k] for e in examples)}


def shows_empty_case(examples, field):
    return any(e[field] is None for e in examples)


def audit(examples):
    return {"copied_verbatim": constants(examples),
            "shows_absent_value": shows_empty_case(examples, "po_number"),
            "count_ok": 2 <= len(examples) <= 4}


if __name__ == "__main__":
    for label, examples in (("leaky", LEAKY), ("good", GOOD)):
        result = audit(examples)
        print(f"{label:6} {result}")

    print("\nThe leaky set shares a vendor name and always has a purchase order,")
    print("so the model copies both: Northwind appears on other vendors' invoices")
    print("and a PO gets invented where there was none.")
    print("\nMore examples from the same template make it worse, not better.")
