"""Adapter failures must never become evidence of correctness."""
import copy
import importlib.util
from pathlib import Path
import sys

import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import supercov_evidence as adapter


def reports():
    def wrap(command, data):
        return {'schemaVersion': 1, 'ok': True, 'command': command, 'data': {'run': 'run_123', **data}}
    return {'summary': wrap('coverage.summary', {'command': ['node', '--test'], 'testExitCode': 0,
            'valid': True, 'stale': False, 'measurement': {'complete': True},
            'coverage': {k: {'covered': 1, 'total': 2, 'percentage': 50} for k in ('lines', 'statements', 'functions', 'branches')},
            'sourceScope': {'language': 'javascript'}}),
            'gaps': wrap('coverage.gaps', {'gaps': []}),
            'assertions': wrap('coverage.assertions', {'items': [], 'summary': {'status': 'notAssessed'}})}


def test_no_false_assertion_or_workflow_pass():
    result = adapter.summarize(reports(), 'run_123', ['node', '--test'], 0)
    assert result['assertion_summary']['status'] == 'notAssessed'
    assert result['coverage']['lines']['percentage'] == 50
    assert 'workflow_action' not in result


@pytest.mark.parametrize('field,value', [('stale', True), ('valid', False)])
def test_stale_or_invalid_is_unknown(field, value):
    raw = reports(); raw['summary']['data'][field] = value
    result = adapter.summarize(raw, 'run_123', ['node', '--test'], 0)
    assert result['test_status'] == result['measurement_status'] == 'unknown'


def test_failed_test_preserved():
    raw = reports(); raw['summary']['data']['testExitCode'] = 1
    assert adapter.summarize(raw, 'run_123', ['node', '--test'], 1)['test_status'] == 'failed'


@pytest.mark.parametrize('kind', ['run', 'command', 'schema', 'exit', 'missing'])
def test_reject_mismatched_evidence(kind):
    raw = reports()
    if kind == 'run': raw['gaps']['data']['run'] = 'run_other'
    if kind == 'command': raw['summary']['data']['command'] = ['true']
    if kind == 'schema': raw['summary']['schemaVersion'] = 2
    if kind == 'exit': raw['summary']['data']['testExitCode'] = 1
    if kind == 'missing': del raw['summary']['data']['measurement']
    with pytest.raises(adapter.service.GateError):
        adapter.summarize(raw, 'run_123', ['node', '--test'], 0)


def test_incomplete_measurement_is_unknown():
    raw = reports(); raw['summary']['data']['measurement']['complete'] = False
    assert adapter.summarize(raw, 'run_123', ['node', '--test'], 0)['measurement_status'] == 'unknown'


def test_new_questions_cannot_grant_enforced_pass():
    import catalog, policy
    answers = {key: {'type': 'noul', 'noul': 0.01} for key, spec in catalog.CATALOG.items() if spec['stage'] == 'change-risk'}
    result = policy.evaluate({'id': 'x', 'complete': True, 'risk': 'standard', 'sources': []}, answers)
    assert result['status'] == 'review'
    assert any(d['reason'] == 'uncalibrated_change_risk' for d in result['details'])


def test_invalid_coverage_denominator():
    raw = reports(); raw['summary']['data']['coverage']['lines']['total'] = 0
    with pytest.raises(adapter.service.GateError):
        adapter.summarize(raw, 'run_123', ['node', '--test'], 0)


def test_untracked_input_changes_binding(tmp_path):
    import subprocess
    def git(*args): subprocess.run(['git', '-C', str(tmp_path), *args], check=True, capture_output=True)
    git('init', '-q')
    (tmp_path/'source.txt').write_text('original')
    git('add', '.'); git('-c', 'user.name=Fixture', '-c', 'user.email=f@example.invalid', 'commit', '-qm', 'fixture')
    before = adapter.snapshot(tmp_path)
    (tmp_path/'config.json').write_text('{}')
    assert adapter.snapshot(tmp_path) != before


def test_measurement_subprocess_does_not_receive_jev_key(tmp_path, monkeypatch):
    monkeypatch.setenv('TYPESAFE_API_KEY', 'fake-test-only')
    out = tmp_path/'output'
    code = adapter.invoke([sys.executable, '-c', 'import os; print("TYPESAFE_API_KEY" in os.environ)'], tmp_path, out, 10)
    assert code == 0 and out.read_text().strip() == 'False'


@pytest.mark.parametrize('failure', ['changed-input', 'ambiguous-run'])
def test_collection_rejects_changes_and_concurrent_runs(tmp_path, monkeypatch, failure):
    import subprocess
    def git(*args): subprocess.run(['git', '-C', str(tmp_path), *args], check=True, capture_output=True)
    git('init', '-q')
    (tmp_path/'.gitignore').write_text('.artifacts/\n.supercov/\n')
    (tmp_path/'source.txt').write_text('original')
    git('add', '.'); git('-c', 'user.name=Fixture', '-c', 'user.email=f@example.invalid', 'commit', '-qm', 'fixture')
    def invoke(argv, root, out, timeout):
        if '--version' in argv:
            out.write_text(adapter.VERSION); return 0
        if '--' in argv:
            (root/'.supercov/runs/run_123').mkdir(parents=True)
            if failure == 'ambiguous-run': (root/'.supercov/runs/run_456').mkdir()
            out.write_text('test log'); return 0
        import json
        key = out.stem
        out.write_text(json.dumps(reports()[key]))
        if key == 'assertions': (root/'source.txt').write_text('changed')
        return 0
    monkeypatch.setattr(adapter, 'invoke', invoke)
    with pytest.raises(adapter.service.GateError):
        adapter.collect(tmp_path, '/unused', tmp_path/'.artifacts/test', ['node', '--test'], 10)
    assert not (tmp_path/'.artifacts/test/report.json').exists()
