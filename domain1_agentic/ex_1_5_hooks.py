"""1.5 Hooks for normalising data and enforcing policy.

PostToolUse tidies what Claude is about to read. PreToolUse forbids.

Run it:  python ex_1_5_hooks.py
"""
from pprint import pprint

from datetime import datetime, timezone

STATUS = {1: "pending", 2: "shipped", 3: "delivered", 4: "returned"}
KEEP = ("order_id", "order_date", "status", "amount", "return_eligible")
REFUND_LIMIT = 500


def to_iso(value):
    """Unix seconds, ISO strings and dd/mm/yyyy all become one ISO date."""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc).date().isoformat()
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return value


# ---------------------------------------------------------------- START HERE
def post_tool_use(tool, result):
    """Runs after the tool, before Claude sees the result."""
    out = dict(result)
    for key in ("order_date", "created_at"):
        if key in out:
            out[key] = to_iso(out[key])
    if isinstance(out.get("status"), int):
        out["status"] = STATUS.get(out["status"], "unknown")
    if "card_number" in out:
        out["card_number"] = "****" + str(out["card_number"])[-4:]
    if tool == "lookup_order":
        out = {k: v for k, v in out.items() if k in KEEP}     # 40 fields down to 5
    return out


def pre_tool_use(tool, args):
    """Runs before the tool. Returns None to allow, or a reason to refuse."""
    if tool == "process_refund" and args.get("amount", 0) > REFUND_LIMIT:
        return f"Refunds over {REFUND_LIMIT} need a human. Call request_approval."
    return None


if __name__ == "__main__":
    raw = {"order_id": "8891", "order_date": 1767225600, "status": 2,
           "amount": 240.0, "return_eligible": True,
           "card_number": "4111111111111111",
           "warehouse_route": "LHR-3", "carrier_telemetry": {"scans": 12}}
    print("before:", len(raw), "fields")
    clean = post_tool_use("lookup_order", raw)
    print("after :", len(clean), "fields ->")
    pprint(clean, width=74)

    print("\nrefund 400 ->",
          pre_tool_use("process_refund", {"amount": 400}) or "allowed")
    print("refund 900 ->", pre_tool_use("process_refund", {"amount": 900}))
    print("\nA PostToolUse hook could not have stopped the 900: by the time it")
    print("runs, the money has already moved.")
