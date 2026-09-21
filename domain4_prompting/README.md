# Domain 4 · Prompting and output

Worth about 20% of the exam. 6 exercises.

Run them all with `python ../run_all.py 4`.

## 4.1 Build an Explicit Criteria Code Review Prompt

`ex_4_1_explicit_criteria.py` · Intermediate · about 45 minutes

Running it shows a vague prompt flagging a TODO and inventing a severity word, and explicit criteria finding the false safety claim.

What the exercise is meant to teach:

- Understand why vague instructions (be conservative, high-confidence only) fail in production prompts
- Design explicit categorical criteria that define what to flag and what to skip
- Calibrate severity levels using concrete code examples rather than prose descriptions
- Measure false positive rates and apply the trust recovery strategy of disabling problematic categories
- Recognise the hierarchy: explicit criteria first, confidence-based routing second

## 4.2 Build a Few-Shot Enhanced Extraction Prompt

`ex_4_2_few_shot.py` · Intermediate · about 45 minutes

Running it shows examples that leak a vendor name into every extraction, and examples that teach null instead.

What the exercise is meant to teach:

- Identify the three triggers for deploying few-shot examples: inconsistent formatting, ambiguous judgement calls, and empty fields for existing data
- Construct effective few-shot examples with reasoning, not just input-output pairs
- Use 2-4 targeted examples covering the specific failing scenarios
- Distinguish when few-shot examples are the right technique versus schema changes or validation loops
- Measure the impact of few-shot examples on empty field rates and format consistency

## 4.3 Build a Structured Extraction Tool with JSON Schema

`ex_4_3_structured_output.py` · Intermediate · about 45 minutes

Running it shows the same document returning null under a nullable field and an invented PO number under a required one.

What the exercise is meant to teach:

- Design JSON schemas with optional/nullable fields to prevent fabrication of missing data
- Understand the three tool_choice modes (auto, any, forced) and when to use each
- Recognise that tool_use eliminates syntax errors but not semantic errors
- Apply schema design patterns: unclear enum values, other + detail string, format normalisation

## 4.4 Build a Validation-Retry Loop for Document Extraction

`ex_4_4_validation_retry.py` · Advanced · about 60 minutes

Running it shows a retry that fixes an arithmetic error and a swapped date, and a missing attachment that no retry can fix.

What the exercise is meant to teach:

- Implement the retry-with-error-feedback pattern: original document + failed extraction + specific validation error
- Distinguish fixable errors (format, structural, mathematical) from unfixable errors (absent information)
- Design self-correction schemas with calculated_total vs stated_total and conflict_detected booleans
- Build systematic improvement loops using detected_pattern fields and dismissal tracking
- Understand the boundary between schema syntax errors (eliminated by tool_use) and semantic validation errors (require retry loops)

## 4.5 Design a Batch Processing Strategy

`ex_4_5_batching.py` · Intermediate · about 45 minutes

Running it shows a real Batches call with custom_id, two of ten results failing for different reasons, and the 12-hour submission interval a 36-hour promise allows.

What the exercise is meant to teach:

- Classify workflows as blocking (synchronous) or latency-tolerant (batch-eligible) based on latency requirements
- Use the Message Batches API with custom_id fields for request-response correlation
- Implement failure handling that resubmits only failed documents with targeted modifications
- Calculate batch submission frequency against SLA constraints accounting for the 24-hour processing window
- Apply the prompt refinement workflow: sample set testing before full batch submission

## 4.6 Build a Multi-Pass Code Review System

`ex_4_6_fresh_eyes.py` · Advanced · about 60 minutes

Running it shows the defect the writing session defends, found by a session that never saw the writing.

What the exercise is meant to teach:

- Understand why self-review in the same session retains reasoning context and is less effective than independent review
- Design multi-pass review architectures with per-file local analysis and cross-file integration passes
- Identify and mitigate attention dilution in large multi-file reviews
- Implement confidence-based routing with calibrated thresholds from labelled validation sets
- Distinguish uncalibrated raw confidence from calibrated thresholds suitable for automated routing
- Claude Certified Architect
