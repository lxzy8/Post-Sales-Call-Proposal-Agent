from typing import List, Optional
from pydantic import BaseModel, Field

class RequirementItem(BaseModel):
    value: str = Field(description="Extracted value or requirement summary.")
    grounded_in_transcript: bool = Field(description="True if explicitly stated in transcript, False if inferred or unknown.")
    evidence_quote: Optional[str] = Field(default=None, description="Direct quote or snippet from transcript as evidence.")

class RequirementExtraction(BaseModel):
    client_name: RequirementItem = Field(description="Name of the prospect/contact person.")
    company_name: RequirementItem = Field(description="Name of the prospect's company.")
    business_problem: RequirementItem = Field(description="Core operational pain or problem described.")
    desired_outcome: RequirementItem = Field(description="What success looks like for the client.")
    requested_services: List[str] = Field(description="Services requested or discussed by client.")
    timeline: RequirementItem = Field(description="Timeline or deadline details discussed.")
    stakeholders: List[str] = Field(description="Key stakeholders and decision makers mentioned.")
    budget_signal: RequirementItem = Field(description="Budget information or signals provided.")
    constraints: List[str] = Field(default_factory=list, description="Technical or organizational constraints mentioned.")
    objections: List[str] = Field(default_factory=list, description="Objections or concerns raised by client.")
    open_questions: List[str] = Field(default_factory=list, description="Unresolved questions or missing details from call.")

class ServiceMatch(BaseModel):
    service_name: str
    is_supported: bool = Field(description="True if Northstar Digital offers this service, False if unsupported.")
    notes: str = Field(description="Details on alignment or why it's unsupported.")

class CaseStudyMatch(BaseModel):
    case_study_title: Optional[str] = Field(default=None)
    found_matching_case_study: bool = Field(description="True if a relevant case study exists in knowledge base.")
    relevance_summary: str = Field(description="Explanation of relevance or statement that no matching case study exists.")

class BusinessKnowledgeLookupResult(BaseModel):
    matched_services: List[ServiceMatch]
    matched_case_studies: List[CaseStudyMatch]
    pricing_status: str = Field(description="Either estimated pricing rules or 'Pricing requires manual estimation.'")

class ProposalBrief(BaseModel):
    client_name: str
    company_name: str
    business_problem: str
    desired_outcome: str
    recommended_services: List[str]
    unsupported_requested_services: List[str] = Field(default_factory=list)
    relevant_case_studies: List[str] = Field(default_factory=list)
    timeline_discussed: str
    budget_signal: str
    pricing_estimate: str = Field(description="Price quote or 'Pricing requires manual estimation.'")
    known_requirements: List[str]
    missing_critical_information: List[str]
    assumptions: List[str]
    risks: List[str]
    recommended_next_step: str

class ValidationResult(BaseModel):
    status: str = Field(description="NEEDS HUMAN REVIEW or PASSED")
    is_pricing_grounded: bool
    is_timeline_clear: bool
    are_services_offered: bool
    case_study_valid: bool
    missing_critical_info_flagged: bool
    issues: List[str] = Field(default_factory=list)

class EmailDraft(BaseModel):
    subject: str
    body: str
    watermark: str = Field(default="DRAFT — NOT SENT")

class WorkflowOutput(BaseModel):
    requirements: RequirementExtraction
    knowledge_lookup: BusinessKnowledgeLookupResult
    proposal_brief: ProposalBrief
    validation: ValidationResult
    email_draft: EmailDraft
    approval_gate_status: str = Field(default="HUMAN APPROVAL REQUIRED")
