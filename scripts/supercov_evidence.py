#!/usr/bin/env python3
"""Collect pinned Supercov evidence locally. Never calls quality or Jev."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'jev-gate' / 'scripts'))
import service

VERSION = 'supercov 1.2.0 (rust contract v1)'


def snapshot(root):
    """Bind tracked and nonignored untracked inputs, including configuration."""
    rev = service.revision(root)
    paths = service.git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard')
    records = {}
    for name in sorted(set(paths.decode().split('\0')) - {''}):
        path = root / name
        if path.is_symlink():
            raise service.GateError('symlink input is unsupported')
        if not path.exists():
            records[name] = None
        elif path.is_file():
            h = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(65536), b''):
                    h.update(block)
            records[name] = h.hexdigest()
        else:
            raise service.GateError('submodule or non-file input is unsupported')
    return {'revision': rev, 'inputs_sha256': service.digest(service.canonical(records))}


def invoke(argv, root, destination, timeout):
    env = dict(os.environ)
    env.pop('TYPESAFE_API_KEY', None)
    with destination.open('xb') as stream:
        os.chmod(destination, 0o600)
        proc = subprocess.Popen(argv, cwd=root, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, start_new_session=True)
        try:
            return proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            raise service.GateError('command timed out; evidence is incomplete')


def envelope(value, command, run):
    if (not isinstance(value, dict) or value.get('schemaVersion') != 1
            or value.get('ok') is not True or value.get('command') != command
            or not isinstance(value.get('data'), dict) or value['data'].get('run') != run):
        raise service.GateError('unsupported or mismatched Supercov report')
    return value['data']


def summarize(raw, run, command, exit_code):
    d = envelope(raw['summary'], 'coverage.summary', run)
    gaps = envelope(raw['gaps'], 'coverage.gaps', run)
    assertions = envelope(raw['assertions'], 'coverage.assertions', run)
    if d.get('command') != command or type(d.get('testExitCode')) is not int or d['testExitCode'] != exit_code:
        raise service.GateError('test command or exit status mismatch')
    for key in ('valid', 'stale'):
        if type(d.get(key)) is not bool:
            raise service.GateError('missing validity or freshness information')
    m = d.get('measurement')
    if not isinstance(m, dict) or type(m.get('complete')) is not bool:
        raise service.GateError('missing measurement status')
    if not isinstance(d.get('coverage'), dict) or not isinstance(d.get('sourceScope'), dict):
        raise service.GateError('missing coverage or source scope')
    for metric in ('lines', 'statements', 'functions', 'branches'):
        value = d['coverage'].get(metric)
        if not isinstance(value, dict) or any(type(value.get(k)) is not int or value[k] < 0 for k in ('covered', 'total')):
            raise service.GateError('invalid coverage counts')
        if value['covered'] > value['total']:
            raise service.GateError('coverage exceeds denominator')
        pct = value.get('percentage')
        if pct is not None and (type(pct) not in (int, float) or not 0 <= pct <= 100):
            raise service.GateError('invalid coverage percentage')
    if not isinstance(gaps.get('gaps'), list) or not isinstance(assertions.get('items'), list):
        raise service.GateError('missing evidence inventory')
    if not isinstance(assertions.get('summary'), dict):
        raise service.GateError('missing assertion status')
    fresh = d['valid'] and not d['stale']
    measured = fresh and m['complete']
    return {'run_id': run, 'test_command': command, 'test_exit_code': exit_code,
            'test_status': 'failed' if exit_code else 'passed' if fresh else 'unknown',
            'measurement_status': 'available' if measured else 'unknown',
            'coverage': d['coverage'], 'source_scope': d['sourceScope'], 'measurement': m,
            'assertion_summary': assertions['summary'],
            'assertion_basis': assertions.get('basis', 'unknown'),
            'gaps_returned': len(gaps['gaps']),
            'gaps_pagination': raw['gaps'].get('pagination'),
            'assertions_pagination': assertions.get('pagination'),
            'limitations': ['Coverage does not establish correctness or mutation resistance.',
                            'Assertion flow explanations are agent-assessed.',
                            'Query pages may be partial; use pinned run ID for further queries.']}


def collect(root, binary, out, command, timeout):
    if not command or command[0].startswith('-'):
        raise service.GateError('provide a test command after --')
    # Output must be ignored and inside the repo so gate manifests can reference it.
    out.relative_to(root)
    ignored = subprocess.run(['git', '-C', str(root), 'check-ignore', '-q', str(out / 'report.json')]).returncode
    if ignored != 0:
        raise service.GateError('output directory must be ignored by Git')
    out.mkdir(parents=True, exist_ok=False, mode=0o700)
    os.chmod(out, 0o700)
    if invoke([binary, '--version'], root, out / 'version.txt', 30) != 0 or (out / 'version.txt').read_text().strip() != VERSION:
        raise service.GateError('install exactly Supercov 1.2.0 with Rust contract v1')
    before = snapshot(root)
    runs = root / '.supercov' / 'runs'
    existing = set(runs.glob('run_*'))
    code = invoke([binary, '--', *command], root, out / 'execution.log', timeout)
    added = set(runs.glob('run_*')) - existing
    if len(added) != 1:
        raise service.GateError('expected one new run; concurrent or missing runs are unsupported')
    run = added.pop().name
    raw = {}
    for key, extra in [('summary', []), ('gaps', ['gaps']), ('assertions', ['assertions'])]:
        path = out / (key + '.json')
        if invoke([binary, 'runs', run, *extra, '--json'], root, path, 60) != 0:
            raise service.GateError('Supercov query failed; inspect private local logs')
        if path.stat().st_size > 8_000_000:
            raise service.GateError('report exceeds local import limit')
        raw[key] = service.strict_json(path.read_bytes())
    if snapshot(root) != before:
        raise service.GateError('inputs changed while collecting evidence')
    result = {'schema_version': 1, 'adapter_version': '1.0.0', 'supercov_version': VERSION,
              **before, **summarize(raw, run, command, code),
              'artifacts': {p.name: service.digest(p.read_bytes()) for p in out.iterdir() if p.is_file()},
              'mode': 'shadow', 'workflow_action': 'observe'}
    path = out / 'report.json'
    with path.open('x') as stream:
        os.chmod(path, 0o600)
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', required=True)
    p.add_argument('--supercov', required=True, help='Absolute path to pinned executable')
    p.add_argument('--out', required=True)
    p.add_argument('--timeout', type=int, default=600)
    p.add_argument('command', nargs=argparse.REMAINDER)
    a = p.parse_args()
    try:
        binary = str(Path(a.supercov).absolute())
        command = a.command[1:] if a.command[:1] == ['--'] else a.command
        r = collect(Path(a.repo).resolve(), binary, Path(a.out).resolve(), command, a.timeout)
        print(json.dumps({'run_id': r['run_id'], 'test_status': r['test_status'],
                          'measurement_status': r['measurement_status'], 'mode': 'shadow'}))
        return 3 if r['test_status'] == 'passed' else 1
    except (service.GateError, ValueError, OSError) as exc:
        print('Supercov evidence error: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
