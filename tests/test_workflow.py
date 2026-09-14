import pytest
import os
from agent.agent import ProposalAgentWorkflow

@pytest.fixture
def workflow():
    return ProposalAgentWorkflow(allow_fallback=True)

def test_scenario_1_and_default_transcript(workflow):
    """TEST 1: Normal transcript processing with ambiguity."""
    transcript_path = os.path.join(os.path.dirname(__file__), "..", "data", "sales_call_transcript.txt")
    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript = f.read()

    result = workflow.run_workflow(transcript)

    assert result.approval_gate_status == "HUMAN APPROVAL REQUIRED"
    assert result.email_draft.watermark == "DRAFT — NOT SENT"
    assert result.requirements.client_name.value != ""
    assert "Nexus" in result.requirements.company_name.value or "Health" in result.requirements.company_name.value
    assert len(result.requirements.requested_services) > 0

def test_scenario_2_missing_pricing(workflow):
    """TEST 2: Missing pricing parameters produces 'Pricing requires manual estimation.'"""
    transcript = """
    Sales Rep: Hi John, what do you need?
    Prospect: We need CRM integration at Acme Corp, but we haven't selected a CRM vendor yet and don't know our budget or seat count.
    """
    result = workflow.run_workflow(transcript)
    assert "Pricing requires manual estimation." in result.proposal_brief.pricing_estimate
    assert result.validation.status == "NEEDS HUMAN REVIEW"

def test_scenario_3_missing_critical_requirement(workflow):
    """TEST 3: Missing critical requirements are explicitly identified."""
    transcript = """
    Sales Rep: Hi Alice from TechCorp.
    Prospect: We want lead capture automation, but we haven't decided what forms or channels to integrate.
    """
    result = workflow.run_workflow(transcript)
    assert len(result.proposal_brief.missing_critical_information) > 0

def test_scenario_4_no_matching_case_study(workflow):
    """TEST 4: Handles request with no matching case study without hallucinating."""
    transcript = """
    Sales Rep: Hi Bob.
    Prospect: I run Space Rocket Inc in aerospace manufacturing. Do you have a case study on aerospace rocket factory analytics?
    """
    result = workflow.run_workflow(transcript)
    case_studies_str = " ".join(result.proposal_brief.relevant_case_studies).lower()
    assert "rocket" not in case_studies_str
    assert "aerospace" not in case_studies_str or "no matching" in case_studies_str or len(result.proposal_brief.relevant_case_studies) == 0 or "none" in case_studies_str

def test_scenario_5_ambiguous_timeline(workflow):
    """TEST 5: Ambiguous timeline is flagged."""
    transcript = """
    Sales Rep: What is your timeline?
    Prospect: We have no idea on timeline. Maybe next year, maybe never. Completely uncertain.
    """
    result = workflow.run_workflow(transcript)
    timeline_str = result.proposal_brief.timeline_discussed.lower()
    assert "uncertain" in timeline_str or "tbd" in timeline_str or "not finalized" in timeline_str or "confirm" in timeline_str or "unknown" in timeline_str or "unclear" in timeline_str

def test_scenario_6_unsupported_service_request(workflow):
    """TEST 6: Unsupported service request is explicitly flagged and not offered."""
    transcript = """
    Sales Rep: Hi Dan from BioMed.
    Prospect: We need custom quantum cryptography for medical devices. Do you do that?
    """
    result = workflow.run_workflow(transcript)
    assert len(result.proposal_brief.unsupported_requested_services) > 0 or result.validation.are_services_offered is False

def test_strict_agents_sdk_no_fallback():
    """Strict E2E test mode: ensures allow_fallback=False raises an error when API is unavailable."""
    wf = ProposalAgentWorkflow(api_key="invalid-key-for-strict-test", allow_fallback=False)
    transcript = "Sales Rep: Hello. Prospect: Hi, we need CRM Integration."
    with pytest.raises(RuntimeError) as exc_info:
        wf.run_workflow(transcript)
    assert "OpenAI Agents SDK execution failed" in str(exc_info.value)
