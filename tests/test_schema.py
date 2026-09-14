import pytest
from agent.schemas import RequirementExtraction, RequirementItem, ProposalBrief, ValidationResult, EmailDraft

def test_requirement_item_schema():
    item = RequirementItem(value="Sarah Jenkins", grounded_in_transcript=True, evidence_quote="I'm Sarah Jenkins")
    assert item.value == "Sarah Jenkins"
    assert item.grounded_in_transcript is True
    assert item.evidence_quote == "I'm Sarah Jenkins"

def test_validation_result_schema():
    val = ValidationResult(
        status="NEEDS HUMAN REVIEW",
        is_pricing_grounded=False,
        is_timeline_clear=True,
        are_services_offered=True,
        case_study_valid=True,
        missing_critical_info_flagged=True,
        issues=["Pricing requires manual estimation."]
    )
    assert val.status == "NEEDS HUMAN REVIEW"
    assert len(val.issues) == 1

def test_email_draft_watermark():
    draft = EmailDraft(subject="Proposal Follow-up", body="Hello Sarah...")
    assert draft.watermark == "DRAFT — NOT SENT"
