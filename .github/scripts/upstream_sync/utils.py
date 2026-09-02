from os import environ
from pathlib import Path
from subprocess import run

_Cwd = str | Path | None


def _run_cmd(cmd: list[str], check: bool, cwd: _Cwd = None) -> str:
    proc = run(cmd, capture_output=True, text=True, cwd=cwd)
    if check and proc.returncode != 0:
        raise RuntimeError(f"{cmd[0]} {' '.join(cmd[1:])} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def git(*args: str, check: bool = True, cwd: _Cwd = None) -> str:
    return _run_cmd(["git", *args], check=check, cwd=cwd)


def git_rc(*args: str, cwd: _Cwd = None) -> int:
    return run(["git", *args], capture_output=True, cwd=cwd).returncode


def gh(*args: str, check: bool = True) -> str:
    return _run_cmd(["gh", *args], check=check)


def set_outputs(outputs: dict[str, str]) -> None:
    path = environ.get("GITHUB_OUTPUT")
    if not path:
        for k, v in outputs.items():
            print(f"  [output] {k}={v!r}")
        return
    with open(path, "a") as f:
        for key, value in outputs.items():
            if "\n" in value:
                f.write(f"{key}<<__DELIM__\n{value}\n__DELIM__\n")
            else:
                f.write(f"{key}={value}\n")


def gha_warning(msg: str) -> None:
    print(f"::warning::{msg}")


def log_rows(raw: str) -> list[str]:
    rows = []
    for entry in raw.splitlines():
        parts = entry.split("\x00", 3)
        if len(parts) != 4:
            continue
        sha, subj, author, date = parts
        safe_subj = subj.replace("|", "\\|")
        safe_author = author.replace("|", "\\|")
        rows.append(f"| `{sha}` | {safe_subj} | {safe_author} | {date} |")
    return rows


def append_summary(*lines: str) -> None:
    path = environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        print("\n".join(lines))
        return
    with open(path, "a") as f:
        f.write("\n".join(lines) + "\n")
