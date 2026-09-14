#!/usr/bin/env python3
import sys
import os
import json
from agent.agent import ProposalAgentWorkflow

def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f"  {title.upper()}")
    print("=" * 80)

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Please export OPENAI_API_KEY before running this script.", file=sys.stderr)
        sys.exit(1)

    transcript_path = os.path.join(os.path.dirname(__file__), "data", "sales_call_transcript.txt")
    if len(sys.argv) > 1:
        transcript_path = sys.argv[1]

    if not os.path.exists(transcript_path):
        print(f"ERROR: Transcript file not found at {transcript_path}", file=sys.stderr)
        sys.exit(1)

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    print_banner("1. Sales Call Transcript Input")
    print(transcript[:500] + "...\n[Transcript truncated for display]")

    workflow = ProposalAgentWorkflow()

    print("\n[Running Post-Sales-Call Proposal Agent Workflow...]")
    output = workflow.run_workflow(transcript)

    print_banner("2. Requirement Extraction")
    req = output.requirements
    print(f"• Client Name: {req.client_name.value} (Grounded: {req.client_name.grounded_in_transcript})")
    print(f"• Company Name: {req.company_name.value} (Grounded: {req.company_name.grounded_in_transcript})")
    print(f"• Business Problem: {req.business_problem.value}")
    print(f"• Desired Outcome: {req.desired_outcome.value}")
    print(f"• Requested Services: {', '.join(req.requested_services)}")
    print(f"• Timeline: {req.timeline.value}")
    print(f"• Stakeholders: {', '.join(req.stakeholders)}")
    print(f"• Budget Signal: {req.budget_signal.value}")
    print(f"• Open Questions / Ambiguities:")
    for q in req.open_questions:
        print(f"   - {q}")

    print_banner("3. Business Knowledge Lookup")
    kl = output.knowledge_lookup
    print("• Matched Services:")
    for ms in kl.matched_services:
        status_str = "OFFERED" if ms.is_supported else "NOT OFFERED (UNSUPPORTED)"
        print(f"   - {ms.service_name}: [{status_str}]")
    print("\n• Matched Case Studies:")
    for cs in kl.matched_case_studies:
        print(f"   - Found Match: {cs.found_matching_case_study}")
        print(f"     Summary: {cs.relevance_summary[:150]}...")
    print(f"\n• Pricing Status Rule: {kl.pricing_status}")

    print_banner("4. Proposal Brief")
    pb = output.proposal_brief
    print(f"Client: {pb.client_name} ({pb.company_name})")
    print(f"Business Problem: {pb.business_problem}")
    print(f"Desired Outcome: {pb.desired_outcome}")
    print(f"Recommended Services: {', '.join(pb.recommended_services)}")
    if pb.unsupported_requested_services:
        print(f"Unsupported Requested Services: {', '.join(pb.unsupported_requested_services)}")
    print(f"Relevant Case Studies: {', '.join(pb.relevant_case_studies) if pb.relevant_case_studies else 'None'}")
    print(f"Pricing Estimate: {pb.pricing_estimate}")
    print(f"Timeline Discussed: {pb.timeline_discussed}")
    print(f"Budget Signal: {pb.budget_signal}")
    print("Known Requirements:")
    for kr in pb.known_requirements:
        print(f"   - {kr}")
    print("Missing Critical Information:")
    for mi in pb.missing_critical_information:
        print(f"   - {mi}")
    print("Assumptions:")
    for asm in pb.assumptions:
        print(f"   - {asm}")
    print("Risks:")
    for rsk in pb.risks:
        print(f"   - {rsk}")
    print(f"Recommended Next Step: {pb.recommended_next_step}")

    print_banner("5. Validation Result")
    val = output.validation
    print(f"Status: {val.status}")
    print(f"• Pricing Grounded: {val.is_pricing_grounded}")
    print(f"• Timeline Clear: {val.is_timeline_clear}")
    print(f"• Services Offered: {val.are_services_offered}")
    print(f"• Case Study Valid: {val.case_study_valid}")
    print(f"• Missing Info Flagged: {val.missing_critical_info_flagged}")
    if val.issues:
        print("Issues Flagged:")
        for iss in val.issues:
            print(f"   - {iss}")

    print_banner("6. Email Draft (DRAFT — NOT SENT)")
    email = output.email_draft
    print(f"Subject: {email.subject}")
    print(f"Watermark: [{email.watermark}]")
    print("-" * 40)
    print(email.body)
    print("-" * 40)

    print_banner("7. Human Approval Gate")
    print("🛑 STATUS: HUMAN APPROVAL REQUIRED")
    print("The proposal brief and email draft have been generated and validated.")
    print("NO EXTERNAL EMAIL OR ACTION HAS BEEN AUTOMATICALLY EXECUTED.")
    print("Please review the output above and approve before sending.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
