"""1.1 Build a multi-tool agent loop.

The loop turns on stop_reason and nothing else.

Run it:  python ex_1_1_agent_loop.py
"""
import json

MAX_ROUNDS = 20          # a safety net, not the stopping rule


# ---------------------------------------------------------------- the tools
def calculator(expression):
    return {"result": eval(expression, {"__builtins__": {}})}


def web_search(query):
    return {"results": [f"(pretend search result for {query!r})"]}


TOOLS = {"calculator": calculator, "web_search": web_search}


# ---------------------------------------------------------------- START HERE
def agent(client, question):
    """Send, read stop_reason, run tools, append results, repeat."""
    messages = [{"role": "user", "content": question}]

    for _ in range(MAX_ROUNDS):
        reply = client.create(messages)

        if reply["stop_reason"] == "end_turn":                 # finished
            return "".join(b["text"] for b in reply["content"] if b["type"] == "text")

        if reply["stop_reason"] == "max_tokens":               # cut off, not finished
            raise RuntimeError("reply was truncated; raise max_tokens")

        if reply["stop_reason"] != "tool_use":
            raise RuntimeError("unexpected stop_reason: " + reply["stop_reason"])

        # Claude may ask for several tools at once. Run them all and return
        # them all in ONE user message, each matched by its tool_use_id.
        messages.append({"role": "assistant", "content": reply["content"]})
        results = []
        for block in reply["content"]:
            if block["type"] != "tool_use":
                continue
            try:
                output = TOOLS[block["name"]](**block["input"])
                results.append({"type": "tool_result", "tool_use_id": block["id"],
                                "content": json.dumps(output)})
            except Exception as exc:                            # a failure is still a result
                results.append({"type": "tool_result", "tool_use_id": block["id"],
                                "content": json.dumps({"error": str(exc)}),
                                "is_error": True})
        messages.append({"role": "user", "content": results})

    raise RuntimeError("hit the safety cap; inspect the transcript")


# ---------------------------------------------------------------- a fake Claude
class FakeClient:
    """Returns a scripted conversation so the loop can be run offline.
    Turn 1 asks for two tools at once; turn 2 finishes."""

    def __init__(self):
        self.turn = 0

    def create(self, messages):
        self.turn += 1
        if self.turn == 1:
            return {"stop_reason": "tool_use", "content": [
                {"type": "text", "text": "Let me check both."},      # text AND tools
                {"type": "tool_use", "id": "a", "name": "calculator",
                 "input": {"expression": "1250 * 0.15"}},
                {"type": "tool_use", "id": "b", "name": "web_search",
                 "input": {"query": "VAT rate"}}]}
        return {"stop_reason": "end_turn",
                "content": [{"type": "text", "text": "15% of 1250 is 187.5."}]}


if __name__ == "__main__":
    client = FakeClient()
    print(agent(client, "What is 15% of 1250?"))
    print(f"rounds used: {client.turn} (the cap of {MAX_ROUNDS} was never reached)")
