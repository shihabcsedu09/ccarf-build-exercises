# CCAR-F build exercises

Thirty small Python programs, one for each objective on the Claude Certified
Architect Foundations exam. Each one is a working answer to a build exercise,
written to be read in a couple of minutes and run in under a second.

They use the real Anthropic SDK. The tool schemas, the `messages.create` calls,
the `stop_reason` loop, the `tool_result` blocks, the Batches API, the Agent SDK
hook signatures, the `.mcp.json` files and the `CLAUDE.md` hierarchy are all the
real shapes, not simplified ones. What you read here is what you would write at
work.

## Running them

```bash
pip install anthropic
python run_all.py          # all thirty
python run_all.py 3        # domain 3 only
python run_all.py 5.5      # one exercise
python domain5_context/ex_5_5_calibrated_router.py
```

Python 3.9 or newer. One dependency: `anthropic`.

### Two modes, same code

| | |
|---|---|
| **No API key** (default) | Every call is answered from a reply recorded in the file. Free, offline, instant, and the same every time. |
| **`ANTHROPIC_API_KEY` set** | The same lines talk to Claude for real. |

```bash
python domain1_agentic/ex_1_1_agent_loop.py                     # offline
ANTHROPIC_API_KEY=sk-... python domain1_agentic/ex_1_1_agent_loop.py   # live
```

Nothing is faked except the network. Offline replies are built as genuine
`anthropic.types.Message` objects, so `reply.stop_reason`, `reply.content`,
`block.type`, `block.input` and `reply.usage` behave exactly as they do against
the live API. An exercise that reads `reply.stop_reason == "tool_use"` is
reading a real field either way. That is the point: you can learn the shape of
the API without a key, a bill, or a network.

Each file prints a banner saying which mode it ran in.

## `claude_helpers.py`

One small module at the repository root, shared by all thirty files.

| | |
|---|---|
| `get_client(script)` | A real `Anthropic()` when a key is set; otherwise a stand-in that replays `script`. |
| `recorded(*blocks)` | Builds a genuine SDK `Message` from the blocks below. Infers `stop_reason`. |
| `say("text")` | A real `TextBlock`. |
| `call(id, name, **args)` | A real `ToolUseBlock`, as Claude would return it. |
| `MODEL` | The model id every exercise uses. |
| `banner(title)` | Prints the title and the mode. |

Read it first — it is about eighty lines, and after it every other file reads
as ordinary API code.

## How each file is laid out

```python
"""2.1 Write tool descriptions that stop misrouting.

Real scenario: two sentences on the situation this comes from.

Run it:
    python ex_2_1_tool_descriptions.py                    offline
    ANTHROPIC_API_KEY=sk-... python ex_2_1_...py          real calls
"""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from claude_helpers import MODEL, banner, call, get_client, recorded, say

# ---------------------------------------------------------------- START HERE
# the tools, the prompt and the call that matter

# ---------------------------------------------------------------- recorded replies
# what Claude says when there is no key, as real SDK objects

if __name__ == "__main__":
    # prints the result that proves the point
```

Read from the `START HERE` marker. Everything below the recorded-replies line
exists only so the file runs without a key.

Fourteen of the thirty make no API call, because their subject is not a call:
where a `CLAUDE.md` loads from, what a `.mcp.json` does with `${VAR}`, when to
open plan mode, which failures are worth retrying. Those write and read real
files, run the real `claude` CLI, and print real config. Their banner says so.

## The thirty


### Domain 1 · Agentic architecture (27% of the exam)

| # | Exercise | What running it shows |
|---|---|---|
| 1.1 | [Build a Multi-Tool Agent Loop](domain1_agentic/ex_1_1_agent_loop.py) | the loop ends on `end_turn`, and two tool calls in one reply come back as two `tool_result` blocks in one user turn |
| 1.2 | [Build a Hub-and-Spoke Research Coordinator](domain1_agentic/ex_1_2_coordinator.py) | `tool_choice` forcing the plan into a schema, and a decomposition by named source that can never report geothermal |
| 1.3 | [Implement Context Passing with Structured Metadata](domain1_agentic/ex_1_3_context_passing.py) | "Write the report." against a subagent prompt carrying goal, findings and output shape |
| 1.4 | [Build a Prerequisite Gate for Financial Operations](domain1_agentic/ex_1_4_prerequisite_gate.py) | a refund blocked because identity was never verified, and a second blocked at the limit, on a run where the prompt alone did not hold |
| 1.5 | [Implement Agent SDK Hooks for Normalisation and Policy Enforcement](domain1_agentic/ex_1_5_hooks.py) | a `PostToolUse` hook cutting 8 fields to 5 and masking a card number, and a `PreToolUse` hook denying a refund over the limit |
| 1.6 | [Build a Multi-Pass Code Review Pipeline](domain1_agentic/ex_1_6_multi_pass_review.py) | three per-file calls, then one call across their findings that catches the defect no single file contains |
| 1.7 | [Implement Session Management Strategies](domain1_agentic/ex_1_7_sessions.py) | resume, fork and fresh start, and the stale snapshot a resume carries with it |

### Domain 2 · Tools and MCP (18% of the exam)

