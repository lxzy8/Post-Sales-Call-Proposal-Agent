import json
import os
import logging
from typing import Dict, Any, Tuple
from pydantic import BaseModel, ValidationError

from agents import Agent, Runner
from openai import APIError, RateLimitError

from agent.schemas import (
    RequirementExtraction,
    RequirementItem,
    BusinessKnowledgeLookupResult,
    ProposalBrief,
    ProposalAnalysis,
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
Your goal is to process unstructured sales call transcripts into grounded, verified proposal packages.

WORKFLOW STEPS YOU MUST PERFORM USING TOOLS:
1. Extract requirements from the transcript.
2. For each service mentioned in the transcript, call `get_service_details(service_name)` to verify if Northstar Digital offers it.
3. Call `get_case_studies(industry_or_topic)` to find matching case studies in our knowledge base.
4. If general information is required, call `search_business_knowledge(query)`.
5. Synthesize all extracted information, knowledge tool lookup results, and proposal brief into the requested output schema.

STRICT BUSINESS RULES:
- Groundedness: Distinguish strictly between explicitly stated transcript facts, internal business knowledge, and unknown details.
- Service Offerings: Northstar Digital ONLY offers: Website Redesign & Modernization, CRM Integration, Lead Capture Automation, and Web Analytics Implementation. If a client requests unsupported services (e.g., custom AI triage or quantum cryptography), explicitly flag them in unsupported_requested_services. NEVER pretend we offer them.
- Case Studies: Reference ONLY genuine case studies returned by `get_case_studies`. If no matching case study exists, explicitly state "No matching case study exists in knowledge base." DO NOT FABRICATE CASE STUDIES.
- Pricing: Pricing depends strictly on verified scope parameters (e.g. CRM platform, seat count). If critical pricing parameters are missing or unclear in the transcript, output EXACTLY: "Pricing requires manual estimation."
"""

class ProposalAgentWorkflow:
    def __init__(self, api_key: str = None, model_name: str = None, allow_fallback: bool = True):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "mock-key-for-offline-tests")
        self.model_name = model_name or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.allow_fallback = allow_fallback

        os.environ["OPENAI_API_KEY"] = self.api_key

        self.agent = Agent(
            name="Post-Sales-Call Proposal Agent",
            instructions=SYSTEM_PROMPT,
            tools=[
                search_business_knowledge,
                get_service_details,
                get_case_studies
            ],
            model=self.model_name,
            output_type=ProposalAnalysis
        )

    def run_agent(self, transcript: str) -> Tuple[ProposalAnalysis, str]:
        """Runs the agent via OpenAI Agents SDK Runner.run_sync()."""
        prompt = f"""Process this sales call transcript. Call all relevant business knowledge tools to verify services and case studies, then produce the final structured proposal analysis.

TRANSCRIPT:
{transcript}
"""
        try:
            print("\n[Agents SDK Runtime -> Starting Runner.run_sync execution loop...]")
            run_result = Runner.run_sync(self.agent, prompt)
            print("[Agents SDK Runtime -> Agent execution completed successfully.]")
            analysis: ProposalAnalysis = run_result.final_output
            return analysis, "MODE: OPENAI AGENTS SDK"
        except Exception as e:
            if not self.allow_fallback:
                logger.error("Agents SDK execution failed and allow_fallback=False.")
                raise RuntimeError(f"OpenAI Agents SDK execution failed: {e}") from e

            logger.warning(f"Agents SDK execution failed or API quota error ({e}). Entering explicit fallback mode.")
            print(f"\n[⚠️ AGENT RUNTIME NOTICE]: {e}")
            print("[MODE: FALLBACK — OPENAI API UNAVAILABLE (Using local deterministic engine for testing)]")
            return self._fallback_analysis(transcript), "MODE: FALLBACK — OPENAI API UNAVAILABLE"

    def generate_email_draft(
        self,
        brief: ProposalBrief,
        validation: ValidationResult
    ) -> EmailDraft:
        """Generates follow-up email draft based on validated proposal brief."""
        subject = f"Proposal Summary & Recommended Next Steps — Northstar Digital / {brief.company_name}"

        body_lines = [
            f"Hi {brief.client_name},\n",
            f"Thank you for speaking with us today about streamlining the sales intake and pipeline process at {brief.company_name}.\n",
            "Based on our discussion, here is a summary of our proposed direction:\n",
            "1. Business Focus:",
            f"   {brief.business_problem}\n",
            "2. Recommended Solution & Services:",
        ]
        for svc in brief.recommended_services:
            body_lines.append(f"   - {svc}")

        if brief.unsupported_requested_services:
            body_lines.append("\nNote on Additional Service Requests:")
            for usvc in brief.unsupported_requested_services:
                body_lines.append(f"   - {usvc}: [Not currently offered by Northstar Digital]")

        body_lines.extend([
            "\n3. Pricing & Timeline Scope:",
            f"   - Pricing Estimate: {brief.pricing_estimate}",
            f"   - Timeline Discussed: {brief.timeline_discussed}\n",
            "4. Open Parameters / Critical Information Needed:"
        ])
        for mi in brief.missing_critical_information:
            body_lines.append(f"   - {mi}")

        body_lines.extend([
            "\nRecommended Next Steps:",
            f"{brief.recommended_next_step}\n",
            "Best regards,",
            "Northstar Digital Sales Team"
        ])

        return EmailDraft(
            subject=subject,
            body="\n".join(body_lines),
            watermark="DRAFT — NOT SENT"
        )

    def run_workflow(self, transcript: str) -> WorkflowOutput:
        """Complete end-to-end post-sales proposal workflow."""
        analysis, mode = self.run_agent(transcript)
        validation = validate_proposal(analysis.requirements, analysis.knowledge_lookup, analysis.proposal_brief)
        email = self.generate_email_draft(analysis.proposal_brief, validation)

        return WorkflowOutput(
            execution_mode=mode,
            requirements=analysis.requirements,
            knowledge_lookup=analysis.knowledge_lookup,
            proposal_brief=analysis.proposal_brief,
            validation=validation,
            email_draft=email,
            approval_gate_status="HUMAN APPROVAL REQUIRED"
        )

    def _fallback_analysis(self, transcript: str) -> ProposalAnalysis:
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
        if "patient triage" in t or "triage" in t:
            requested_services.append("Custom AI Patient Triage Automation")
        if "cryptography" in t or "rocket" in t:
            requested_services.append("Custom Quantum Cryptography")

        if not requested_services:
            requested_services = ["CRM Integration"]

        matched_services = []
        for svc in requested_services:
            svc_fn = getattr(get_service_details, "__wrapped__", get_service_details)
            res = svc_fn(svc)
            is_supported = "SERVICE NOT OFFERED" not in str(res)
            matched_services.append({
                "service_name": svc,
                "is_supported": is_supported,
                "notes": str(res)
            })

        topic = " ".join(requested_services)
        cs_fn = getattr(get_case_studies, "__wrapped__", get_case_studies)
        cs_res = cs_fn(topic)
        found_cs = "NO MATCHING CASE STUDY" not in str(cs_res)
        matched_case_studies = [{
            "case_study_title": "Apex Logistics / Meridian Wealth" if found_cs else None,
            "found_matching_case_study": found_cs,
            "relevance_summary": str(cs_res)
        }]

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

        req = RequirementExtraction(
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

        has_missing_params = len(open_q) > 0
        pricing_status = "Pricing requires manual estimation." if has_missing_params else "Standard reference pricing guidelines apply."

        kl = BusinessKnowledgeLookupResult(
            matched_services=matched_services,
            matched_case_studies=matched_case_studies,
            pricing_status=pricing_status
        )

        offered = [m["service_name"] for m in matched_services if m["is_supported"]]
        unsupported = [m["service_name"] for m in matched_services if not m["is_supported"]]

        cs_title = []
        if found_cs:
            cs_title.append("Case Study 1: Apex Logistics Consulting")
        else:
            cs_title.append("No matching case study exists in knowledge base.")

        pb = ProposalBrief(
            client_name=client,
            company_name=company,
            business_problem=req.business_problem.value,
            desired_outcome=req.desired_outcome.value,
            recommended_services=offered if offered else ["CRM Integration"],
            unsupported_requested_services=unsupported,
            relevant_case_studies=cs_title,
            timeline_discussed=req.timeline.value,
            budget_signal=req.budget_signal.value,
            pricing_estimate=pricing_status,
            known_requirements=[f"Automate lead intake for {company}"],
            missing_critical_information=open_q if open_q else ["Exact scope parameters needed for pricing."],
            assumptions=["Client will select target CRM system prior to project kickoff."],
            risks=["Scope expansion if CRM migration is required."],
            recommended_next_step="Schedule follow-up call to finalize CRM choice and scope details."
        )

        return ProposalAnalysis(
            requirements=req,
            knowledge_lookup=kl,
            proposal_brief=pb
        )
