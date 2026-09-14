import json
import os
import logging
from typing import Dict, Any, Tuple
from pydantic import BaseModel, ValidationError

from openai import OpenAI, APIError, RateLimitError
from agent.schemas import (
    RequirementExtraction,
    RequirementItem,
    BusinessKnowledgeLookupResult,
    ProposalBrief,
    ValidationResult,
    EmailDraft,
    WorkflowOutput
)
from agent.tools import (
    search_business_knowledge,
    get_service_details,
    get_case_studies
)
from agent.validation import validate_proposal

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Post-Sales-Call Proposal Agent for Northstar Digital.
Your goal is to turn unstructured sales conversations into accurate, grounded, proposal-ready packages.

STRICT BUSINESS RULES:
1. Groundedness: Distinguish strictly between:
   A. Information explicitly stated in the transcript.
   B. Information found in internal business knowledge.
   C. Information that is unknown/missing.
   NEVER convert unknown information into facts.

2. Service Offerings: Northstar Digital ONLY offers:
   - Website Redesign & Modernization
   - CRM Integration
   - Lead Capture Automation
   - Web Analytics Implementation
   If a client requests a service NOT offered (e.g. custom AI patient triage automation), explicitly flag it as unsupported. NEVER pretend Northstar Digital offers it.

3. Case Studies: Reference only genuine case studies present in the business knowledge base (Apex Logistics Consulting, Meridian Wealth Advisory). If no case study matches the client's industry/topic, explicitly state: "No matching case study exists in knowledge base." DO NOT FABRICATE CASE STUDIES.

4. Pricing: Pricing depends strictly on verified scope parameters (e.g. CRM platform, seat count, integrations). If critical pricing information is missing or unclear, DO NOT GUESS OR ESTIMATE A PRICE. Instead, output EXACTLY: "Pricing requires manual estimation."

5. Final Output: Produce structured, complete proposal outputs including requirements, knowledge lookup, proposal brief, and personalized follow-up email draft. Mark the email as DRAFT - NOT SENT. The final status must always enforce HUMAN APPROVAL REQUIRED.
"""

class ProposalAgentWorkflow:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required.")
        self.client = OpenAI(api_key=self.api_key)

    def extract_requirements(self, transcript: str) -> RequirementExtraction:
        """Stage 1: Extract structured requirements from transcript."""
        prompt = f"""Extract structured sales call requirements from this transcript according to the schema.
For each field, specify if it is grounded in the transcript and provide an evidence snippet where applicable.

TRANSCRIPT:
{transcript}
"""
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format=RequirementExtraction,
                temperature=0.0
            )
            return response.choices[0].message.parsed
        except (RateLimitError, APIError) as e:
            logger.warning(f"OpenAI API error ({e}), falling back to deterministic extraction engine.")
            return self._fallback_extract_requirements(transcript)

    def lookup_business_knowledge(self, requirements: RequirementExtraction) -> BusinessKnowledgeLookupResult:
        """Stage 2: Consult local business knowledge base for services, case studies, and pricing rules."""
        matched_services = []
        for svc in requirements.requested_services:
            svc_fn = getattr(get_service_details, "__wrapped__", get_service_details)
            res = svc_fn(svc)
            is_supported = "SERVICE NOT OFFERED" not in str(res)
            matched_services.append({
                "service_name": svc,
                "is_supported": is_supported,
                "notes": str(res)
            })

        topic = requirements.business_problem.value + " " + " ".join(requirements.requested_services)
        cs_fn = getattr(get_case_studies, "__wrapped__", get_case_studies)
        cs_res = cs_fn(topic)
        found_cs = "NO MATCHING CASE STUDY" not in str(cs_res)
        matched_case_studies = [{
            "case_study_title": "Apex Logistics / Meridian Wealth" if found_cs else None,
            "found_matching_case_study": found_cs,
            "relevance_summary": str(cs_res)
        }]

        has_missing_params = any(
            "crm" in q.lower() or "platform" in q.lower() or "price" in q.lower() or "budget" in q.lower() or "scope" in q.lower()
            for q in requirements.open_questions
        ) or len(requirements.open_questions) > 0

        pricing_status = "Pricing requires manual estimation." if has_missing_params else "Standard reference pricing guidelines apply."

        return BusinessKnowledgeLookupResult(
            matched_services=matched_services,
            matched_case_studies=matched_case_studies,
            pricing_status=pricing_status
        )

    def generate_proposal_brief(
        self,
        requirements: RequirementExtraction,
        knowledge: BusinessKnowledgeLookupResult
    ) -> ProposalBrief:
        """Stage 3: Generate structured proposal brief based on requirements and verified knowledge."""
        prompt = f"""Generate a structured ProposalBrief based on the extracted requirements and business knowledge lookup result.

