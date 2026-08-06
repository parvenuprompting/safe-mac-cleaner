import subprocess


def reveal_in_finder(path: str) -> None:
    subprocess.run(["open", "-R", path], check=False)


def empty_trash() -> tuple[bool, str]:
    result = subprocess.run(
        ["osascript", "-e", 'tell application "Finder" to empty trash'],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False, result.stderr.strip() or "Finder kon de Prullenbak niet legen."
    return True, ""
