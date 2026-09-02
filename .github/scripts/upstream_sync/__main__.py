import sys

from .git_ops    import check, detect_conflicts
from .github_ops import ensure_labels, upsert_pr
from .report     import build_pr_body, write_summary

COMMANDS = {
    "check":            check,
    "detect-conflicts": detect_conflicts,
    "build-pr-body":    build_pr_body,
    "ensure-labels":    ensure_labels,
    "upsert-pr":        upsert_pr,
    "write-summary":    write_summary,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(f"usage: python3 -m upstream_sync <{'|'.join(COMMANDS)}>")
    try:
        COMMANDS[sys.argv[1]]()
    except RuntimeError as exc:
        sys.exit(str(exc))