| # | Exercise | What running it shows |
|---|---|---|
| 2.1 | [Design Tool Descriptions That Eliminate Misrouting](domain2_tools_mcp/ex_2_1_tool_descriptions.py) | the same question routed to `get_customer` on 31-character descriptions and to `lookup_order` on 381-character ones |
| 2.2 | [Build Structured Error Responses for All Four Categories](domain2_tools_mcp/ex_2_2_structured_errors.py) | four error categories routed to four different next moves, and an empty search returned as success |
| 2.3 | [Configure Tool Distribution Across a Multi-Agent System](domain2_tools_mcp/ex_2_3_tool_distribution.py) | 18 tools cut to four role-shaped sets, all four values of `tool_choice`, and why `any` breaks an agent loop |
| 2.4 | [Configure MCP Servers with Scoping and Environment Variables](domain2_tools_mcp/ex_2_4_mcp_config.py) | a real `.mcp.json` written and read back, `${VAR}` expansion failing loudly, and a literal token caught in review |
| 2.5 | [Trace and Refactor a Deprecated Function Using Built-in Tools](domain2_tools_mcp/ex_2_5_trace_function.py) | a real temp repo searched with real grep and glob, and the alias chain followed to the call sites a name search misses |

### Domain 3 · Claude Code configuration (20% of the exam)

| # | Exercise | What running it shows |
|---|---|---|
| 3.1 | [Build a Multi-Level CLAUDE.md Configuration](domain3_claude_code/ex_3_1_claude_md_hierarchy.py) | real files on disk, which of them load for a given path, and why a personal rule never reaches the team |
| 3.2 | [Create Custom Commands and Skills](domain3_claude_code/ex_3_2_commands_skills.py) | a real command, skill and subagent with their frontmatter, and what separates the three |
| 3.3 | [Configure Path-Specific Rules with Glob Patterns](domain3_claude_code/ex_3_3_path_rules.py) | real `.claude/rules/*.md` files, the rules that load for three different paths, and what one root file costs |
| 3.4 | [Practice Plan Mode vs Direct Execution Decision-Making](domain3_claude_code/ex_3_4_execution_mode.py) | plan mode or straight in, decided on reversibility and whether the approach is settled, never on size |
| 3.5 | [Practice Iterative Refinement Techniques](domain3_claude_code/ex_3_5_refinement.py) | four situations, four different refinement moves, each one a real call |
| 3.6 | [Set Up a CI/CD Pipeline with Claude Code](domain3_claude_code/ex_3_6_ci_pipeline.py) | the non-interactive command built flag by flag, deny beating allow, and a real JSON envelope parsed |

### Domain 4 · Prompting and output (20% of the exam)

| # | Exercise | What running it shows |
|---|---|---|
| 4.1 | [Build an Explicit Criteria Code Review Prompt](domain4_prompting/ex_4_1_explicit_criteria.py) | a vague prompt flagging a TODO and inventing a severity word, and explicit criteria finding the false safety claim |
| 4.2 | [Build a Few-Shot Enhanced Extraction Prompt](domain4_prompting/ex_4_2_few_shot.py) | examples that leak a vendor name into every extraction, and examples that teach `null` instead |
| 4.3 | [Build a Structured Extraction Tool with JSON Schema](domain4_prompting/ex_4_3_structured_output.py) | the same document returning `null` under a nullable field and an invented PO number under a required one |
| 4.4 | [Build a Validation-Retry Loop for Document Extraction](domain4_prompting/ex_4_4_validation_retry.py) | a retry that fixes an arithmetic error and a swapped date, and a missing attachment that no retry can fix |
| 4.5 | [Design a Batch Processing Strategy](domain4_prompting/ex_4_5_batching.py) | a real Batches call with `custom_id`, two of ten results failing for different reasons, and the 12-hour submission interval a 36-hour promise allows |
| 4.6 | [Build a Multi-Pass Code Review System](domain4_prompting/ex_4_6_fresh_eyes.py) | the defect the writing session defends, found by a session that never saw the writing |

### Domain 5 · Context and reliability (15% of the exam)

| # | Exercise | What running it shows |
|---|---|---|
| 5.1 | [Build a Persistent Case Facts Context Manager](domain5_context/ex_5_1_case_facts.py) | a summary that says "a recent order" and a facts block that still says 247.83 on order #8891, asked at turn 30 |
| 5.2 | [Build an Escalation Decision Engine](domain5_context/ex_5_2_escalation.py) | five cases against the three real triggers, with frustration and self-reported confidence deliberately left out |
| 5.3 | [Build a Structured Error Propagation System](domain5_context/ex_5_3_error_propagation.py) | a timeout offering alternatives, a permission failure that no retry fixes, and an empty search reported as a finding |
| 5.4 | [Build a Context-Resilient Codebase Explorer](domain5_context/ex_5_4_context_resilience.py) | a run resumed from a manifest after a crash, and an idempotency key stopping a refund being paid twice |
| 5.5 | [Build a Confidence-Calibrated Review Router](domain5_context/ex_5_5_calibrated_router.py) | 90.6% overall hiding a 60% segment, and the same 0.99 score routed two different ways |
| 5.6 | [Build a Provenance-Preserving Synthesis Pipeline](domain5_context/ex_5_6_provenance.py) | the same claim written with and without its source fields, and a conflict annotated with both dates |

## Where the briefs come from

The exercise briefs are the Build Exercises published at
claudecertificationguide.com/learn. The solutions, the recorded replies and the
demonstrations in this repository are written here.

## Licence

Do what you like with these. They exist to be read while revising.
