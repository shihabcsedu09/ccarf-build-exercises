# Domain 1 · Agentic architecture

Worth about 27% of the exam. 7 exercises.

Run them all with `python ../run_all.py 1`.

## 1.1 Build a Multi-Tool Agent Loop

`ex_1_1_agent_loop.py` · Intermediate · about 45 minutes

Running it shows the loop ends on end_turn, and two tool calls in one reply come back as two results in one user turn.

What the exercise is meant to teach:

- How the agentic loop lifecycle works with the Messages API
- Why stop_reason is the authoritative signal for loop control
- How to handle tool_use and end_turn stop_reason values correctly
- How to append tool results to conversation history for multi-turn execution
- When safety iteration caps are appropriate versus inappropriate as stopping mechanisms

## 1.2 Build a Hub-and-Spoke Research Coordinator

`ex_1_2_coordinator.py` · Intermediate · about 60 minutes

Running it shows a decomposition by named source can never report geothermal; a decomposition by question finds it.

What the exercise is meant to teach:

- How hub-and-spoke architecture centralises all communication through a coordinator
- Why subagent isolation means every piece of context must be explicitly passed
- How to implement broad task decomposition that avoids the narrow decomposition failure
- How iterative refinement loops detect and fill coverage gaps
- Why tracing failures to the coordinator decomposition is the correct diagnostic approach

## 1.3 Implement Context Passing with Structured Metadata

`ex_1_3_context_passing.py` · Intermediate · about 50 minutes

Running it shows a structured finding keeps its source and confidence, and an agent without the Task tool cannot delegate whatever its prompt says.

What the exercise is meant to teach:

- Why the coordinator allowedTools must include Task (or Agent, its current name) to spawn subagents
- How to design structured metadata that separates content from source attribution
- Why context passing failures cause attribution errors in downstream agents
- How to spawn independent subagents in parallel for reduced latency
- The difference between fork_session and parallel Task tool invocation

## 1.4 Build a Prerequisite Gate for Financial Operations

`ex_1_4_prerequisite_gate.py` · Advanced · about 60 minutes

Running it shows five refund requests against the gates, and the six fields a handoff has to carry.

What the exercise is meant to teach:

- Why programmatic enforcement is required for financial operations instead of prompt-based guidance
- How prerequisite gates physically block tool execution until preconditions are met
- The difference between the 8% prompt failure rate and 0% gate failure rate
- How to implement structured handoff protocols with all required fields
- How multi-concern requests should be decomposed and handled in parallel

## 1.5 Implement Agent SDK Hooks for Normalisation and Policy Enforcement

`ex_1_5_hooks.py` · Advanced · about 60 minutes

Running it shows a post-tool hook cutting 8 fields to 5 and masking a card number, and a pre-tool hook refusing a refund over the limit.

What the exercise is meant to teach:

- The distinction between PostToolUse hooks (after execution, data normalisation) and PreToolUse hooks (before execution, policy enforcement)
- Why hooks provide deterministic guarantees that prompts cannot match
- How to normalise heterogeneous data formats from multiple MCP tools into a consistent schema
- How to implement threshold-based and prerequisite-based policy enforcement using pre-execution hooks
- The decision framework: hooks for 100% requirements, prompts for preferences

## 1.6 Build a Multi-Pass Code Review Pipeline

`ex_1_6_multi_pass_review.py` · Advanced · about 60 minutes

Running it shows one wide pass finds 2 defects, four narrow passes find 8, and only the fourth sees across files.

What the exercise is meant to teach:

- Why attention dilution produces inconsistent analysis depth across files in single-pass reviews
- How multi-pass architecture (per-item + cross-item) solves the structural attention allocation problem
- The difference between fixed sequential pipelines and dynamic adaptive decomposition
- Why batching without a cross-file integration pass still misses cross-cutting issues
- How to identify attention dilution artefacts: same pattern flagged in one file, approved in another

## 1.7 Implement Session Management Strategies

`ex_1_7_sessions.py` · Intermediate · about 45 minutes

Running it shows which of resume, fresh and fork each situation calls for.

What the exercise is meant to teach:

- The three session management options: resume, fork_session, and fresh start with summary injection
- Why resuming after file changes leads to the stale context problem
- How structured summary injection preserves knowledge without stale tool results
- When targeted re-analysis is more efficient than full re-exploration
- The difference between fork_session (divergent exploration) and resume (continuation)
- Claude Certified Architect
