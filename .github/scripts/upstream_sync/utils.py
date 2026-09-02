import os
import subprocess
import sys
from pathlib import Path

PR_BODY_FILE = Path("/tmp/pr_body.md")


def _run_cmd(cmd: list[str], check: bool) -> str:
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and result.returncode != 0:
        sys.exit(f"{cmd[0]} {' '.join(cmd[1:])} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git(*args: str, check: bool = True) -> str:
    return _run_cmd(["git", *args], check=check)


def git_rc(*args: str) -> int:
    return subprocess.run(["git", *args], capture_output=True).returncode


def gh(*args: str, check: bool = True) -> str:
    return _run_cmd(["gh", *args], check=check)


def set_output(key: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        print(f"  [output] {key}={value!r}")
        return
    with open(path, "a") as f:
        if "\n" in value:
            f.write(f"{key}<<__DELIM__\n{value}\n__DELIM__\n")
        else:
            f.write(f"{key}={value}\n")


def append_summary(*lines: str) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        print("\n".join(lines))
        return
    with open(path, "a") as f:
        f.write("\n".join(lines) + "\n")
