import pytest

import platform_macos
import smc_cleaner as cleaner
from models import ScanSettings


def test_validate_scan_directories_rejects_home_and_outside(tmp_path, monkeypatch):
    home = tmp_path / "home"
    inside = home / "Downloads"
    outside = tmp_path / "outside"
    inside.mkdir(parents=True)
    outside.mkdir()
    monkeypatch.setattr(cleaner, "HOME_PATH", home.resolve())

    valid, errors = cleaner.validate_scan_directories([str(inside), str(home), str(outside)])

    assert valid == [str(inside.resolve())]
    assert len(errors) == 2


def test_validate_scan_directories_removes_overlapping_roots(tmp_path, monkeypatch):
    home = tmp_path / "home"
    parent = home / "Documents"
    child = parent / "Projects"
    child.mkdir(parents=True)
    monkeypatch.setattr(cleaner, "HOME_PATH", home.resolve())

    valid, errors = cleaner.validate_scan_directories([str(child), str(parent)])

    assert errors == []
    assert valid == [str(parent.resolve())]


def test_scan_disk_filters_files_and_records_metadata(tmp_path, monkeypatch):
    home = tmp_path / "home"
    folder = home / "Downloads"
    folder.mkdir(parents=True)
    candidate = folder / "large.txt"
    candidate.write_bytes(b"x" * 2048)
    small = folder / "small.txt"
    small.write_bytes(b"x")
    monkeypatch.setattr(cleaner, "HOME_PATH", home.resolve())

    results, errors = cleaner.scan_disk([str(folder)], min_size_mb=0, min_age_days=0,
                                        age_mode="last_modified", top_n=10)

    assert errors == []
    paths = {item["path"] for item in results}
    assert str(candidate) in paths
    assert all(key in results[0] for key in ("_st_dev", "_st_ino", "_st_size", "_st_mtime_ns"))


def test_delete_files_rejects_changed_file(tmp_path, monkeypatch):
    monkeypatch.setattr(cleaner, "HOME_PATH", tmp_path.resolve())
    path = tmp_path / "candidate.txt"
    path.write_text("before")
    stat = path.stat()
    item = {
        "path": str(path),
        "size_mb": 1,
        "_st_dev": stat.st_dev,
        "_st_ino": stat.st_ino,
        "_st_size": stat.st_size,
        "_st_mtime_ns": stat.st_mtime_ns,
    }
    path.write_text("after with different content")
    monkeypatch.setattr(cleaner, "send2trash", pytest.fail)

    result = cleaner.delete_files([item])

    assert result["succeeded"] == []
    assert "gewijzigd" in result["failed"][0]["error"]


def test_delete_files_reports_success_and_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(cleaner, "HOME_PATH", tmp_path.resolve())
    good = tmp_path / "good.txt"
    good.write_text("good")
    missing = tmp_path / "missing.txt"
    calls = []

    def fake_send2trash(path):
        calls.append(path)

    monkeypatch.setattr(cleaner, "send2trash", fake_send2trash)
    result = cleaner.delete_files([
        {"path": str(good), "size_mb": 2},
        {"path": str(missing), "size_mb": 3},
    ])

    assert calls == [str(good)]
    assert result["succeeded"] == [str(good)]
    assert len(result["failed"]) == 1
    assert result["total_size_mb"] == 2


def test_scan_settings_normalizes_persisted_values():
    settings = ScanSettings.from_values("99999", "-2", "2000000", "invalid")

    assert settings.as_dict() == {
        "top_n": 10000,
        "age": 0,
        "size": 1000000,
        "mode": "last_used",
    }


def test_empty_trash_adapter_returns_command_error(monkeypatch):
    class FailedCommand:
        returncode = 1
        stderr = "Finder error"

    monkeypatch.setattr(platform_macos.subprocess, "run", lambda *args, **kwargs: FailedCommand())

    assert platform_macos.empty_trash() == (False, "Finder error")
