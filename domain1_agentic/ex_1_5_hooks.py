"""1.5 Write PreToolUse and PostToolUse hooks.

Real scenario: the support agent talks to three MCP servers. One returns Unix
timestamps, one ISO dates, one numeric status codes. And refunds over 500 must
never go through on their own.

Pre runs before a tool and can allow, deny, ask a human or rewrite the input.
Post runs after and can rewrite what Claude is allowed to see.

These functions have the signature the Agent SDK calls. With the SDK installed
you pass them straight into ClaudeAgentOptions(hooks=...); the dispatcher below
applies the same decisions so the file runs either way.

Run it:
    python ex_1_5_hooks.py
"""
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import banner

STATUS_WORDS = {1: "pending", 2: "shipped", 3: "delivered"}


# ---------------------------------------------------------------- START HERE
def refund_limit(input_data, tool_use_id, context):
    """PreToolUse. Return {} to allow, or a deny decision Claude must act on."""
    if input_data["tool_name"].endswith("process_refund"):
        if input_data["tool_input"].get("amount", 0) > 500:
            return {"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason":
                    "Over the 500 limit. Call escalate_to_human with the case summary.",
            }}
    return {}


def require_approval(input_data, tool_use_id, context):
    """PreToolUse. 'ask' pauses for a person instead of refusing outright.

    Use it where the action is legitimate but somebody has to agree to it.
    """
    if input_data["tool_name"].endswith("delete_account"):
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": "Account deletion needs a human to confirm.",
        }}
    return {}


def normalise_output(input_data, tool_use_id, context):
    """PostToolUse. Rewrite the result before Claude reads it.

    Three servers, three date formats. Convert once here and the model never
    has to guess, which is the difference between a right answer and a
    confident wrong one.
    """
    result = dict(input_data["tool_response"])

    for key in ("created_at", "updated_at"):
        if isinstance(result.get(key), int):          # Unix seconds
            result[key] = datetime.datetime.utcfromtimestamp(
                result[key]).strftime("%Y-%m-%d")

    if isinstance(result.get("status"), int):         # numeric status code
        result["status"] = STATUS_WORDS.get(result["status"], "unknown")

    # Trim only what this hook understands. A blanket filter would empty every
    # other tool's result, which is a worse bug than the one being fixed.
    if "order_id" in result:
        keep = ("order_id", "status", "total", "created_at", "expected_delivery")
        result = dict((k, v) for k, v in result.items() if k in keep)

    return {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                   "updatedToolOutput": result}}


# ---------------------------------------------------------------- the dispatcher
def run_tool(name, arguments, raw_result, pre_hooks, post_hooks):
    """Apply the hooks exactly as the Agent SDK would, then return what Claude sees."""
    for hook in pre_hooks:
        out = hook({"tool_name": name, "tool_input": arguments}, "toolu_x", None)
        decision = out.get("hookSpecificOutput", {}).get("permissionDecision")
        if decision in ("deny", "ask"):
            return {"decision": decision,
                    "reason": out["hookSpecificOutput"]["permissionDecisionReason"]}

    seen = raw_result
    for hook in post_hooks:
        out = hook({"tool_name": name, "tool_response": seen}, "toolu_x", None)
        seen = out.get("hookSpecificOutput", {}).get("updatedToolOutput", seen)
    return {"decision": "allow", "claude_sees": seen}


# The same two rules, written for Claude Code instead of the SDK. Same idea,
# different file: a matcher picks the tool, exit code 2 blocks and explains.
SETTINGS_JSON = {
    "hooks": {
        "PreToolUse": [{"matcher": "mcp__support__process_refund",
                        "hooks": [{"type": "command",
                                   "command": "bash .claude/hooks/refund_limit.sh"}]}],
        "PostToolUse": [{"matcher": "mcp__.*",
                         "hooks": [{"type": "command",
                                    "command": "python .claude/hooks/normalise.py"}]}],
    }
}

if __name__ == "__main__":
    banner("1.5 hooks: pre is the bouncer, post is the translator", api=False)
    pre = [refund_limit, require_approval]
    post = [normalise_output]

    raw = {"order_id": "8891", "status": 2, "created_at": 1741046400,
           "total": 47.9, "warehouse_code": "W-12", "carrier_ref": "DHL-9931",
           "internal_notes": "none", "expected_delivery": "2026-09-24"}

    print("small refund:")
    print("  ", run_tool("mcp__support__process_refund", {"amount": 47.9}, {"ok": True}, pre, post))
    print("large refund:")
    print("  ", run_tool("mcp__support__process_refund", {"amount": 750}, {"ok": True}, pre, post))
    print("account deletion:")
    print("  ", run_tool("mcp__support__delete_account", {"id": "C-4421"}, {"ok": True}, pre, post))
    print()
    print("tool returned %d fields, two of them machine formats:" % len(raw))
    print("  ", raw)
    seen = run_tool("mcp__orders__lookup_order", {}, raw, pre, post)["claude_sees"]
    print("Claude sees %d fields, already in words:" % len(seen))
    print("  ", seen)
    print()
    print("The same two rules for Claude Code, in .claude/settings.json:")
    print(json.dumps(SETTINGS_JSON, indent=2))
