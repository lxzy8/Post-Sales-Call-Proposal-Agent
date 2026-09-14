# AGENTS.md — Agent Guidelines & Repository Directives

## Repository Purpose
This repository implements an end-to-end prototype for an AI Engineer Intern assignment: **Post-Sales-Call Proposal Agent**.
It processes unstructured sales call transcripts, extracts structured requirements, queries local business knowledge (services, case studies, pricing rules), validates outputs against business guardrails, generates proposal briefs and email drafts, and terminates strictly at a **Human Approval Gate**.

## Architecture Overview
- **CLI Entrypoint**: `run.py` - Runs the pipeline and outputs readable terminal steps.
- **Core Package**: `agent/`
  - `agent/schemas.py`: Pydantic schema models for structured outputs (`RequirementExtraction`, `BusinessKnowledgeLookupResult`, `ProposalBrief`, `ValidationResult`, `EmailDraft`, `WorkflowOutput`).
  - `agent/tools.py`: Business knowledge lookup tools (`search_business_knowledge`, `get_service_details`, `get_case_studies`).
  - `agent/validation.py`: Programmatic guardrail validation verifying groundedness, pricing rules, timeline ambiguity, service offerings, and missing requirement detection.
  - `agent/agent.py`: Agentic workflow coordinator built using `openai-agents` / OpenAI API structured outputs.
- **Data Knowledge Base**: `data/` (`company_profile.md`, `services.md`, `case_studies.md`, `pricing_guidelines.md`, `sales_call_transcript.txt`).
- **Tests**: `tests/` (`test_schema.py`, `test_validation.py`, `test_workflow.py`).
- **Evidence**: `evidence/` PNG screenshots illustrating execution.

## Coding Conventions
- Use Python 3.12+ with typing hints and Pydantic v2 schemas.
- Strictly ground claims in transcript or business knowledge files. Never guess prices or hallucinate unsupported services/case studies.
- Always output "Pricing requires manual estimation." when scope or CRM parameters are missing.
- Keep tool interfaces minimal and cleanly separated.

## How to Run Workflow
```bash
export OPENAI_API_KEY="your-api-key"
python3 run.py
```

## How to Run Tests
```bash
PYTHONPATH=. python3 -m pytest
```

## Secret-Handling Rules
- Read `OPENAI_API_KEY` exclusively from environment variables.
- NEVER hardcode secrets in source files, READMEs, test fixtures, or committed evidence.
- Always maintain `.gitignore` ignoring `.env`, `*.env`, and virtual environments.

## Acceptance Criteria
- Project installs clean dependencies (`requirements.txt`).
- Reads `OPENAI_API_KEY` from environment.
- Processes sales transcripts into structured schemas.
- Flags missing information and unsupported services.
- Never sends email automatically (ends at `HUMAN APPROVAL REQUIRED`).
- Comprehensive unit and integration test coverage.
