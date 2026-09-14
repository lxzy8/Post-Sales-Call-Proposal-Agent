# AGENTS.md — Agent Guidelines & Repository Directives

## Repository Purpose
This repository implements an end-to-end prototype for an AI Engineer Intern assignment: **Post-Sales-Call Proposal Agent**.
It processes unstructured sales call transcripts, extracts structured requirements, queries local business knowledge (services, case studies, pricing rules) via function tools, validates outputs against deterministic business guardrails, generates proposal briefs and email drafts, and terminates strictly at a **Human Approval Gate**.

## Core OpenAI Agents SDK Architecture
- **Framework**: Official `openai-agents` SDK (`Agent`, `Runner`, `@function_tool`).
- **Runtime Execution**: The model genuinely decides when and which function tools to call during the `Runner.run_sync()` loop. Tools are registered as `@function_tool` callables.
- **No Direct Tool Bypass**: Production code does NOT bypass tool execution or directly call tool inner functions (`__wrapped__`). Tool invocations are managed exclusively by the `Runner` runtime.
- **CLI Entrypoint**: `run.py` - Runs the pipeline and outputs readable execution traces and stages.
- **Core Package**: `agent/`
  - `agent/schemas.py`: Pydantic schema models (`ProposalAnalysis`, `RequirementExtraction`, `BusinessKnowledgeLookupResult`, `ProposalBrief`, `ValidationResult`, `EmailDraft`, `WorkflowOutput`).
  - `agent/tools.py`: `@function_tool` definitions (`search_business_knowledge`, `get_service_details`, `get_case_studies`).
  - `agent/validation.py`: Deterministic guardrail validation verifying groundedness, pricing rules, timeline ambiguity, service offerings, and missing requirement detection.
  - `agent/agent.py`: `ProposalAgentWorkflow` coordinating `Agent` and `Runner.run_sync()`.
- **Data Knowledge Base**: `data/` (`company_profile.md`, `services.md`, `case_studies.md`, `pricing_guidelines.md`, `sales_call_transcript.txt`).
- **Tests**: `tests/` (`test_schema.py`, `test_validation.py`, `test_workflow.py`).
- **Evidence**: `evidence/` PNG screenshots illustrating real terminal execution.

## Model & Secret Configuration
- `OPENAI_MODEL`: Configurable via environment variable (defaults to `gpt-4o`).
- `OPENAI_API_KEY`: Read exclusively from environment variables.
- NEVER hardcode secrets in source files, READMEs, test fixtures, or committed evidence.

## Testing & Execution Commands
```bash
# Run CLI
python3 run.py

# Run Tests
PYTHONPATH=. python3 -m pytest
```
