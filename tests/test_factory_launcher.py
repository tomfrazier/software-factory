import os
from pathlib import Path
import shutil
import subprocess
import sys

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/factory-python.sh'


def launch(tmp_path, secret=None, override=None):
    (tmp_path/'scripts').mkdir()
    shutil.copy2(SCRIPT,tmp_path/'scripts/factory-python.sh')
    (tmp_path/'.venv/bin').mkdir(parents=True)
    (tmp_path/'.venv/bin/python').symlink_to(sys.executable)
    if secret is not None:
        (tmp_path/'.secrets').mkdir()
        (tmp_path/'.secrets/typesafe-api-key').write_text(secret)
    env=dict(os.environ)
    env.pop('TYPESAFE_API_KEY',None)
    if override is not None:env['TYPESAFE_API_KEY']=override
    return subprocess.run(['bash',str(tmp_path/'scripts/factory-python.sh'),'-c',
                           'import os; print(os.environ.get("TYPESAFE_API_KEY", "missing"))'],
                          capture_output=True,text=True,env=env,check=True).stdout.strip()


def test_reads_raw_key_without_final_newline(tmp_path):
    assert launch(tmp_path,'fixture-key')=='fixture-key'


def test_existing_environment_wins(tmp_path):
    assert launch(tmp_path,'file-key','environment-key')=='environment-key'


def test_secret_is_not_executable_shell(tmp_path):
    marker=tmp_path/'must-not-exist'
    raw='$(touch '+str(marker)+')'
    assert launch(tmp_path,raw)==raw
    assert not marker.exists()


def test_missing_file_keeps_offline_runs_usable(tmp_path):
    assert launch(tmp_path)=='missing'
