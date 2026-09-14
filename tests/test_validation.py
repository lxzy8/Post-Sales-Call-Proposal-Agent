import pytest
from agent.schemas import (
    RequirementExtraction, RequirementItem, BusinessKnowledgeLookupResult,
    ServiceMatch, CaseStudyMatch, ProposalBrief
)
from agent.validation import validate_proposal

def test_validation_missing_pricing():
    req = RequirementExtraction(
        client_name=RequirementItem(value="Sarah", grounded_in_transcript=True),
        company_name=RequirementItem(value="Nexus", grounded_in_transcript=True),
        business_problem=RequirementItem(value="Data entry pain", grounded_in_transcript=True),
        desired_outcome=RequirementItem(value="Automated pipeline", grounded_in_transcript=True),
        requested_services=["CRM Integration"],
        timeline=RequirementItem(value="Q3/Q4", grounded_in_transcript=True),
        stakeholders=["Sarah"],
        budget_signal=RequirementItem(value="Mid five figures", grounded_in_transcript=True),
        open_questions=["Which CRM platform will be used?"]
    )

    kl = BusinessKnowledgeLookupResult(
        matched_services=[ServiceMatch(service_name="CRM Integration", is_supported=True, notes="Offered")],
        matched_case_studies=[CaseStudyMatch(case_study_title="Apex", found_matching_case_study=True, relevance_summary="Match")],
        pricing_status="Pricing requires manual estimation."
    )

    brief = ProposalBrief(
        client_name="Sarah",
        company_name="Nexus",
        business_problem="Data entry pain",
        desired_outcome="Automated pipeline",
        recommended_services=["CRM Integration"],
        pricing_estimate="$20,000 fixed price",  # Violates rule! Should state manual estimation.
        timeline_discussed="Q3/Q4",
        budget_signal="Mid five figures",
        known_requirements=["CRM integration"],
        missing_critical_information=["CRM platform unconfirmed"],
        assumptions=[],
        risks=[],
        recommended_next_step="Confirm CRM platform"
    )

    res = validate_proposal(req, kl, brief)
    assert res.status == "NEEDS HUMAN REVIEW"
    assert res.is_pricing_grounded is False
    assert any("Pricing Violation" in issue for issue in res.issues)

def test_validation_unsupported_service():
    req = RequirementExtraction(
        client_name=RequirementItem(value="Sarah", grounded_in_transcript=True),
        company_name=RequirementItem(value="Nexus", grounded_in_transcript=True),
        business_problem=RequirementItem(value="Triage", grounded_in_transcript=True),
        desired_outcome=RequirementItem(value="AI Triage", grounded_in_transcript=True),
        requested_services=["Custom AI Patient Triage"],
        timeline=RequirementItem(value="Q3", grounded_in_transcript=True),
        stakeholders=["Sarah"],
        budget_signal=RequirementItem(value="Flexible", grounded_in_transcript=True),
        open_questions=[]
    )

    kl = BusinessKnowledgeLookupResult(
        matched_services=[ServiceMatch(service_name="Custom AI Patient Triage", is_supported=False, notes="SERVICE NOT OFFERED")],
        matched_case_studies=[],
        pricing_status="Pricing requires manual estimation."
    )

    brief = ProposalBrief(
        client_name="Sarah",
        company_name="Nexus",
        business_problem="Triage",
        desired_outcome="AI Triage",
        recommended_services=["Custom AI Patient Triage"], # Violates rule!
        pricing_estimate="Pricing requires manual estimation.",
        timeline_discussed="Q3",
        budget_signal="Flexible",
        known_requirements=[],
        missing_critical_information=[],
        assumptions=[],
        risks=[],
        recommended_next_step="Discuss"
    )

    res = validate_proposal(req, kl, brief)
    assert res.status == "NEEDS HUMAN REVIEW"
    assert res.are_services_offered is False
    assert any("Unsupported Service" in issue or "Invalid Recommendation" in issue for issue in res.issues)
