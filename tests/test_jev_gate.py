"""Offline contract and fail-closed tests. No real TypeSafe calls."""
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import urllib.error

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "jev-gate" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import catalog
import policy
import service
import jev_gate


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.fixture
def case(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "notes.txt").write_text("Before: The test was not run.\nAfter: The test was not run.\nRule: Preserve qualifications.\n")
    git(tmp_path, "add", "notes.txt")
    git(tmp_path, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
    rev = service.revision(tmp_path)
    def src(role, start=1, end=3):
        return {"path": "notes.txt", "sha256": service.digest((tmp_path / "notes.txt").read_bytes()),
                "start": start, "end": end, "role": role, "kind": "primary"}
    manifest = {"schema_version": 1, "stage": "prose", "revision": rev,
                "expected_units": ["claim"], "required_checks": ["source_verified"],
                "checks": [{"id": "source_verified", "status": "passed", "revision": rev, "evidence": src("rule")}],
                "units": [{"id": "claim", "subject": "The test qualification", "complete": True, "risk": "standard",
                           "sources": [src("before",1,1), src("after",2,2), src("rule",3,3)]}]}
    return tmp_path, manifest


def response(request, choice="adequate", risk=0.01):
    answers = {}
    for key, q in request["questions"].items():
        if q["type"] == "choice":
            answers[key] = {"type": "choice", "choice": choice, "confidence": 0.99,
                            "probabilities": {k: 0.98 if k == choice else 0.01 for k in q["criteria"]}}
        elif q["type"] == "noul":
            answers[key] = {"type": "noul", "noul": risk}
        else:
            answers[key] = {"type": "score", "score": 1.0, "confidence": 1.0,
                            "legend": {str(i):v for i,v in enumerate(q["criteria"])},
                            "probabilities": {"0":0.0,"1":1.0,"2":0.0}}
    return {"model": catalog.MODEL, "answers": answers, "usage": {"input_tokens": 200, "output_tokens": 20}}


def evaluate(case, **kw):
    root, manifest = case
    plan = service.pack(root, manifest)
    return jev_gate.run(root, manifest, plan, api_key="test-key", mode=kw.pop("mode", "enforce"),
                        call=kw.pop("call", lambda request,key: response(request, **kw)))


def test_all_catalog_stages_match_request_schema_and_provider_limits():
    for stage in catalog.STAGES:
        qs = catalog.questions(stage)
        assert "context_sufficient" in qs and len(qs) >= 2
        request = {"model": catalog.MODEL, "state": {}, "questions": qs}
        service.validate(request, "request.schema.json")
        service.validate_response(response(request), request)


def test_pack_is_minimal_and_binds_sources(case):
    root, manifest = case
    (root / "unrelated.txt").write_text("DO NOT SEND THIS")
    plan = service.pack(root, manifest)
    text = service.canonical(plan).decode()
    assert "DO NOT SEND THIS" not in text
    assert "The test was not run" in text
    assert plan["requests"][0]["budget"]["token_count"] is None


@pytest.mark.parametrize("mutation", ["head", "diff", "source", "range", "units", "checks", "roles", "extra", "empty"])
def test_invalid_or_incomplete_manifest_cannot_pass(case, mutation):
    root, m = case
    if mutation == "head": m["revision"]["head"] = "0" * 40
    if mutation == "diff": (root / "notes.txt").write_text("changed")
    if mutation == "source": m["units"][0]["sources"][0]["sha256"] = "0" * 64
    if mutation == "range": m["units"][0]["sources"][0]["end"] = 100
    if mutation == "units": m["expected_units"].append("missing")
    if mutation == "checks": m["required_checks"].append("tests")
    if mutation == "roles": m["units"][0]["sources"].pop()
    if mutation == "extra": m["skip_validation"] = True
    if mutation == "empty": m["units"] = []
    with pytest.raises(service.GateError): service.pack(root, m)


@pytest.mark.parametrize("name", ["../notes.txt", "/etc/passwd", ".env", "private.pem", ".git/config", "node_modules/foo"])
def test_excluded_paths(case, name):
    root, _ = case
    with pytest.raises(service.GateError): service.local_path(root, name)


def test_symlink_source(case):
    root, _ = case
    (root / "link").symlink_to(root / "notes.txt")
    with pytest.raises(service.GateError): service.local_path(root, "link")


@pytest.mark.parametrize("secret", ["-----BEGIN RSA PRIVATE KEY-----", "Bearer " + "a"*24, "ghp_" + "a"*30, "password=" + "a"*24])
def test_secret_screen(secret):
    with pytest.raises(service.GateError): service.privacy_check({"text": secret})


@pytest.mark.parametrize("bad", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}', '{} garbage'])
def test_strict_json(bad):
    with pytest.raises(service.GateError): service.strict_json(bad)


def test_pair_and_total_budgets_independent():
    req = {"model":catalog.MODEL,"state":"x" * 16000,"questions":{"q":{"type":"noul","instructions":"ok"}}}
    with pytest.raises(service.GateError, match="budget"): service.budget(req)
    req["state"] = "small"
    req["questions"] = {str(i): {"type":"noul","instructions":"x" * 4000} for i in range(9)}
    with pytest.raises(service.GateError, match="budget"): service.budget(req)
    req["questions"] = {"q":{"type":"noul","instructions":"ok"}}
    assert service.budget(req)["request_bytes"] < service.REQUEST_BYTES
    req["state"] = "😀" * 1500
    with pytest.raises(service.GateError): service.budget(req)


@pytest.mark.parametrize("choice,risk,status", [("adequate",.01,"pass"),("unknown",.01,"review"),("inadequate",.01,"blocked"),("adequate",.5,"review"),("adequate",.95,"blocked")])
def test_threshold_routes(case, choice, risk, status):
    report = evaluate(case, choice=choice, risk=risk)
    assert report["status"] == status
    assert report["workflow_action"] == ("continue" if status == "pass" else "stop")
    service.validate(report,"decision.schema.json")


def test_shadow_and_replay_never_authorize(case):
    assert evaluate(case, mode="shadow")["workflow_action"] == "observe"
    root, manifest = case
    plan = service.pack(root, manifest)
    replay = {"plan_sha256": service.digest(service.canonical(plan)), "responses":{"claim":response(plan["requests"][0]["request"])}}
    report = jev_gate.run(root, manifest, plan, mode="enforce", replay=replay)
    assert report["status"] == "pass" and report["mode"] == "replay" and report["workflow_action"] != "continue"
    replay["plan_sha256"] = "0"*64
    assert jev_gate.run(root, manifest, plan, replay=replay)["status"] == "error"


@pytest.mark.parametrize("check_status,expected",[("failed","blocked"),("unknown","review")])
def test_failed_checks_make_no_calls(case, check_status, expected):
    root,m = case
    m["checks"][0]["status"] = check_status
    def never(*args): raise AssertionError("network called")
    assert evaluate(case,call=never)["status"] == expected


@pytest.mark.parametrize("flag", ["summary", "high", "incomplete"])
def test_grounding_and_risk_override_positive_answers(case,flag):
    unit = case[1]["units"][0]
    if flag == "summary": unit["sources"][0]["kind"] = "summary"
    if flag == "high": unit["risk"] = "high"
    if flag == "incomplete": unit["complete"] = False
    assert evaluate(case)["status"] == "review"


def test_does_not_average_away_bad_unit(case):
    root,m=case
    extra=copy.deepcopy(m["units"][0]);extra["id"]="other";extra["risk"]="high"
    m["units"].append(extra);m["expected_units"].append("other")
    assert evaluate(case)["status"] == "review"


@pytest.mark.parametrize("mutate", [
    lambda r:r.update(model="jev-latest"),
    lambda r:r["answers"].pop("context_sufficient"),
    lambda r:r["answers"].update(extra={"type":"noul","noul":0}),
    lambda r:r["answers"]["claim_inflation"].update(noul=True),
    lambda r:r["answers"]["claim_inflation"].update(noul=float("nan")),
    lambda r:r["answers"]["claim_inflation"].update(noul=1.1),
    lambda r:r["answers"]["context_sufficient"].update(confidence=-1),
    lambda r:r["answers"]["context_sufficient"].update(choice="invented"),
    lambda r:r["answers"]["context_sufficient"].update(probabilities={"adequate":1.0}),
    lambda r:r["answers"]["context_sufficient"]["probabilities"].update(adequate=.5),
    lambda r:r["usage"].update(input_tokens=64001),
    lambda r:r["usage"].update(input_tokens=True),
])
def test_malformed_responses_fail_closed(case,mutate):
    def call(req,key):
        r=response(req);mutate(r);return r
    assert evaluate(case,call=call)["status"] == "error"


def test_stale_during_provider_call(case):
    root,_=case
    def call(req,key):
        (root/"notes.txt").write_text("changed while provider ran")
        return response(req)
    assert evaluate(case,call=call)["status"] == "error"


def test_provider_error_retains_no_pass(case):
    def call(*args): raise service.GateError("TypeSafe HTTP 401; no decision")
    report=evaluate(case,call=call)
    assert report["status"] == "error" and report["workflow_action"] == "stop"


class Reply(io.BytesIO):
    status=200


class Opener:
    def __init__(self, items): self.items=iter(items);self.requests=[]
    def open(self,req,timeout):
        self.requests.append(req)
        item=next(self.items)
        if isinstance(item,Exception):raise item
        return Reply(service.canonical(item))


def http_error(status, retry=None):
    return urllib.error.HTTPError(service.ENDPOINT,status,"test",{"Retry-After":retry} if retry else {},io.BytesIO(b"secret-error-body"))


def test_http_contract_and_bounded_retries():
    req={"model":catalog.MODEL,"state":"x","questions":{"q":{"type":"noul","instructions":"condition"}}}
    expected={"ok":True}
    opener=Opener([http_error(429,"2"),http_error(529),expected]);delays=[]
    assert service.http_post(req,"test-key",opener=opener,sleep=delays.append)==expected
    assert delays==[2,2] and len(opener.requests)==3
    sent=opener.requests[0]
    assert sent.full_url==service.ENDPOINT and sent.method=="POST"
    assert sent.get_header("Authorization")=="Bearer test-key"
    assert service.strict_json(sent.data)==req


@pytest.mark.parametrize("status",[301,401,403,413,422,500])
def test_non_retryable_http_errors(status):
    req={"model":catalog.MODEL,"state":"x","questions":{"q":{"type":"noul","instructions":"condition"}}}
    opener=Opener([http_error(status)])
    with pytest.raises(service.GateError) as error: service.http_post(req,"test-key",opener=opener)
    assert "secret-error-body" not in str(error.value) and len(opener.requests)==1


def test_long_retry_after_and_exhaustion():
    req={"model":catalog.MODEL,"state":"x","questions":{"q":{"type":"noul","instructions":"condition"}}}
    for errors in ([http_error(429,"300")],[http_error(529)]*3):
        with pytest.raises(service.GateError): service.http_post(req,"test-key",opener=Opener(errors),sleep=lambda _:None)


def test_write_no_overwrite(tmp_path):
    p=tmp_path/"result.json"
    jev_gate.write_new(p,{"value":1})
    with pytest.raises(FileExistsError):jev_gate.write_new(p,{"value":2})
    assert json.loads(p.read_text())=={"value":1}


def test_cli_prepare_replay_and_missing_key(case, monkeypatch):
    root,manifest=case
    m=root/"manifest.json";m.write_text(json.dumps(manifest))
    args=[str(m),"--repo",str(root)]
    plan_path=root/"plan.json"
    assert jev_gate.main(["prepare",*args,"--out",str(plan_path)])==0
    plan=json.loads(plan_path.read_text());sha=service.digest(service.canonical(plan))
    fixture=root/"replay.json"
    fixture.write_text(json.dumps({"plan_sha256":sha,"responses":{"claim":response(plan["requests"][0]["request"])}}))
    assert jev_gate.main(["run",*args,"--out",str(root/"out.json"),"--responses",str(fixture)])==3
    monkeypatch.delenv("TYPESAFE_API_KEY",raising=False)
    assert jev_gate.main(["run",*args,"--out",str(root/"live.json"),"--live","--approved-plan-sha256",sha])==2
    assert not (root/"live.json").exists()


def test_catalog_snapshot_matches_executable_questions():
    path=SCRIPTS.parent / 'references' / 'questions.json'
    data=json.loads(path.read_text())
    assert data['catalog']==catalog.CATALOG
    assert data['requests_by_stage']=={s:catalog.questions(s) for s in catalog.STAGES}


def test_exact_threshold_boundaries(case):
    def call(req,key):
        r=response(req,risk=.05)
        for a in r['answers'].values():
            if a['type']=='choice':
                a.update(confidence=.9, probabilities={'adequate':.95,'inadequate':.025,'unknown':.025})
        return r
    assert evaluate(case,call=call)['status']=='pass'
    def low(req,key):
        r=call(req,key);r['answers']['context_sufficient']['confidence']=.899999
        return r
    assert evaluate(case,call=low)['status']=='review'
    assert evaluate(case,risk=.9)['status']=='blocked'


def test_unhashable_choice_and_invalid_score():
    req={'model':catalog.MODEL,'state':{},'questions':catalog.questions('test-plan')}
    r=response(req);r['answers']['context_sufficient']['choice']=[]
    with pytest.raises(service.GateError):service.validate_response(r,req)
    r=response(req);r['answers']['test_priority']['score']=0
    with pytest.raises(service.GateError):service.validate_response(r,req)
    r=response(req);r['answers']['test_priority']['legend']={'0':'made up'}
    with pytest.raises(service.GateError):service.validate_response(r,req)


def test_multi_unit_run_budget(case,monkeypatch):
    root,m=case
    monkeypatch.setattr(service,'MAX_RUN_BYTES',1)
    with pytest.raises(service.GateError,match='run budget'):service.pack(root,m)


def test_redirects_are_not_followed():
    assert service.NoRedirect().redirect_request(None,None,302,'redirect',{},'https://example.invalid') is None


def test_missing_replay_unit_and_second_request_failure(case):
    root,m=case
    second=copy.deepcopy(m['units'][0]);second['id']='second'
    m['units'].append(second);m['expected_units'].append('second')
    plan=service.pack(root,m)
    replay={'plan_sha256':service.digest(service.canonical(plan)),'responses':{'claim':response(plan['requests'][0]['request'])}}
    assert jev_gate.run(root,m,plan,replay=replay)['status']=='error'
    calls=[]
    def fail_second(req,key):
        calls.append(1)
        if len(calls)==2:raise service.GateError('provider unavailable')
        return response(req)
    result=evaluate(case,call=fail_second)
    assert result['status']=='error' and result['workflow_action']=='stop' and len(result['calls'])==1
