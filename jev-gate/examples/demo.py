#!/usr/bin/env python3
"""Create a disposable fixture and replay synthetic Jev outcomes. No network."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import catalog
import service
import jev_gate


def fixture_response(request, choice):
    answers = {}
    for key, q in request["questions"].items():
        if q["type"] == "noul":
            answers[key] = {"type": "noul", "noul": 0.01}
        else:
            answers[key] = {"type": "choice", "choice": choice, "confidence": 0.99,
                            "probabilities": {k: .98 if k == choice else .01 for k in q["criteria"]}}
    return {"model": catalog.MODEL, "answers": answers, "usage": {"input_tokens": 200, "output_tokens": 40}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.out).resolve()
    root.mkdir(parents=True, exist_ok=False)
    repo = root / "fixture-repo"
    repo.mkdir()
    def git(*items):
        subprocess.run(["git", "-C", str(repo), *items], check=True, capture_output=True)
    git("init", "-q")
    (repo / "claims.txt").write_text("Before: We have not tested offline use.\nAfter: Offline use remains untested.\nRule: Keep factual qualifications.\n")
    git("add", "claims.txt")
    git("-c", "user.name=Jev fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "synthetic fixture")
    revision = service.revision(repo)
    def source(role, start, end):
        return {"path": "claims.txt", "sha256": service.digest((repo / "claims.txt").read_bytes()),
                "start": start, "end": end, "role": role, "kind": "primary"}
    manifest = {"schema_version": 1, "stage": "prose", "revision": revision,
                "expected_units": ["qualification"], "required_checks": ["fixture_provenance"],
                "checks": [{"id": "fixture_provenance", "status": "passed", "revision": revision, "evidence": source("rule",3,3)}],
                "units": [{"id": "qualification", "subject": "Preserving the offline testing qualification", "complete": True,
                           "risk": "standard", "sources": [source("before",1,1),source("after",2,2),source("rule",3,3)]}]}
    manifest_path = root / "manifest.json"
    jev_gate.write_new(manifest_path, manifest)
    plan = service.pack(repo, manifest)
    jev_gate.write_new(root / "plan.json", plan)
    summary = []
    for name,choice,expected in [("supported","adequate","pass"),("ambiguous","unknown","review"),("contradicted","inadequate","blocked")]:
        envelope = {"plan_sha256": service.digest(service.canonical(plan)),
                    "responses": {"qualification": fixture_response(plan["requests"][0]["request"],choice)}}
        jev_gate.write_new(root / (name + "-fixture.json"), envelope)
        result_path = root / (name + "-decision.json")
        code = jev_gate.main(["run",str(manifest_path),"--repo",str(repo),"--out",str(result_path),"--responses",str(root/(name+"-fixture.json"))])
        result = json.loads(result_path.read_text())
        assert code == 3 and result["status"] == expected and result["workflow_action"] != "continue"
        summary.append({"scenario":name,"status":result["status"],"workflow_action":result["workflow_action"],"exit":code})
    jev_gate.write_new(root/"summary.json",{"synthetic":True,"network_calls":0,"outcomes":summary})
    print(json.dumps({"fixture_directory":str(root),"network_calls":0,"synthetic":True}))


if __name__ == "__main__":
    main()
