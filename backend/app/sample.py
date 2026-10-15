"""Synthetic organization. No real employee, financial or authorization information."""
from __future__ import annotations


SKILLS = [
    "refund-preparation", "refund-approval", "payout-execution", "vendor-review",
    "vendor-approval", "vendor-provisioning", "incident-triage", "release-approval",
    "deployment-execution", "payroll-review", "payroll-approval", "salary-release",
    "privacy-review", "export-approval", "export-execution",
]
PERMISSIONS = [
    "REFUND_PREPARE", "REFUND_APPROVE", "PAYOUT_RELEASE", "VENDOR_REVIEW",
    "VENDOR_APPROVE", "VENDOR_CREATE", "INCIDENT_VIEW", "RELEASE_APPROVE",
    "DEPLOY_PROD", "PAYROLL_REVIEW", "PAYROLL_APPROVE", "SALARY_RELEASE",
    "PRIVACY_REVIEW", "EXPORT_APPROVE", "EXPORT_EXECUTE",
]

TEAMS = ["Operations", "Finance", "Treasury", "Engineering", "Security", "People"]

# (id, name, team, role, skills, permissions; expired permissions)
ROSTER = [
    ("p01", "Noor Mehta", "Operations", "Operations analyst", ["refund-preparation", "vendor-review"], ["REFUND_PREPARE", "VENDOR_REVIEW"], []),
    ("p02", "Ava Shah", "Finance", "Refund lead", ["refund-approval"], ["REFUND_APPROVE"], []),
    ("p03", "Priya Nair", "Finance", "Refund backup", ["refund-approval"], ["REFUND_APPROVE"], ["REFUND_APPROVE"]),
    ("p04", "Vikram Rao", "Treasury", "Payments specialist", ["refund-approval", "payout-execution"], ["REFUND_APPROVE", "PAYOUT_RELEASE"], []),
    ("p05", "Leena Das", "Finance", "Finance manager", ["payroll-approval"], ["PAYROLL_APPROVE"], []),
    ("p06", "Samir Bose", "Treasury", "Treasury analyst", ["salary-release"], ["SALARY_RELEASE"], []),
    ("p07", "Isha Jain", "People", "Payroll coordinator", ["payroll-review"], ["PAYROLL_REVIEW"], []),
    ("p08", "Kabir Sethi", "Operations", "Vendor specialist", ["vendor-review"], ["VENDOR_REVIEW"], []),
    ("p09", "Mina Roy", "Finance", "Vendor approver", ["vendor-approval"], ["VENDOR_APPROVE"], []),
    ("p10", "Ansh Gupta", "Operations", "Vendor provisioning", ["vendor-provisioning"], ["VENDOR_CREATE"], []),
    ("p11", "Riya Sen", "Engineering", "Incident commander", ["incident-triage"], ["INCIDENT_VIEW"], []),
    ("p12", "Nikhil Das", "Engineering", "Release captain", ["release-approval"], ["RELEASE_APPROVE"], []),
    ("p13", "Tara Singh", "Engineering", "Platform engineer", ["deployment-execution"], ["DEPLOY_PROD"], []),
    ("p14", "Dev Malhotra", "Security", "Privacy officer", ["privacy-review"], ["PRIVACY_REVIEW"], []),
    ("p15", "Zoya Khan", "Security", "Data approver", ["export-approval"], ["EXPORT_APPROVE"], []),
    ("p16", "Arjun Pillai", "Engineering", "Data operations", ["export-execution"], ["EXPORT_EXECUTE"], []),
    ("p17", "Farah Ali", "People", "HR operations", ["payroll-review"], ["PAYROLL_REVIEW"], []),
    ("p18", "Omar Chawla", "Engineering", "Release backup", ["release-approval"], ["RELEASE_APPROVE"], []),
    ("p19", "Naina Verma", "Engineering", "SRE", ["incident-triage", "deployment-execution"], ["INCIDENT_VIEW", "DEPLOY_PROD"], []),
    ("p20", "Parth Bhatia", "Operations", "Vendor backup", ["vendor-provisioning"], ["VENDOR_CREATE"], ["VENDOR_CREATE"]),
    ("p21", "Gauri Arora", "Security", "Security engineer", ["privacy-review"], ["PRIVACY_REVIEW"], []),
    ("p22", "Rohit Kapoor", "Finance", "Senior accountant", ["payroll-approval"], ["PAYROLL_APPROVE"], ["PAYROLL_APPROVE"]),
    ("p23", "Meera Joshi", "Treasury", "Settlement backup", ["salary-release"], ["SALARY_RELEASE"], ["SALARY_RELEASE"]),
    ("p24", "Yash Oberoi", "Finance", "Refund associate", ["refund-approval"], [], []),
    ("p25", "Kavya Iyer", "Operations", "Operations lead", ["refund-preparation"], ["REFUND_PREPARE"], []),
    ("p26", "Sana Qureshi", "Security", "Compliance manager", ["export-approval"], ["EXPORT_APPROVE"], []),
    ("p27", "Neil Mathur", "Engineering", "DBA", ["export-execution"], ["EXPORT_EXECUTE"], []),
    ("p28", "Pooja Kulkarni", "People", "People analyst", ["payroll-review"], ["PAYROLL_REVIEW"], []),
    ("p29", "Harsh Khanna", "Operations", "Ops reviewer", ["vendor-review"], ["VENDOR_REVIEW"], []),
    ("p30", "Aditi Menon", "Finance", "Accounts director", ["vendor-approval"], ["VENDOR_APPROVE"], []),
]

