import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('factory_doctor', Path(__file__).resolve().parents[1]/'scripts/factory_doctor.py')
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


def configured(monkeypatch):
    monkeypatch.setattr(doctor.importlib.metadata,'version',lambda _: '4.26.0')
    monkeypatch.setattr(doctor.shutil,'which',lambda n:'/tools/'+n)
    monkeypatch.setattr(doctor,'probe',lambda args:(0,'libx264 ass avfoundation configured'))


def test_desktop_missing_filter_fails_even_with_ffmpeg_installed(monkeypatch):
    configured(monkeypatch)
    monkeypatch.setattr(doctor,'probe',lambda args:(0,'libx264 avfoundation configured'))
    result=doctor.inspect('desktop')
    assert not result['automated_checks_passed']
    assert next(c for c in result['checks'] if c['name']=='ass_filter')['status']=='failed'


def test_headless_does_not_require_ffmpeg(monkeypatch):
    configured(monkeypatch)
    monkeypatch.setattr(doctor.shutil,'which',lambda n:None if n in ('ffmpeg','ffprobe') else '/tools/'+n)
    result=doctor.inspect('headless')
    assert result['automated_checks_passed']
    assert not result['ready_for_unattended_work']


def test_key_is_checked_without_disclosure_or_network(monkeypatch):
    configured(monkeypatch)
    monkeypatch.delenv('TYPESAFE_API_KEY',raising=False)
    assert not doctor.inspect(live=True)['automated_checks_passed']
    monkeypatch.setenv('TYPESAFE_API_KEY','sensitive-value')
    result=doctor.inspect(live=True)
    assert result['automated_checks_passed']
    assert 'sensitive-value' not in str(result)


def test_failed_auth_does_not_echo_auth_output(monkeypatch):
    configured(monkeypatch)
    monkeypatch.setattr(doctor,'probe',lambda args:(1,'secret') if args[:2]==['gh','auth'] else (0,'configured'))
    result=doctor.inspect(check_auth=True)
    assert not result['automated_checks_passed'] and 'secret' not in str(result)


smoke_spec = importlib.util.spec_from_file_location('smoke_video', Path(__file__).resolve().parents[1]/'scripts/smoke_video.py')
smoke = importlib.util.module_from_spec(smoke_spec)
smoke_spec.loader.exec_module(smoke)


def test_smoke_validates_actual_probe_result(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(smoke.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='{"format":{"duration":"1.0"},"streams":[{"codec_name":"h264","width":320,"height":180}]}'))
    assert smoke.main()==0


def test_smoke_rejects_wrong_codec(monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(smoke.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='{"format":{"duration":"1.0"},"streams":[{"codec_name":"vp9","width":320,"height":180}]}'))
    assert smoke.main()==2


def test_smoke_handles_missing_executable(monkeypatch):
    def missing(*a,**k):raise FileNotFoundError()
    monkeypatch.setattr(smoke.subprocess,'run',missing)
    assert smoke.main()==2
