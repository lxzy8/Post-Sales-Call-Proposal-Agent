from typing import List
from agent.schemas import RequirementExtraction, BusinessKnowledgeLookupResult, ProposalBrief, ValidationResult

def validate_proposal(
    requirements: RequirementExtraction,
    knowledge_lookup: BusinessKnowledgeLookupResult,
    proposal_brief: ProposalBrief
) -> ValidationResult:
    """
    Programmatic validation guardrail verifying that:
    1. Factual claims are grounded in transcript or business rules.
    2. Pricing was not hallucinated / guessed when parameters are missing.
    3. Timelines are not fabricated if ambiguous.
    4. Services recommended are actually offered by company.
    5. Case studies referenced exist in business knowledge.
    6. Important missing requirements are explicitly flagged.
    """
    issues: List[str] = []

    # 1. Pricing Check
    is_pricing_grounded = True
    price_str = proposal_brief.pricing_estimate
    pricing_status = knowledge_lookup.pricing_status

    # If open questions or missing details exist for key pricing drivers (e.g. CRM platform, scope)
    # pricing must state "Pricing requires manual estimation."
    has_missing_pricing_params = any(
        "crm" in q.lower() or "platform" in q.lower() or "price" in q.lower() or "budget" in q.lower() or "scope" in q.lower()
        for q in requirements.open_questions
    ) or len(proposal_brief.missing_critical_information) > 0

    if has_missing_pricing_params or "manual estimation" in pricing_status.lower():
        if "pricing requires manual estimation" not in price_str.lower():
            is_pricing_grounded = False
            issues.append(
                f"Pricing Violation: Agent output pricing as '{price_str}', but required parameters (e.g. CRM platform, exact scope) are missing. Pricing must state 'Pricing requires manual estimation.'"
            )

    # 2. Timeline Check
    is_timeline_clear = True
    timeline_val = requirements.timeline.value.lower()
    if "not finalized" in timeline_val or "uncertain" in timeline_val or "ambiguous" in timeline_val or "tbd" in timeline_val or not requirements.timeline.grounded_in_transcript:
        if "confirm" not in proposal_brief.timeline_discussed.lower() and "tbd" not in proposal_brief.timeline_discussed.lower() and "uncertain" not in proposal_brief.timeline_discussed.lower() and "target" not in proposal_brief.timeline_discussed.lower():
            is_timeline_clear = False
            issues.append("Timeline Warning: Timeline is ambiguous or not finalized in transcript; must be clearly flagged for confirmation.")

    # 3. Service Offering Check
    are_services_offered = True
    offered_services_list = ["website redesign", "crm integration", "lead capture automation", "web analytics implementation", "analytics implementation", "web analytics"]
    for service_match in knowledge_lookup.matched_services:
        if not service_match.is_supported:
            are_services_offered = False
            issues.append(f"Unsupported Service Flagged: Client requested '{service_match.service_name}' which is NOT offered by Northstar Digital.")

    # Check if proposal brief mistakenly included an unsupported service in recommended_services
    for rec in proposal_brief.recommended_services:
        if not any(off in rec.lower() for off in offered_services_list):
            are_services_offered = False
            issues.append(f"Invalid Recommendation: '{rec}' is recommended in proposal brief but is not an offered service.")

    # 4. Case Study Check
    case_study_valid = True
    for cs_match in knowledge_lookup.matched_case_studies:
        if not cs_match.found_matching_case_study:
            # Verify proposal brief does not hallucinate a case study
            for cs_ref in proposal_brief.relevant_case_studies:
                if "no matching case study" not in cs_ref.lower() and "none available" not in cs_ref.lower():
                    case_study_valid = False
                    issues.append(f"Case Study Violation: Proposal referenced '{cs_ref}' when no matching case study exists in knowledge base.")

    # 5. Missing Critical Info Check
    missing_critical_info_flagged = True
    if len(requirements.open_questions) > 0 and len(proposal_brief.missing_critical_information) == 0:
        missing_critical_info_flagged = False
        issues.append("Missing Info Violation: Transcript contains unresolved questions, but missing_critical_information in proposal brief is empty.")

    # Status Determination
    # Note: If unsupported services or missing info issues exist, or pricing needs manual estimation, status is NEEDS HUMAN REVIEW
    status = "NEEDS HUMAN REVIEW" if (issues or not is_pricing_grounded or not is_timeline_clear or len(proposal_brief.missing_critical_information) > 0) else "PASSED"

    return ValidationResult(
        status=status,
        is_pricing_grounded=is_pricing_grounded,
        is_timeline_clear=is_timeline_clear,
        are_services_offered=are_services_offered,
        case_study_valid=case_study_valid,
        missing_critical_info_flagged=missing_critical_info_flagged,
        issues=issues
    )
