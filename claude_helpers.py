"""Shared plumbing, so every exercise can use the real Anthropic SDK.

Set ANTHROPIC_API_KEY and the exercises talk to Claude for real. Leave it
unset and you get a stand-in that replays a recorded reply instead.

Only the network is replaced. The request you build, the parameter names you
pass and the reply object you read are the real ones, and the reply is a
genuine anthropic.types.Message. So the code in each exercise is the code you
would ship; nothing is reshaped to make the demo work.
"""
import os

from anthropic import Anthropic
from anthropic.types import Message, TextBlock, ToolUseBlock, Usage

# Pin a dated snapshot in production. An alias can move under you, which is how
# a field's accuracy drops with no change to your prompt (objective 5.1).
MODEL = "claude-sonnet-4-6"


def live():
    """True when a real key is present, so an exercise can say which mode it ran in."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


# ---------------------------------------------------------------- recorded replies
def say(text):
    """One text block, the way Claude returns prose."""
    return TextBlock(type="text", text=text)


def call(tool_use_id, name, **arguments):
    """One tool_use block: Claude asking you to run a tool. The id is the receipt."""
    return ToolUseBlock(type="tool_use", id=tool_use_id, name=name, input=arguments)


def recorded(*blocks, **kwargs):
    """Build a genuine SDK Message, so offline code reads exactly like live code."""
    stop_reason = kwargs.pop("stop_reason", None)
    if stop_reason is None:
        # Claude sets tool_use whenever it asked for a tool, end_turn when finished.
        stop_reason = "tool_use" if any(b.type == "tool_use" for b in blocks) else "end_turn"
    return Message(
        id=kwargs.pop("id", "msg_recorded"),
        type="message",
        role="assistant",
        model=MODEL,
        stop_reason=stop_reason,
        stop_sequence=None,
        usage=Usage(input_tokens=kwargs.pop("input_tokens", 600),
                    output_tokens=kwargs.pop("output_tokens", 90)),
        content=list(blocks),
    )


# ---------------------------------------------------------------- offline stand-in
class _OfflineMessages(object):
    def __init__(self, owner):
        self._owner = owner

    def create(self, **request):
        """Same signature as the real client.messages.create, and it keeps the
        request so an exercise can show what was actually sent."""
        self._owner.requests.append(request)
        if not self._owner.script:
            raise RuntimeError("the recorded script ran out; add another reply")
        return self._owner.script.pop(0)


class _OfflineBatch(object):
    """Enough of the Message Batches API to run the batching exercise offline."""

    def __init__(self, owner):
        self._owner = owner
        self._batches = {}

    def create(self, requests):
        batch_id = "msgbatch_%02d" % (len(self._batches) + 1)
        self._batches[batch_id] = list(requests)
        self._owner.requests.append({"batch": batch_id, "count": len(requests)})
        return _Obj(id=batch_id, processing_status="in_progress",
                    request_counts=_Obj(processing=len(requests), succeeded=0, errored=0))

    def retrieve(self, batch_id):
        sent = self._batches[batch_id]
        failures = self._owner.batch_failures
        errored = sum(1 for r in sent if r["custom_id"] in failures)
        return _Obj(id=batch_id, processing_status="ended",
                    request_counts=_Obj(processing=0,
                                        succeeded=len(sent) - errored, errored=errored))

    def results(self, batch_id):
        for request in self._batches[batch_id]:
            reason = self._owner.batch_failures.get(request["custom_id"])
            if reason:
                yield _Obj(custom_id=request["custom_id"],
                           result=_Obj(type="errored", error=_Obj(type=reason)))
            else:
                yield _Obj(custom_id=request["custom_id"],
                           result=_Obj(type="succeeded", message=recorded(say("extracted"))))


class _Obj(object):
    """A tiny stand-in for the SDK's response objects, which use attributes."""

    def __init__(self, **fields):
        self.__dict__.update(fields)

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__,
                           ", ".join("%s=%r" % kv for kv in self.__dict__.items()))


class OfflineClient(object):
    """Stands in for anthropic.Anthropic() when there is no API key."""

    def __init__(self, script, batch_failures=None):
        self.script = list(script)
        self.requests = []
        self.batch_failures = batch_failures or {}
        self.messages = _OfflineMessages(self)
        self.messages.batches = _OfflineBatch(self)


def get_client(script=None, batch_failures=None):
    """A real client when a key is set, otherwise one that replays `script`."""
    if live():
        return Anthropic()
    return OfflineClient(script or [], batch_failures)


def banner(exercise, api=True):
    """One line at the top of the output saying what this run actually did."""
    if not api:
        mode = "no API calls: this one is about files, config and decisions"
    elif live():
        mode = "LIVE against the Anthropic API"
    else:
        mode = "offline, replaying a recorded reply"
    print("%s  [%s]" % (exercise, mode))
    print("-" * 72)
