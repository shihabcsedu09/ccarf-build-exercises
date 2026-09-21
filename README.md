# CCAR-F build exercises

Thirty small Python programs, one for each objective on the Claude Certified
Architect Foundations exam. Each one is a working answer to a build exercise,
written to be read in a couple of minutes and run in under a second.

Nothing here calls an API. Every exercise carries its own stub data and prints
a result that demonstrates the point it is making, so you can change a value
and watch the conclusion change with it.

## Running them

```bash
python run_all.py          # all thirty
python run_all.py 3        # domain 3 only
python run_all.py 5.5      # one exercise
python domain5_context/ex_5_5_calibrated_router.py
```

Python 3.8 or newer. No dependencies.

## How each file is laid out

```python
"""5.5 Build a confidence-calibrated review router.

Two sentences on the idea being tested.

Run it:  python ex_5_5_calibrated_router.py
"""

# ---------------------------------------------------------------- START HERE
def the_function_that_matters(...):
    ...

# ---------------------------------------------------------------- stubs
# fake clients and sample data, so the file runs offline

if __name__ == "__main__":
    # prints the result that proves the point
```

Read from the `START HERE` marker. Everything above it is the brief and
everything below the stubs line exists only so the file runs on its own.

## The thirty


### Domain 1 · Agentic architecture (27% of the exam)

| # | Exercise | What running it shows |
|---|---|---|
| 1.1 | [Build a Multi-Tool Agent Loop](domain1_agentic/ex_1_1_agent_loop.py) | the loop ends on end_turn, and two tool calls in one reply come back as two results in one user turn |
| 1.2 | [Build a Hub-and-Spoke Research Coordinator](domain1_agentic/ex_1_2_coordinator.py) | a decomposition by named source can never report geothermal; a decomposition by question finds it |
| 1.3 | [Implement Context Passing with Structured Metadata](domain1_agentic/ex_1_3_context_passing.py) | a structured finding keeps its source and confidence, and an agent without the Task tool cannot delegate whatever its prompt says |
| 1.4 | [Build a Prerequisite Gate for Financial Operations](domain1_agentic/ex_1_4_prerequisite_gate.py) | five refund requests against the gates, and the six fields a handoff has to carry |
| 1.5 | [Implement Agent SDK Hooks for Normalisation and Policy Enforcement](domain1_agentic/ex_1_5_hooks.py) | a post-tool hook cutting 8 fields to 5 and masking a card number, and a pre-tool hook refusing a refund over the limit |
| 1.6 | [Build a Multi-Pass Code Review Pipeline](domain1_agentic/ex_1_6_multi_pass_review.py) | one wide pass finds 2 defects, four narrow passes find 8, and only the fourth sees across files |
| 1.7 | [Implement Session Management Strategies](domain1_agentic/ex_1_7_sessions.py) | which of resume, fresh and fork each situation calls for |

### Domain 2 · Tools and MCP (18% of the exam)

| # | Exercise | What running it shows |
|---|---|---|
| 2.1 | [Design Tool Descriptions That Eliminate Misrouting](domain2_tools_mcp/ex_2_1_tool_descriptions.py) | a thin description scoring nothing on all five parts, and a full one scoring all five |
| 2.2 | [Build Structured Error Responses for All Four Categories](domain2_tools_mcp/ex_2_2_structured_errors.py) | each of the four error categories routed to a different next move, and an empty search reported as success |
| 2.3 | [Configure Tool Distribution Across a Multi-Agent System](domain2_tools_mcp/ex_2_3_tool_distribution.py) | a coordinator that cannot write, a researcher that cannot delegate, and the moment tool_choice has to force a call |
| 2.4 | [Configure MCP Servers with Scoping and Environment Variables](domain2_tools_mcp/ex_2_4_mcp_config.py) | a config failing loudly on a missing variable, and an audit catching a literal token in the file |
| 2.5 | [Trace and Refactor a Deprecated Function Using Built-in Tools](domain2_tools_mcp/ex_2_5_trace_function.py) | a grep that misses the call sites because of a rename, and the alias chain followed to the end |

### Domain 3 · Claude Code configuration (20% of the exam)

