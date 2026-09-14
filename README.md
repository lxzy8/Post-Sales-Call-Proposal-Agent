# Post-Sales-Call Proposal Agent — OpenAI Agents SDK Prototype

An operational workflow prototype for mid-market B2B service companies (50–300 employees) that converts unstructured sales call transcripts into grounded, verified proposal briefs and personalized follow-up email drafts using the **OpenAI Agents SDK**.

---

## 1. Operational Problem
For B2B digital consultancies and agencies, qualified sales calls happen daily, but converting conversations into actionable proposals takes hours of manual work:
- Reviewing call recordings/transcripts
- Extracting technical requirements, timelines, and budgets
- Checking internal service offerings and case studies
- Drafting proposal briefs and personalized follow-up emails

This delay causes sales momentum loss and leads to inconsistency in proposals.

---

## 2. Selected AI Capability
**OpenAI Agents API / Agents SDK (`agents`)**
- `Agent`: Agent definition with instructions, tools, and `output_type=ProposalAnalysis`.
- `Runner`: `Runner.run_sync()` execution loop managing tool selection and execution.
- `@function_tool`: Model-invoked tools for business knowledge lookup (`get_service_details`, `get_case_studies`, `search_business_knowledge`).
- Human Approval Gate before any external action.

---

## 3. Why the Pairing Makes Sense
Sales call transcripts contain high context but high ambiguity. Standard AI models tend to hallucinate missing details (e.g., guessing prices, promising unsupported features).

By pairing the **OpenAI Agents SDK** structured outputs with **deterministic programmatic validation rules** and **internal business knowledge files**, deterministic validation blocks unsupported pricing, services, timelines, and commitments from reaching the final draft without review.

---

## 4. Architecture & Logical Pipeline

```
[ Sales Transcript ]
         ↓
[ OpenAI Agent + Runner.run_sync() ]
         ↓
   (Agent decides tool call)
   ├──> [ get_service_details(...) ]
   ├──> [ get_case_studies(...) ]
   └──> [ search_business_knowledge(...) ]
         ↓
[ ProposalAnalysis (Structured Output) ]
         ↓
[ Deterministic Validation Guardrail ]
         ↓
[ Personalized Email Draft (DRAFT — NOT SENT) ]
         ↓
[ 🛑 HUMAN APPROVAL REQUIRED ]
```

---

## 5. Directory Structure
```
.
├── README.md
├── AGENTS.md
├── requirements.txt
├── .gitignore
├── run.py
├── agent/
│   ├── __init__.py
│   ├── agent.py
│   ├── schemas.py
│   ├── tools.py
│   └── validation.py
├── data/
│   ├── company_profile.md
│   ├── services.md
│   ├── case_studies.md
│   ├── pricing_guidelines.md
│   └── sales_call_transcript.txt
├── tests/
│   ├── test_schema.py
│   ├── test_validation.py
│   └── test_workflow.py
└── evidence/
    ├── 01_input.png
    ├── 02_agent_execution.png
    ├── 03_requirements.png
    ├── 04_knowledge_lookup.png
    ├── 05_validation.png
    ├── 06_proposal_brief.png
    ├── 07_email_draft.png
    └── 08_human_approval.png
```

---

## 6. Setup & Execution

### Setup & Pinned Dependencies
```bash
# Install pinned dependencies
pip install -r requirements.txt
```

### Environment Variables
```bash
export OPENAI_API_KEY="sk-proj-..."
export OPENAI_MODEL="gpt-4o"  # Optional, defaults to gpt-4o
```

### Run Workflow CLI
```bash
python3 run.py
```

### Run Test Suite
```bash
PYTHONPATH=. python3 -m pytest
```

---

## 7. Business Knowledge Base (`data/`)
- `company_profile.md`: Northstar Digital overview.
- `services.md`: Supported services (Website Redesign, CRM Integration, Lead Capture Automation, Web Analytics).
- `case_studies.md`: Historical case studies (Apex Logistics Consulting, Meridian Wealth Advisory).
- `pricing_guidelines.md`: Reference pricing & mandatory rule: if scope parameters are missing, output `"Pricing requires manual estimation."`

---

## 8. Guardrails & Operational Scenarios
The workflow undergoes deterministic validation across 6 critical operational scenarios (`tests/test_workflow.py`):

| Test Scenario | Scenario Description | Expected & Verified Behavior |
|---|---|---|
| **Test 1** | Normal complete sales call | Structured requirements extracted; proposal brief & email generated. |
| **Test 2** | Missing pricing parameters | Pricing strictly outputs `"Pricing requires manual estimation."` |
| **Test 3** | Missing critical requirement | Unresolved questions explicitly flagged in proposal brief under missing information. |
| **Test 4** | No matching case study | Agent explicitly reports no matching case study exists without hallucinating one. |
| **Test 5** | Ambiguous timeline | Timeline flagged as requiring confirmation. |
| **Test 6** | Unsupported service request | Unsupported service (e.g., custom AI triage or quantum crypto) flagged as not offered. |

---

## 9. Human Approval Gate
The workflow **NEVER** automatically sends an email or interacts with external email APIs. Every execution terminates at:
```
🛑 STATUS: HUMAN APPROVAL REQUIRED
The proposal brief and email draft have been generated and validated.
NO EXTERNAL EMAIL OR ACTION HAS BEEN AUTOMATICALLY EXECUTED.
```

---

## 10. Evidence / Screenshot Mapping (`evidence/`)
- `01_input.png`: Sample sales transcript input.
- `02_agent_execution.png`: OpenAI Agents SDK `Runner.run_sync()` trace & execution mode.
- `03_requirements.png`: Structured requirement extraction.
- `04_knowledge_lookup.png`: Business knowledge lookup & tool results.
- `05_validation.png`: Deterministic validation guardrail output.
- `06_proposal_brief.png`: Generated proposal brief.
- `07_email_draft.png`: Personalized email draft marked `DRAFT — NOT SENT`.
- `08_human_approval.png`: Explicit Human Approval Gate.
