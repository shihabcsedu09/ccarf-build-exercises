# Domain 2 · Tools and MCP

Worth about 18% of the exam. 5 exercises.

Run them all with `python ../run_all.py 2`.

## 2.1 Design Tool Descriptions That Eliminate Misrouting

`ex_2_1_tool_descriptions.py` · Beginner · about 30 minutes

Running it shows a thin description scoring nothing on all five parts, and a full one scoring all five.

What the exercise is meant to teach:

- Understand that tool descriptions are the primary mechanism LLMs use for tool selection
- Write production-grade descriptions with purpose, inputs, examples, edge cases, and boundaries
- Diagnose misrouting caused by ambiguous or overlapping descriptions
- Identify system prompt conflicts that override well-written tool descriptions

## 2.2 Build Structured Error Responses for All Four Categories

`ex_2_2_structured_errors.py` · Intermediate · about 45 minutes

Running it shows each of the four error categories routed to a different next move, and an empty search reported as success.

What the exercise is meant to teach:

- Implement structured error responses with errorCategory, isRetryable, and description metadata
- Distinguish between access failures (isError: true) and valid empty results (isError: false)
- Categorise tool failures into transient, validation, business, and permission types
- Build agent recovery logic that takes different actions based on error metadata

## 2.3 Configure Tool Distribution Across a Multi-Agent System

`ex_2_3_tool_distribution.py` · Intermediate · about 45 minutes

Running it shows a coordinator that cannot write, a researcher that cannot delegate, and the moment tool_choice has to force a call.

What the exercise is meant to teach:

- Scope tools to agent roles using the 4-5 tools per agent guideline
- Implement scoped cross-role tools to avoid coordinator round-trip latency
- Configure tool_choice modes (auto, any, forced) for different workflow requirements
- Apply least-privilege tool design by replacing generic tools with constrained alternatives
- Verify that tool distribution prevents cross-role misuse in multi-agent systems

## 2.4 Configure MCP Servers with Scoping and Environment Variables

`ex_2_4_mcp_config.py` · Beginner · about 30 minutes

Running it shows a config failing loudly on a missing variable, and an audit catching a literal token in the file.

What the exercise is meant to teach:

- Configure project-level MCP servers in .mcp.json for team-wide sharing
- Use environment variable expansion to keep credentials out of version control
- Distinguish between project-level and user-level MCP configuration scoping
- Expose MCP resources to reduce unnecessary exploratory tool calls
- Write enhanced MCP tool descriptions that compete with built-in tool descriptions

## 2.5 Trace and Refactor a Deprecated Function Using Built-in Tools

`ex_2_5_trace_function.py` · Intermediate · about 30 minutes

Running it shows a grep that misses the call sites because of a rename, and the alias chain followed to the end.

What the exercise is meant to teach:

- Apply Grep for content search and Glob for path matching in the correct sequence
- Use incremental codebase discovery instead of reading all files upfront
- Select Edit as the primary modification tool and widen the anchor (or use replace_all) when Edit reports a non-unique match
- Trace function usage across wrapper modules and barrel files
- Follow the Grep-then-Glob pattern for finding callers and their test files
- Claude Certified Architect