WORKFLOWS = [
    {"id":"enterprise-refund", "name":"Enterprise refund release", "department":"Finance", "criticality":"Critical", "description":"Safely process high-value customer refunds with independent approval and payment release.", "owner":"Finance", "steps":[
        ("prepare", "Prepare refund packet", "refund-preparation", "REFUND_PREPARE"),
        ("approve", "Approve refund", "refund-approval", "REFUND_APPROVE"),
        ("release", "Release payment", "payout-execution", "PAYOUT_RELEASE")], "separation":[("approve","release")], "docs":["Refund operations playbook v3", "Finance separation-of-duties policy"], "decision":"High-value refunds require independent authorization"},
    {"id":"vendor-onboarding", "name":"High-risk vendor onboarding", "department":"Operations", "criticality":"High", "description":"Vet and approve third-party vendors before platform provisioning.", "owner":"Operations", "steps":[
        ("review", "Complete due diligence", "vendor-review", "VENDOR_REVIEW"),
        ("approve", "Authorize new vendor", "vendor-approval", "VENDOR_APPROVE"),
        ("provision", "Provision vendor account", "vendor-provisioning", "VENDOR_CREATE")], "separation":[("approve","provision")], "docs":["Vendor intake SOP", "Third-party risk policy"], "decision":"Vendor onboarding requires maker-checker approval"},
    {"id":"production-hotfix", "name":"Emergency production hotfix", "department":"Engineering", "criticality":"Critical", "description":"Ship urgent patches without bypassing independent release approval.", "owner":"Engineering", "steps":[
        ("triage", "Validate incident severity", "incident-triage", "INCIDENT_VIEW"),
        ("approve", "Authorize emergency release", "release-approval", "RELEASE_APPROVE"),
        ("deploy", "Execute production deploy", "deployment-execution", "DEPLOY_PROD")], "separation":[("approve","deploy")], "docs":["Emergency change runbook", "Production access review"], "decision":"Emergency deployments need separation of duties"},
    {"id":"payroll-release", "name":"Monthly payroll release", "department":"People", "criticality":"Critical", "description":"Review, authorize and transmit the employee payroll batch.", "owner":"People", "steps":[
        ("review", "Reconcile payroll batch", "payroll-review", "PAYROLL_REVIEW"),
        ("approve", "Authorize payroll", "payroll-approval", "PAYROLL_APPROVE"),
        ("release", "Release salary batch", "salary-release", "SALARY_RELEASE")], "separation":[("approve","release")], "docs":["Monthly payroll control SOP", "Treasury cut-off times"], "decision":"Payroll approval must be separate from release"},
    {"id":"customer-data-export", "name":"Restricted customer-data export", "department":"Security", "criticality":"High", "description":"Review privacy requirements before releasing customer data extracts.", "owner":"Security", "steps":[
        ("privacy", "Verify lawful data request", "privacy-review", "PRIVACY_REVIEW"),
        ("approve", "Authorize data movement", "export-approval", "EXPORT_APPROVE"),
        ("execute", "Deliver approved export", "export-execution", "EXPORT_EXECUTE")], "separation":[("approve","execute")], "docs":["Data export policy", "Privacy evidence checklist"], "decision":"All exports require scoped privacy approval"},
]



def demo_snapshot(workflow_id: str) -> dict:
    """Pure-Python fixture used ONLY in unit tests. Live API always reads FalkorDB."""
    flow = next(w for w in WORKFLOWS if w["id"] == workflow_id)
    people = []
    for identifier, name, team, role, skills, grants, expired in ROSTER:
        people.append({"id": identifier, "name": name, "team": team, "role": role, "active": True,
                       "skills": skills, "permissions": {p: ("EXPIRED" if p in expired else "ACTIVE") for p in grants}})
    return {"workflow": {k:v for k,v in flow.items() if k not in ("steps", "separation", "docs")},
            "steps": [{"id": f"{workflow_id}:{sid}", "short_id": sid, "name": n, "position": i+1, "skill":sk, "permission":perm} for i,(sid,n,sk,perm) in enumerate(flow["steps"])],
            "separation": [[f"{workflow_id}:{a}", f"{workflow_id}:{b}"] for a,b in flow["separation"]],
            "people": people,
            "documents": flow["docs"], "decision": flow["decision"]}
