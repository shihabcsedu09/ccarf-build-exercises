# Domain 3 · Claude Code configuration

Worth about 20% of the exam. 6 exercises.

Run them all with `python ../run_all.py 3`.

## 3.1 Build a Multi-Level CLAUDE.md Configuration

`ex_3_1_claude_md_hierarchy.py` · Beginner · about 30 minutes

Running it shows real files on disk, which of them load for a given path, and why a personal rule never reaches the team.

What the exercise is meant to teach:

- Understand the three-level CLAUDE.md hierarchy (user, project, directory) and when to use each
- Configure modular project standards using @ path imports
- Use .claude/rules/ for topic-specific rule files
- Diagnose configuration scoping issues with the /memory command
- Identify root cause when a new team member does not receive instructions

## 3.2 Create Custom Commands and Skills

`ex_3_2_commands_skills.py` · Intermediate · about 30 minutes

Running it shows a real command, skill and subagent with their frontmatter, and what separates the three.

What the exercise is meant to teach:

- Distinguish between project-scoped and user-scoped command locations
- Configure SKILL.md frontmatter with context: fork, allowed-tools, and argument-hint
- Understand when to use skills vs CLAUDE.md for conventions vs workflows
- Verify scoping boundaries between shared and personal configuration
- Apply the context: fork pattern to isolate verbose output from the main conversation

## 3.3 Configure Path-Specific Rules with Glob Patterns

`ex_3_3_path_rules.py` · Intermediate · about 30 minutes

Running it shows real .claude/rules/*.md files, the rules that load for three different paths, and what one root file costs.

What the exercise is meant to teach:

- Write YAML frontmatter with glob patterns for conditional rule loading
- Apply path-specific rules to files spread across many directories
- Understand why path-specific rules are more token-efficient than root CLAUDE.md
- Distinguish when to use path-specific rules vs directory-level CLAUDE.md
- Verify conditional loading behaviour using the /context command

## 3.4 Practice Plan Mode vs Direct Execution Decision-Making

`ex_3_4_execution_mode.py` · Intermediate · about 45 minutes

Running it shows plan mode or straight in, decided on reversibility and whether the approach is settled, never on size.

What the exercise is meant to teach:

- Apply the decision framework for choosing plan mode vs direct execution based on task ambiguity
- Execute the hybrid plan-then-execute pattern for multi-file migrations
- Use the Explore subagent to isolate verbose discovery output from the main conversation
- Recognise complexity upfront rather than waiting for it to emerge
- Distinguish task difficulty from task ambiguity when selecting execution mode

## 3.5 Practice Iterative Refinement Techniques

`ex_3_5_refinement.py` · Beginner · about 30 minutes

Running it shows four situations, four different refinement moves, each one a real call.

What the exercise is meant to teach:

- Apply the technique hierarchy: concrete examples over prose for inconsistent interpretation
- Use test-driven iteration to provide unambiguous feedback via test failures
- Deploy the interview pattern for unfamiliar domains to surface hidden requirements
- Distinguish when to batch feedback vs iterate sequentially based on issue interdependence
- Recognise that 2-3 well-chosen examples are sufficient for pattern generalisation

## 3.6 Set Up a CI/CD Pipeline with Claude Code

`ex_3_6_ci_pipeline.py` · Advanced · about 45 minutes

Running it shows the non-interactive command built flag by flag, deny beating allow, and a real JSON envelope parsed.

What the exercise is meant to teach:

- Use the -p flag for non-interactive Claude Code execution in CI pipelines
- Configure structured JSON output with --output-format json and --json-schema
- Implement session context isolation between code generation and review
- Set up incremental review to eliminate duplicate findings across runs
- Provide project context via CLAUDE.md for CI-invoked Claude Code
- Claude Certified Architect
