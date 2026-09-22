"""Local routing policy; model output never executes an action."""
from catalog import CATALOG

POLICY_VERSION = "1.0.0"
# Initial conservative thresholds, not a claim of domain calibration.
SUPPORT_PROBABILITY = 0.95
SUPPORT_CONFIDENCE = 0.90
RISK_CLEAR = 0.05
RISK_BLOCK = 0.90
ORDER = {"pass": 0, "review": 1, "blocked": 2, "error": 3}


def combine(statuses):
    return max(statuses, key=ORDER.get) if statuses else "review"


def evaluate(unit, answers):
    details = []
    for key, answer in answers.items():
        policy = CATALOG[key]["policy"]
        if policy == "priority":
            details.append({"question": key, "status": "diagnostic", "reason": "priority_never_grants_pass"})
            continue
        if policy == "risk":
            p = answer["noul"]
            status = "pass" if p <= RISK_CLEAR else "blocked" if p >= RISK_BLOCK else "review"
        else:
            choice = answer["choice"]
            confident = answer["confidence"] >= SUPPORT_CONFIDENCE and answer["probabilities"][choice] >= SUPPORT_PROBABILITY
            status = "pass" if confident and choice == "adequate" else "blocked" if confident and choice == "inadequate" else "review"
        details.append({"question": key, "status": status, "reason": "threshold_policy"})
    if not unit["complete"]:
        details.append({"question": None, "status": "review", "reason": "coverage_incomplete"})
    if unit["risk"] == "high":
        details.append({"question": None, "status": "review", "reason": "high_risk_requires_human"})
    if any(s["kind"] == "summary" for s in unit["sources"]):
        details.append({"question": None, "status": "review", "reason": "summary_requires_primary_evidence_review"})
    return {"unit_id": unit["id"], "status": combine([d["status"] for d in details if d["status"] != "diagnostic"]), "details": details}


def deterministic_status(manifest):
    states = [c["status"] for c in manifest["checks"]]
    return "blocked" if "failed" in states else "review" if "unknown" in states else "pass"