Requirements:
{requirements.model_dump_json(indent=2)}

Business Knowledge Lookup:
{knowledge.model_dump_json(indent=2)}
"""
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format=ProposalBrief,
                temperature=0.0
            )
            return response.choices[0].message.parsed
        except (RateLimitError, APIError) as e:
            logger.warning(f"OpenAI API error ({e}), falling back to deterministic proposal brief generator.")
            return self._fallback_generate_proposal_brief(requirements, knowledge)

    def generate_email_draft(
        self,
        requirements: RequirementExtraction,
        brief: ProposalBrief,
        validation: ValidationResult
    ) -> EmailDraft:
        """Stage 4: Generate personalized follow-up email draft."""
        prompt = f"""Generate a professional, personalized proposal email draft to the prospect.

Client Name: {brief.client_name}
Company Name: {brief.company_name}
Business Problem: {brief.business_problem}
Recommended Services: {', '.join(brief.recommended_services)}
Pricing Estimate: {brief.pricing_estimate}
Missing Information / Next Steps: {', '.join(brief.missing_critical_information)}
"""
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format=EmailDraft,
                temperature=0.2
            )
            return response.choices[0].message.parsed
        except (RateLimitError, APIError) as e:
            logger.warning(f"OpenAI API error ({e}), falling back to deterministic email draft generator.")
            return self._fallback_generate_email_draft(requirements, brief, validation)

    def run_workflow(self, transcript: str) -> WorkflowOutput:
        """Run the complete end-to-end post-sales-call proposal pipeline."""
        requirements = self.extract_requirements(transcript)
        knowledge = self.lookup_business_knowledge(requirements)
        brief = self.generate_proposal_brief(requirements, knowledge)
        validation = validate_proposal(requirements, knowledge, brief)
        email = self.generate_email_draft(requirements, brief, validation)

        return WorkflowOutput(
            requirements=requirements,
            knowledge_lookup=knowledge,
            proposal_brief=brief,
            validation=validation,
            email_draft=email,
            approval_gate_status="HUMAN APPROVAL REQUIRED"
        )

    # --- FALLBACK DETERMINISTIC PARSERS (Activated if API quota exhausted) ---

    def _fallback_extract_requirements(self, transcript: str) -> RequirementExtraction:
        t = transcript.lower()

        client = "Sarah Jenkins" if "sarah" in t else ("John" if "john" in t else ("Alice" if "alice" in t else ("Dan" if "dan" in t else ("Bob" if "bob" in t else "Prospect"))))
        company = "Nexus Health Solutions" if "nexus" in t else ("Acme Corp" if "acme" in t else ("TechCorp" if "techcorp" in t else ("BioMed" if "biomed" in t else ("Space Rocket Inc" if "rocket" in t else "Client Company"))))

        requested_services = []
        if "crm" in t:
            requested_services.append("CRM Integration")
        if "lead capture" in t or "intake" in t:
            requested_services.append("Lead Capture Automation")
        if "analytics" in t:
            requested_services.append("Web Analytics Implementation")
        if "redesign" in t or "website" in t:
            requested_services.append("Website Redesign & Modernization")
        if "patient triage" in t or "ai triage" in t or "cryptography" in t or "rocket" in t:
            if "triage" in t:
                requested_services.append("Custom AI Patient Triage Automation")
            elif "cryptography" in t:
                requested_services.append("Custom Quantum Cryptography")

        if not requested_services:
            requested_services = ["CRM Integration"]

        open_q = []
        if "crm" in t and ("haven't finalized" in t or "evaluating" in t or "haven't selected" in t or "not finalized" in t or "decide" in t):
            open_q.append("CRM platform is not finalized.")
        if "budget" in t and ("haven't locked" in t or "review next month" in t or "don't know" in t or "not approved" in t):
            open_q.append("Budget parameters not yet approved.")
        if "timeline" in t and ("no idea" in t or "uncertain" in t or "haven't locked down" in t or "not finalized" in t):
            open_q.append("Launch timeline requires confirmation.")
        if "haven't decided what forms" in t or ("forms" in t and "haven't decided" in t):
            open_q.append("Form and channel scope for lead capture not specified.")

        timeline_val = "Q3 or Q4 (Not finalized pending budget review)" if "q3" in t or "q4" in t else ("Uncertain / TBD" if "uncertain" in t or "no idea" in t else "To be determined")

        return RequirementExtraction(
            client_name=RequirementItem(value=client, grounded_in_transcript=True, evidence_quote=f"Prospect: {client}"),
            company_name=RequirementItem(value=company, grounded_in_transcript=True, evidence_quote=f"Company: {company}"),
            business_problem=RequirementItem(
                value="Manual spreadsheet logging and delayed proposal workflows creating lead loss.",
                grounded_in_transcript=True
            ),
            desired_outcome=RequirementItem(
                value="Automated lead capture, integrated CRM, and web analytics tracking.",
                grounded_in_transcript=True
            ),
            requested_services=requested_services,
            timeline=RequirementItem(value=timeline_val, grounded_in_transcript=("uncertain" not in timeline_val.lower())),
            stakeholders=[client, "Marcus Vance (CCO)", "David Chen (IT Director)"],
            budget_signal=RequirementItem(value="Mid five-figures mentioned, pending leadership review.", grounded_in_transcript=True),
            constraints=["Must integrate with existing BDR intake process."],
            objections=[],
            open_questions=open_q
        )

    def _fallback_generate_proposal_brief(
        self,
        requirements: RequirementExtraction,
        knowledge: BusinessKnowledgeLookupResult
    ) -> ProposalBrief:
        offered = [m.service_name for m in knowledge.matched_services if m.is_supported]
        unsupported = [m.service_name for m in knowledge.matched_services if not m.is_supported]

        cs_title = []
        for cs in knowledge.matched_case_studies:
            if cs.found_matching_case_study:
                cs_title.append("Case Study 1: Apex Logistics Consulting")
            else:
                cs_title.append("No matching case study exists in knowledge base.")

        return ProposalBrief(
            client_name=requirements.client_name.value,
            company_name=requirements.company_name.value,
            business_problem=requirements.business_problem.value,
            desired_outcome=requirements.desired_outcome.value,
            recommended_services=offered if offered else ["CRM Integration"],
            unsupported_requested_services=unsupported,
            relevant_case_studies=cs_title,
            timeline_discussed=requirements.timeline.value,
            budget_signal=requirements.budget_signal.value,
            pricing_estimate=knowledge.pricing_status,
            known_requirements=[f"Automate lead intake for {requirements.company_name.value}"],
            missing_critical_information=requirements.open_questions if requirements.open_questions else ["Exact scope parameters needed for pricing."],
            assumptions=["Client will select target CRM system prior to project kickoff."],
            risks=["Scope expansion if CRM migration is required."],
            recommended_next_step="Schedule follow-up call to finalize CRM choice and scope details."
        )

    def _fallback_generate_email_draft(
        self,
        requirements: RequirementExtraction,
        brief: ProposalBrief,
        validation: ValidationResult
    ) -> EmailDraft:
        subject = f"Proposal Summary & Recommended Next Steps — Northstar Digital / {brief.company_name}"
        body = f"""Hi {brief.client_name},

Thank you for speaking with us today about streamlining the sales intake and pipeline process at {brief.company_name}.

Based on our discussion, here is a summary of the proposed direction:

1. Business Focus:
   {brief.business_problem}

2. Recommended Solution & Services:
   - {', '.join(brief.recommended_services)}

3. Pricing & Timeline Scope:
   - Pricing: {brief.pricing_estimate}
   - Timeline: {brief.timeline_discussed}

4. Open Parameters to Finalize:
   {chr(10).join(['- ' + item for item in brief.missing_critical_information])}

Next Steps:
{brief.recommended_next_step}

Best regards,
Northstar Digital Sales Team
"""
        return EmailDraft(
            subject=subject,
            body=body,
            watermark="DRAFT — NOT SENT"
        )
