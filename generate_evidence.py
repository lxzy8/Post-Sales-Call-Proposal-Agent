import os
import html
from playwright.sync_api import sync_playwright
from agent.agent import ProposalAgentWorkflow

def main():
    os.makedirs("evidence", exist_ok=True)

    with open("data/sales_call_transcript.txt", "r", encoding="utf-8") as f:
        transcript = f.read()

    workflow = ProposalAgentWorkflow()
    output = workflow.run_workflow(transcript)

    req = output.requirements
    kl = output.knowledge_lookup
    pb = output.proposal_brief
    val = output.validation
    email = output.email_draft

    sections = {
        "01_input.png": ("Input Sales Call Transcript", f"<pre>{html.escape(transcript)}</pre>"),
        "02_agent_execution.png": ("Workflow Execution Started", "<h3>Post-Sales-Call Proposal Agent Workflow Initiated</h3><p>Processing unstructured conversation through 7-stage deterministic reasoning pipeline...</p>"),
        "03_requirements.png": ("Stage 1: Structured Requirement Extraction", f"""
        <ul>
          <li><b>Client Name:</b> {html.escape(req.client_name.value)} (Grounded: {req.client_name.grounded_in_transcript})</li>
          <li><b>Company Name:</b> {html.escape(req.company_name.value)} (Grounded: {req.company_name.grounded_in_transcript})</li>
          <li><b>Business Problem:</b> {html.escape(req.business_problem.value)}</li>
          <li><b>Desired Outcome:</b> {html.escape(req.desired_outcome.value)}</li>
          <li><b>Requested Services:</b> {html.escape(', '.join(req.requested_services))}</li>
          <li><b>Timeline:</b> {html.escape(req.timeline.value)}</li>
          <li><b>Stakeholders:</b> {html.escape(', '.join(req.stakeholders))}</li>
          <li><b>Budget Signal:</b> {html.escape(req.budget_signal.value)}</li>
          <li><b>Open Questions:</b>
            <ul>{''.join([f'<li>{html.escape(q)}</li>' for q in req.open_questions])}</ul>
          </li>
        </ul>
        """),
        "04_knowledge_lookup.png": ("Stage 2: Business Knowledge Lookup", f"""
        <h4>Matched Services:</h4>
        <ul>{''.join([f'<li><b>{html.escape(ms.service_name)}:</b> Offered={ms.is_supported} ({html.escape(ms.notes[:100])}...)</li>' for ms in kl.matched_services])}</ul>
        <h4>Matched Case Studies:</h4>
        <ul>{''.join([f'<li><b>Found Match:</b> {cs.found_matching_case_study} - {html.escape(cs.relevance_summary[:150])}...</li>' for cs in kl.matched_case_studies])}</ul>
        <h4>Pricing Rule Status:</h4>
        <p><code>{html.escape(kl.pricing_status)}</code></p>
        """),
        "05_validation.png": ("Stage 3: Validation Result", f"""
        <div style="background-color: #2b1f1d; padding: 15px; border-left: 4px solid #f39c12; margin-bottom: 15px;">
          <h3 style="color: #f39c12; margin-top: 0;">VALIDATION STATUS: {html.escape(val.status)}</h3>
          <ul>
            <li><b>Pricing Grounded:</b> {val.is_pricing_grounded}</li>
            <li><b>Timeline Clear:</b> {val.is_timeline_clear}</li>
            <li><b>Services Offered:</b> {val.are_services_offered}</li>
            <li><b>Case Study Valid:</b> {val.case_study_valid}</li>
            <li><b>Missing Info Flagged:</b> {val.missing_critical_info_flagged}</li>
          </ul>
          <h4>Flagged Issues:</h4>
          <ul>{''.join([f'<li>{html.escape(iss)}</li>' for iss in val.issues])}</ul>
        </div>
        """),
        "06_proposal_brief.png": ("Stage 4: Proposal Brief", f"""
        <div style="background-color: #1e2530; padding: 15px; border: 1px solid #3a4b63;">
          <p><b>Client:</b> {html.escape(pb.client_name)} ({html.escape(pb.company_name)})</p>
          <p><b>Business Problem:</b> {html.escape(pb.business_problem)}</p>
          <p><b>Recommended Services:</b> {html.escape(', '.join(pb.recommended_services))}</p>
          <p><b>Unsupported Services Flagged:</b> {html.escape(', '.join(pb.unsupported_requested_services) if pb.unsupported_requested_services else 'None')}</p>
          <p><b>Pricing Estimate:</b> <code>{html.escape(pb.pricing_estimate)}</code></p>
          <p><b>Timeline:</b> {html.escape(pb.timeline_discussed)}</p>
          <p><b>Missing Critical Information:</b></p>
          <ul>{''.join([f'<li>{html.escape(mi)}</li>' for mi in pb.missing_critical_information])}</ul>
        </div>
        """),
        "07_email_draft.png": ("Stage 5: Personalized Email Draft", f"""
        <div style="background-color: #182218; padding: 15px; border: 1px solid #2e522e;">
          <div style="background-color: #2e522e; color: #ffffff; padding: 4px 8px; font-weight: bold; width: fit-content;">{html.escape(email.watermark)}</div>
          <h4>Subject: {html.escape(email.subject)}</h4>
          <pre style="white-space: pre-wrap; font-family: monospace;">{html.escape(email.body)}</pre>
        </div>
        """),
        "08_human_approval.png": ("Stage 6: Human Approval Gate", """
        <div style="background-color: #3b1d1d; padding: 25px; border: 2px solid #e74c3c; text-align: center;">
          <h2 style="color: #e74c3c; margin-top: 0;">🛑 HUMAN APPROVAL REQUIRED</h2>
          <p style="font-size: 16px;">The proposal brief and email draft have been generated and validated.</p>
          <p style="font-size: 16px; font-weight: bold; color: #f39c12;">NO EXTERNAL EMAIL OR ACTION HAS BEEN AUTOMATICALLY EXECUTED.</p>
          <p style="color: #bdc3c7;">Review complete. Pending human approval before proceeding.</p>
        </div>
        """)
    }

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1000, "height": 700})

        for fname, (title, body_html) in sections.items():
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <style>
                body {{
                  background-color: #0d1117;
                  color: #c9d1d9;
                  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                  padding: 30px;
                  margin: 0;
                }}
                h1 {{
                  color: #58a6ff;
                  border-bottom: 1px solid #30363d;
                  padding-bottom: 10px;
                }}
                pre, code {{
                  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
                  background-color: #161b22;
                  padding: 10px;
                  border-radius: 6px;
                }}
                li {{ margin-bottom: 6px; }}
              </style>
            </head>
            <body>
              <h1>Northstar Digital Agent — {title}</h1>
              {body_html}
            </body>
            </html>
            """
            page.set_content(html_content)
            page.screenshot(path=os.path.join("evidence", fname))
            print(f"Captured evidence screenshot: evidence/{fname}")

        browser.close()

if __name__ == "__main__":
    main()
