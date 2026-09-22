"""Context, revision checks, request budgets, and TypeSafe HTTP transport."""
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.request

from catalog import MODEL, VERSION, CATALOG, questions

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
# Operational byte limits, deliberately below both documented token limits.
# These are NOT token counts; no public Jev tokenizer was found in official docs.
PAIR_BYTES = 16_000
REQUEST_BYTES = 32_000
MAX_CALLS = 64
MAX_RUN_BYTES = 512_000
MAX_FILE_BYTES = 1_000_000
SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"


class GateError(Exception):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise GateError("duplicate JSON key")
            obj[key] = value
        return obj
    def reject(_):
        raise GateError("non-finite JSON number")
    def finite_float(raw):
        value = float(raw)
        if not math.isfinite(value):
            raise GateError("non-finite JSON number")
        return value
    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=reject, parse_float=finite_float)
    except (ValueError, UnicodeError) as exc:
        raise GateError("invalid JSON") from exc


def validate(value, name):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise GateError("install jev-gate/requirements.txt in your virtual environment") from exc
    schema = strict_json((SCHEMA_DIR / name).read_bytes())
    error = next(Draft202012Validator(schema).iter_errors(value), None)
    if error:
        # Validation errors may contain confidential input. Return only a location.
        raise GateError("schema violation at " + "/".join(map(str, error.absolute_path)))


def git(root, *args):
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False)
    if proc.returncode:
        raise GateError("git inspection failed")
    return proc.stdout