| # | Exercise | What running it shows |
|---|---|---|
| 3.1 | [Build a Multi-Level CLAUDE.md Configuration](domain3_claude_code/ex_3_1_claude_md_hierarchy.py) | which CLAUDE.md files load for a given path, who else sees each one, and why a personal rule never reaches the team |
| 3.2 | [Create Custom Commands and Skills](domain3_claude_code/ex_3_2_commands_skills.py) | where a command lives, when a personal one shadows the team's, and what makes a skill different from a slash command |
| 3.3 | [Configure Path-Specific Rules with Glob Patterns](domain3_claude_code/ex_3_3_path_rules.py) | the rules that load for three different paths, and what putting them all in the root file costs |
| 3.4 | [Practice Plan Mode vs Direct Execution Decision-Making](domain3_claude_code/ex_3_4_execution_mode.py) | plan mode or straight in, decided on whether the approach is settled rather than on size |
| 3.5 | [Practice Iterative Refinement Techniques](domain3_claude_code/ex_3_5_refinement.py) | four situations mapped to four different refinement moves |
| 3.6 | [Set Up a CI/CD Pipeline with Claude Code](domain3_claude_code/ex_3_6_ci_pipeline.py) | the non-interactive command, the deny list beating the allow list, and reading the JSON envelope |

### Domain 4 · Prompting and output (20% of the exam)

| # | Exercise | What running it shows |
|---|---|---|
| 4.1 | [Build an Explicit Criteria Code Review Prompt](domain4_prompting/ex_4_1_explicit_criteria.py) | a vague prompt reporting 4 findings and an explicit one reporting the 2 that are real |
| 4.2 | [Build a Few-Shot Enhanced Extraction Prompt](domain4_prompting/ex_4_2_few_shot.py) | an example set that leaks a vendor name into every extraction, and one that teaches null instead |
| 4.3 | [Build a Structured Extraction Tool with JSON Schema](domain4_prompting/ex_4_3_structured_output.py) | the same document returning null under a nullable field and an invented PO number under a required one |
| 4.4 | [Build a Validation-Retry Loop for Document Extraction](domain4_prompting/ex_4_4_validation_retry.py) | a retry that fixes an arithmetic error, and a missing attachment that no retry can fix |
| 4.5 | [Design a Batch Processing Strategy](domain4_prompting/ex_4_5_batching.py) | which workloads belong in a batch, and the submission interval a 36-hour promise allows |
| 4.6 | [Build a Multi-Pass Code Review System](domain4_prompting/ex_4_6_fresh_eyes.py) | the defect the writing session defends, and what a reported 0.9 has actually been worth |

### Domain 5 · Context and reliability (15% of the exam)

| # | Exercise | What running it shows |
|---|---|---|
| 5.1 | [Build a Persistent Case Facts Context Manager](domain5_context/ex_5_1_case_facts.py) | a summariser turning 187.43 into about $190 while the facts block keeps the exact figure |
| 5.2 | [Build an Escalation Decision Engine](domain5_context/ex_5_2_escalation.py) | five cases against the three real triggers, with frustration and self-reported confidence correctly ignored |
| 5.3 | [Build a Structured Error Propagation System](domain5_context/ex_5_3_error_propagation.py) | a transient failure recovering, a permanent one reported with its 118 partial rows, and an empty result reported as success |
| 5.4 | [Build a Context-Resilient Codebase Explorer](domain5_context/ex_5_4_context_resilience.py) | a crash-resume briefing rebuilt from a file, and 2400 lines of context saved by delegating |
| 5.5 | [Build a Confidence-Calibrated Review Router](domain5_context/ex_5_5_calibrated_router.py) | 96% overall hiding a 60% segment, and the same 0.96 score routed two different ways |
| 5.6 | [Build a Provenance-Preserving Synthesis Pipeline](domain5_context/ex_5_6_provenance.py) | attribution surviving a summarisation step, a conflict annotated with both dates, and an unsourced sentence cut |

## Where the briefs come from

The exercise briefs are the Build Exercises published at
claudecertificationguide.com/learn. The solutions, the stub data and the
demonstrations in this repository are written here.

## Licence

Do what you like with these. They exist to be read while revising.
