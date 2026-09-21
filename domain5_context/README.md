# Domain 5 · Context and reliability

Worth about 15% of the exam. 6 exercises.

Run them all with `python ../run_all.py 5`.

## 5.1 Build a Persistent Case Facts Context Manager

`ex_5_1_case_facts.py` · Intermediate · about 45 minutes

Running it shows a summary that says "a recent order" and a facts block that still says 247.83 on order #8891, asked at turn 30.

What the exercise is meant to teach:

- Implement the persistent case facts block pattern to protect transactional data from summarisation
- Trim verbose tool results to relevant fields before they accumulate in context
- Recognise and mitigate the progressive summarisation trap for numerical values, dates, and identifiers
- Apply the lost-in-the-middle mitigation by placing key findings at the beginning of aggregated inputs
- Understand that the Claude API is stateless and each request must include complete conversation history

## 5.2 Build an Escalation Decision Engine

`ex_5_2_escalation.py` · Intermediate · about 40 minutes

Running it shows five cases against the three real triggers, with frustration and self-reported confidence deliberately left out.

What the exercise is meant to teach:

- Implement the three valid escalation triggers: explicit human request, policy exceptions/gaps, and inability to progress
- Identify and avoid the two unreliable triggers: sentiment-based escalation and self-reported confidence scores
- Handle the frustration nuance: frustrated customer with resolvable issue vs explicit human request
- Design ambiguous customer matching that requests additional identifiers rather than selecting heuristically
- Add explicit escalation criteria with few-shot examples to system prompts as the proportionate first response

## 5.3 Build a Structured Error Propagation System

`ex_5_3_error_propagation.py` · Advanced · about 50 minutes

Running it shows a timeout offering alternatives, a permission failure that no retry fixes, and an empty search reported as a finding.

What the exercise is meant to teach:

- Design structured error context with the four required elements: failure type, attempted action, partial results, and alternative approaches
- Distinguish access failures (timeout, connection error) from valid empty results (successful query, no matches)
- Identify and avoid the two anti-patterns: silent suppression and workflow termination
- Implement local retry logic for transient failures before propagating to the coordinator
- Add coverage annotations to synthesis output for transparency about information gaps

## 5.4 Build a Context-Resilient Codebase Explorer

`ex_5_4_context_resilience.py` · Advanced · about 60 minutes

Running it shows a run resumed from a manifest after a crash, and an idempotency key stopping a refund being paid twice.

What the exercise is meant to teach:

- Recognise context degradation as an attention quality problem, not a token limit problem
- Implement scratchpad files to persist key findings outside the conversation context
- Use subagent delegation for context isolation, not just parallelisation
- Design crash recovery via structured state manifests for session resilience
- Apply summary injection between exploration phases to prevent cold start duplication

## 5.5 Build a Confidence-Calibrated Review Router

`ex_5_5_calibrated_router.py` · Advanced · about 50 minutes

Running it shows 90.6% overall hiding a 60% segment, and the same 0.99 score routed two different ways.

What the exercise is meant to teach:

- Recognise the aggregate metrics trap: 97% overall accuracy can hide 40% error rates on specific document types
- Implement accuracy tracking broken down by document type AND field segment
- Calibrate raw confidence scores using labelled validation sets to produce reliable routing thresholds
- Design stratified random sampling that includes high-confidence extractions for ongoing verification
- Prioritise limited reviewer capacity on the highest-uncertainty items with dynamic queue ordering

## 5.6 Build a Provenance-Preserving Synthesis Pipeline

`ex_5_6_provenance.py` · Advanced · about 60 minutes

Running it shows the same claim written with and without its source fields, and a conflict annotated with both dates.

What the exercise is meant to teach:

- Design structured claim-source mappings with claim, source URL, document name, excerpt, and publication date
- Preserve attribution through multi-step synthesis pipelines without loss during summarisation
- Handle conflicting sources by annotating both values rather than arbitrarily selecting one
- Use temporal awareness (publication dates) to distinguish trends from contradictions
- Apply content-appropriate rendering: tables for financial data, prose for news, lists for technical findings
- Claude Certified Architect
