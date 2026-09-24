#!/usr/bin/env python3
"""Read-only factory host checks. Does not install tools or transmit repo context."""
import argparse
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys


def probe(argv):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=15)
        return p.returncode, p.stdout + p.stderr
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""


def inspect(profile="headless", live=False, check_auth=False):
    checks = []
    def add(name, ok, fix, required=True):
        checks.append({"name": name, "status": "passed" if ok else "failed" if required else "manual",
                       "required": required, "remedy": "" if ok else fix})
    add("python", sys.version_info >= (3, 10), "Use Python 3.10 or newer and recreate .venv on this Mac.")
    try:
        version = importlib.metadata.version("jsonschema")
    except importlib.metadata.PackageNotFoundError:
        version = None
    add("jsonschema", version == "4.26.0", "Install jev-gate/requirements.txt using this Python interpreter.")
    for tool in ("git", "node", "npm", "gh", "jq"):
        path = shutil.which(tool)
        code, _ = probe([path, "--version"]) if path else (1, "")
        add(tool, code == 0, "Install " + tool + " on the execution host and expose it in the factory process PATH.")
    for field in ("user.name", "user.email"):
        code, output = probe(["git", "config", "--get", field])
        add("git." + field, code == 0 and bool(output.strip()), "Configure Git " + field + " for the factory user or project.")
    add("typesafe_key_present", bool(os.environ.get("TYPESAFE_API_KEY")),
        "Set TYPESAFE_API_KEY in the Mini's factory process environment. Presence does not verify validity.", live)
    if check_auth:
        code, _ = probe(["gh", "auth", "status"])
        add("github_auth", code == 0, "Run gh auth login as the factory user on this host.")
    else:
        add("github_auth", False, "Run with --check-auth to check GitHub authentication without showing credentials.", False)
    if profile == "desktop":
        for tool in ("ffmpeg", "ffprobe"):
            path = shutil.which(tool)
            code, _ = probe([path, "-version"]) if path else (1, "")
            add(tool, code == 0, "Install ffmpeg-full and prepend its bin directory to PATH.")
        for name, flag, pattern in [("libx264", "-encoders", r"\blibx264\b"),
                                    ("ass_filter", "-filters", r"\bass\s"),
                                    ("avfoundation", "-devices", r"\bavfoundation\b")]:
            code, output = probe(["ffmpeg", "-hide_banner", flag])
            add(name, code == 0 and bool(re.search(pattern, output)),
                "Use ffmpeg-full on PATH; installing libass alone does not add a filter to an existing FFmpeg binary.")
        for tool in ("before-and-after", "agent-browser"):
            add(tool, bool(shutil.which(tool)), "Install @vercel/before-and-after and agent-browser with npm.")
        add("desktop_session_and_permissions", False,
            "Log into the Mini's GUI session, grant Screen Recording/Accessibility to the actual host app, then run a real capture and interaction test. SSH is not proof of desktop access.", False)
    else:
        add("headless_browser", False,
            "Install your chosen browser automation runtime on the Mini and run an actual browser launch/screenshot probe. Desktop video is not required for this profile.", False)
    add("agent_runtime", False, "Install and authenticate the chosen coding agent on the Mini; this repository is a skill collection, not a remote job server.", False)
    add("greptile", False, "Verify Greptile is installed on each target repository using an authorized test PR when ready.", False)
    return {"schema_version": 1, "host": platform.node(), "platform": platform.system(),
            "architecture": platform.machine(), "python": sys.executable, "profile": profile,
            "automated_checks_passed": all(c["status"] == "passed" for c in checks if c["required"]),
            "ready_for_unattended_work": False, "checks": checks,
            "tool_paths": {n: shutil.which(n) for n in ("git", "node", "ffmpeg", "ffprobe", "gh")}}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--profile", choices=["headless", "desktop"], default="headless")
    p.add_argument("--live-jev", action="store_true")
    p.add_argument("--check-auth", action="store_true")
    args = p.parse_args(argv)
    report = inspect(args.profile, args.live_jev, args.check_auth)
    print(json.dumps(report, indent=2))
    return 0 if report["automated_checks_passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
