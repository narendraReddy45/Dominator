from pathlib import Path

PR_BODY_FILE = Path("/tmp/pr_body.md")
CONFLICT_WORKTREE = Path("/tmp/_conflict_check")
TEMPLATES_DIR = Path(__file__).parent / "templates"

# NUL-separated format — NUL cannot appear in git metadata, making it safe across
# subjects with pipes, author names with commas, etc.
GIT_LOG_FORMAT = "format:%h%x00%s%x00%an%x00%ad"

LABEL_SYNC = "upstream-sync"
LABEL_CONFLICTS = "conflicts"

SYNC_LABELS = [
    (LABEL_SYNC, "Automated upstream sync PR", "0075ca"),
    (LABEL_CONFLICTS, "PR has merge conflicts requiring manual resolution", "d93f0b"),
]
