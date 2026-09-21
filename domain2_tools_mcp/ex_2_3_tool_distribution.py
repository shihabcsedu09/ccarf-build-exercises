"""2.3 Distribute tools across a multi-agent system.

Four or five tools per role. tool_choice decides whether Claude may
answer in words, must call something, or must call one named tool.

Run it:  python ex_2_3_tool_distribution.py
"""

ALL_TOOLS = [f"tool_{i}" for i in range(1, 23)]          # 22 tools in the catalogue

AGENTS = {
    "intake":    ["get_customer", "lookup_order"],
    "refunds":   ["lookup_order", "process_refund", "escalate_to_human"],
    "synthesis": ["verify_fact"],      # a narrow slice, not the whole search kit
}

GUIDELINE = 5


# ---------------------------------------------------------------- START HERE
def check_distribution(agents, guideline=GUIDELINE):
    """Flag any role holding more tools than it can choose between reliably."""
    return {name: {"count": len(tools), "ok": len(tools) <= guideline}
            for name, tools in agents.items()}


def tool_choice(moment):
    """The three settings the exam asks about."""
    if moment == "normal_turn":
        return {"type": "auto"}                    # may answer in words
    if moment == "must_produce_structured_output":
        return {"type": "any"}                     # must call something
    if moment == "prerequisite_first":
        return {"type": "tool", "name": "extract_metadata"}   # must call this one
    raise ValueError(moment)


def sequence_for_prerequisite():
    """Force the first call, then hand control back, so the model can choose."""
    return [tool_choice("prerequisite_first"), tool_choice("normal_turn")]


if __name__ == "__main__":
    print("one agent with everything:", check_distribution({"everything": ALL_TOOLS}))
    for name, info in check_distribution(AGENTS).items():
        print(f"  {name:10} {info['count']} tools  {'ok' if info['ok'] else 'TOO MANY'}")

    print("\ntool_choice by moment:")
    for moment in ("normal_turn", "must_produce_structured_output", "prerequisite_first"):
        print(f"  {moment:32} {tool_choice(moment)}")

    print("\nprerequisite sequence:", sequence_for_prerequisite())
    print("Leaving 'any' on inside an agent loop means Claude can never say")
    print("it is finished, because every turn is forced to call something.")
