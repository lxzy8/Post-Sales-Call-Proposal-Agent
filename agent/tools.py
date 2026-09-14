import os
import glob
from typing import Dict, List
from agents import function_tool

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

def _read_data_file(filename: str) -> str:
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

@function_tool
def search_business_knowledge(query: str) -> str:
    """Search through company profile, services, case studies, and pricing documentation for relevant information.

    Args:
        query: Keywords or topic to search across business knowledge base.
    """
    print(f"  [Agents SDK Runtime -> Tool Invoked]: search_business_knowledge(query='{query}')")
    results = []
    query_lower = query.lower()
    for filepath in glob.glob(os.path.join(DATA_DIR, "*.md")):
        fname = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            if any(term in content.lower() for term in query_lower.split()):
                results.append(f"--- Document: {fname} ---\n{content}\n")
    if not results:
        return f"No business documentation found matching '{query}'."
    return "\n".join(results)

@function_tool
def get_service_details(service_name: str) -> str:
    """Retrieve detailed information about a specific service offered by Northstar Digital.

    Args:
        service_name: Name of the service (e.g., 'CRM Integration', 'Lead Capture Automation', 'Website Redesign', 'Web Analytics Implementation').
    """
    print(f"  [Agents SDK Runtime -> Tool Invoked]: get_service_details(service_name='{service_name}')")
    content = _read_data_file("services.md")
    service_lower = service_name.lower()

    supported_services = [
        "website redesign",
        "crm integration",
        "lead capture automation",
        "web analytics implementation",
        "analytics implementation",
        "web analytics"
    ]

    is_supported = any(sup in service_lower for sup in supported_services)
    if not is_supported:
        return (
            f"SERVICE NOT OFFERED: Northstar Digital does NOT offer '{service_name}'. "
            f"Offered services are strictly: Website Redesign, CRM Integration, Lead Capture Automation, and Web Analytics Implementation."
        )
    return f"Official Service Details:\n{content}"

@function_tool
def get_case_studies(industry_or_topic: str) -> str:
    """Look up existing case studies relevant to an industry, service, or business problem.

    Args:
        industry_or_topic: Topic, service, or industry to search in case studies (e.g. 'Lead capture', 'Healthcare', 'Consulting').
    """
    print(f"  [Agents SDK Runtime -> Tool Invoked]: get_case_studies(industry_or_topic='{industry_or_topic}')")
    content = _read_data_file("case_studies.md")
    topic_lower = industry_or_topic.lower()

    matched = []
    if any(k in topic_lower for k in ["lead capture", "crm", "logistics", "consulting", "b2b"]):
        matched.append("Case Study 1: Apex Logistics Consulting (Lead Capture Automation + CRM Integration)")
    if any(k in topic_lower for k in ["analytics", "redesign", "wealth", "financial"]):
        matched.append("Case Study 2: Meridian Wealth Advisory (Website Redesign + Web Analytics Implementation)")

    if not matched:
        return (
            f"NO MATCHING CASE STUDY: No case study exists for '{industry_or_topic}'. "
            f"Do not fabricate or invent a case study. Clearly state in proposal that no matching case study is available for this specific topic/industry."
        )

    return f"Matching Case Studies Found:\n" + "\n".join(matched) + f"\n\nFull Case Studies Reference:\n{content}"