def revision(root):
    top = Path(git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if top != root.resolve():
        raise GateError("--repo must be the repository root")
    return {"head": git(root, "rev-parse", "HEAD").decode().strip(),
            "diff_sha256": digest(git(root, "diff", "--no-ext-diff", "--no-textconv", "--binary", "HEAD", "--"))}


def local_path(root, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise GateError("source path must stay within the repository")
    if any(p.lower() in (".git", ".ssh", ".secrets", "node_modules", ".venv") or p.lower().startswith(".env") for p in path.parts):
        raise GateError("excluded source path")
    if path.suffix.lower() in (".pem", ".key", ".p12", ".pfx", ".png", ".jpg", ".jpeg", ".mp4", ".pdf", ".zip"):
        raise GateError("excluded binary or credential source")
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise GateError("symlink source rejected")
    if not current.is_file() or not current.resolve().is_relative_to(root.resolve()):
        raise GateError("source is not a regular repository file")
    if current.stat().st_size > MAX_FILE_BYTES:
        raise GateError("source file too large; create a reviewed text extract")
    return current


def source(root, spec):
    raw = local_path(root, spec["path"]).read_bytes()
    if digest(raw) != spec["sha256"]:
        raise GateError("source hash changed; rebuild manifest")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise GateError("source must be UTF-8 text") from exc
    if any(ord(c) < 32 and c not in "\n\r\t" for c in text):
        raise GateError("binary/control characters in source")
    lines = text.splitlines(keepends=True)
    start, end = spec["start"], spec["end"]
    if end < start or end > len(lines):
        raise GateError("invalid excerpt range")
    excerpt = "".join(lines[start-1:end])
    return {**spec, "text": excerpt}


def privacy_check(value):
    text = canonical(value).decode("ascii")
    patterns = [r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"\bAKIA[0-9A-Z]{16}\b",
                r"\bgh[pousr]_[A-Za-z0-9]{20,}\b", r"\bgithub_pat_[A-Za-z0-9_]{20,}\b",
                r"(?i)bearer\s+[a-z0-9._-]{16,}",
                r"(?i)(?:api[_-]?key|password|secret|token)\s*[=:]\s*[^\s,;]{12,}"]
    if any(re.search(p, text) for p in patterns):
        raise GateError("possible secret in selected context; prepare a redacted extract")


def budget(request):
    state_size = len(canonical(request["state"]))
    longest = max(len(canonical(q)) for q in request["questions"].values())
    total = len(canonical(request))
    if state_size + longest > PAIR_BYTES or total > REQUEST_BYTES:
        raise GateError("context budget exceeded; split semantic units, never truncate")
    return {"state_plus_longest_question_bytes": state_size + longest,
            "request_bytes": total, "token_count": None,
            "method": "ascii-json-byte-cap-not-a-tokenizer"}


def pack(root, manifest):
    validate(manifest, "manifest.schema.json")
    if manifest["revision"] != revision(root):
        raise GateError("manifest revision is stale")
    units = manifest["units"]
    ids = [u["id"] for u in units]
    if len(ids) != len(set(ids)) or set(ids) != set(manifest["expected_units"]):
        raise GateError("missing or duplicate semantic units")
    checks = [c["id"] for c in manifest["checks"]]
    if len(checks) != len(set(checks)) or set(checks) != set(manifest["required_checks"]):
        raise GateError("missing or duplicate deterministic checks")
    for check in manifest["checks"]:
        if check["revision"] != manifest["revision"]:
            raise GateError("deterministic check revision is stale")
        source(root, check["evidence"])
    requests = []
    for unit in units:
        qs = questions(manifest["stage"])
        required = set().union(*(set(CATALOG[q]["roles"]) for q in qs))
        if not required <= {s["role"] for s in unit["sources"]}:
            raise GateError("unit lacks required source roles")
        excerpts = [source(root, s) for s in unit["sources"]]
        request = {"model": MODEL, "state": {"subject": unit["subject"], "sources": excerpts}, "questions": qs}
        privacy_check(request)
        limits = budget(request)
        requests.append({"unit_id": unit["id"], "request": request, "budget": limits,
                         "request_sha256": digest(canonical(request))})
    if len(requests) > MAX_CALLS or sum(r["budget"]["request_bytes"] for r in requests) > MAX_RUN_BYTES:
        raise GateError("run budget exceeded; split into explicitly tracked runs")
    return {"schema_version": 1, "catalog_version": VERSION,
            "manifest_sha256": digest(canonical(manifest)), "revision": manifest["revision"], "requests": requests}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def http_post(request, api_key, *, opener=None, sleep=time.sleep):
    """Only retries explicit overload/rate-limit responses; at most three attempts."""
    budget(request)
    privacy_check(request)
    opener = opener or urllib.request.build_opener(NoRedirect)
    payload = canonical(request)
    for attempt in range(3):
        req = urllib.request.Request(ENDPOINT, data=payload, method="POST",
                                     headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"})
        try:
            with opener.open(req, timeout=20) as response:
                if response.status != 200:
                    raise GateError("unexpected HTTP status")
                data = response.read(1_000_001)
                if len(data) > 1_000_000:
                    raise GateError("response too large")
                return strict_json(data)
        except urllib.error.HTTPError as exc:
            status = exc.code
            delay = 2 ** attempt
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            exc.close()
            if status not in (429, 529) or attempt == 2:
                raise GateError(f"TypeSafe HTTP {status}; no decision") from None
            if retry_after:
                try:
                    delay = max(delay, float(retry_after))
                except ValueError:
                    # Date-form retry headers require a later operator retry.
                    raise GateError("provider requested a later retry") from None
                if not math.isfinite(delay) or delay > 30:
                    raise GateError("provider requested a later retry")
            sleep(delay)
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
            raise GateError("TypeSafe transport unavailable; no decision") from None
    raise GateError("retry limit reached")


def unit_interval(number):
    return type(number) in (int, float) and math.isfinite(number) and 0 <= number <= 1


def validate_response(response, request):
    if not isinstance(response, dict) or response.get("model") != MODEL:
        raise GateError("unexpected model version")
    answers = response.get("answers")
    if not isinstance(answers, dict) or set(answers) != set(request["questions"]):
        raise GateError("missing or unexpected answer IDs")
    usage = response.get("usage")
    if not isinstance(usage, dict) or any(type(usage.get(k)) is not int or usage[k] < 0 for k in ("input_tokens", "output_tokens")):
        raise GateError("invalid usage")
    if usage["input_tokens"] > 64_000:
        raise GateError("reported token limit exceeded")
    for key, question in request["questions"].items():
        answer = answers[key]
        kind = question["type"]
        if not isinstance(answer, dict) or answer.get("type") != kind:
            raise GateError("answer type mismatch")
        if kind == "noul":
            if not unit_interval(answer.get("noul")):
                raise GateError("invalid Noul probability")
            continue
        if not unit_interval(answer.get("confidence")):
            raise GateError("invalid confidence")
        options = question["criteria"] if kind == "choice" else {str(i): s for i, s in enumerate(question["criteria"])}
        probs = answer.get("probabilities")
        if not isinstance(probs, dict) or set(probs) != set(options) or not all(unit_interval(v) for v in probs.values()):
            raise GateError("invalid probability distribution")
        if abs(sum(probs.values()) - 1) > 0.0001:
            raise GateError("probabilities do not sum to one")
        if kind == "choice":
            selected = answer.get("choice")
            if not isinstance(selected, str) or selected not in options or probs[selected] < max(probs.values()):
                raise GateError("invalid choice")
        else:
            score = answer.get("score")
            mean = sum(int(k) * p for k, p in probs.items())
            if type(score) not in (float, int) or not math.isfinite(score) or abs(score - mean) > 0.0001 or answer.get("legend") != options:
                raise GateError("invalid score or legend")
    return answers
