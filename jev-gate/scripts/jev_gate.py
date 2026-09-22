#!/usr/bin/env python3
"""Prepare minimal Jev packets, then run or replay a scoped judgment audit."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import sys

from catalog import MODEL, VERSION
from policy import POLICY_VERSION, combine, deterministic_status, evaluate
from service import (GateError, canonical, digest, strict_json, validate, pack,
                     http_post, validate_response, revision)


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as out:
        out.write(canonical(value) + b"\n")


def run(root, manifest, plan, *, mode="shadow", api_key=None, replay=None, call=http_post):
    live = replay is None and api_key is not None
    report = {"schema_version": 1, "catalog_version": VERSION, "policy_version": POLICY_VERSION,
              "model": MODEL, "mode": mode if live else "replay",
              "created_at": datetime.now(timezone.utc).isoformat(), "revision": plan["revision"],
              "plan_sha256": digest(canonical(plan)), "manifest_sha256": plan["manifest_sha256"],
              "status": "error", "workflow_action": "stop", "units": [], "calls": []}
    try:
        hard = deterministic_status(manifest)
        if hard != "pass":
            report.update(status=hard, reason="deterministic_checks_not_passed")
            return report
        if not live:
            validate(replay, "replay.schema.json")
            if replay["plan_sha256"] != report["plan_sha256"]:
                raise GateError("replay does not match plan")
            if set(replay["responses"]) != {r["unit_id"] for r in plan["requests"]}:
                raise GateError("replay has missing or extra units")
        for unit, packet in zip(manifest["units"], plan["requests"]):
            if pack(root, manifest) != plan:
                raise GateError("inputs changed during evaluation")
            raw = call(packet["request"], api_key) if live else replay["responses"][unit["id"]]
            answers = validate_response(raw, packet["request"])
            report["calls"].append({"unit_id": unit["id"], "request_sha256": packet["request_sha256"],
                                    "budget": packet["budget"], "response": raw})
            report["units"].append(evaluate(unit, answers))
        if pack(root, manifest) != plan:
            raise GateError("inputs changed during evaluation")
        report["status"] = combine([u["status"] for u in report["units"]])
        report["workflow_action"] = "continue" if live and mode == "enforce" and report["status"] == "pass" else "stop" if mode == "enforce" else "observe"
    except (GateError, OSError) as exc:
        report.update(status="error", workflow_action="stop", reason=str(exc) if isinstance(exc, GateError) else "local I/O failure")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["snapshot", "prepare", "run"])
    parser.add_argument("manifest", nargs="?")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--out")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--responses", help="Offline replay envelope; never authorizes continuation")
    parser.add_argument("--approved-plan-sha256")
    parser.add_argument("--mode", choices=["shadow", "enforce"], default="shadow")
    args = parser.parse_args(argv)
    try:
        root = Path(args.repo).resolve()
        if args.command == "snapshot":
            print(canonical(revision(root)).decode())
            return 0
        if not args.manifest or not args.out:
            raise GateError("manifest and --out are required")
        if Path(args.out).exists():
            raise GateError("output already exists; choose a new run path")
        manifest_path = Path(args.manifest)
        if manifest_path.stat().st_size > 1_000_000:
            raise GateError("manifest too large")
        manifest = strict_json(manifest_path.read_bytes())
        plan = pack(root, manifest)
        plan_sha = digest(canonical(plan))
        if args.command == "prepare":
            if args.live or args.responses:
                raise GateError("prepare does not call the API or consume responses")
            write_new(args.out, plan)
            print(canonical({"status": "prepared", "plan_sha256": plan_sha, "requests": len(plan["requests"]), "out": args.out}).decode())
            return 0
        if args.live == bool(args.responses):
            raise GateError("choose exactly one of --live or --responses")
        if args.live and args.approved_plan_sha256 != plan_sha:
            raise GateError("review the prepared plan and supply its --approved-plan-sha256")
        api_key = os.environ.get("TYPESAFE_API_KEY") if args.live else None
        if args.live and not api_key:
            raise GateError("TYPESAFE_API_KEY is not set; no request sent")
        replay = None
        if args.responses:
            path = Path(args.responses)
            if path.stat().st_size > 4_000_000:
                raise GateError("replay too large")
            replay = strict_json(path.read_bytes())
        report = run(root, manifest, plan, mode=args.mode, api_key=api_key, replay=replay)
        validate(report, "decision.schema.json")
        write_new(args.out, report)
        print(canonical({k: report[k] for k in ("status", "mode", "workflow_action", "plan_sha256")}).decode())
        # Only an enforced, live pass has a success exit code. Prepare is not a gate.
        return 0 if report["workflow_action"] == "continue" else 2 if report["status"] == "error" else 3
    except (GateError, OSError, ValueError) as exc:
        message = str(exc) if isinstance(exc, GateError) else "local I/O or input failure"
        print(canonical({"status": "error", "workflow_action": "stop", "reason": message}).decode())
        return 2


if __name__ == "__main__":
    sys.exit(main())
