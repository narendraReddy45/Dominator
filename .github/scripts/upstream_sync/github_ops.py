import json

from .constants import GIT_LOG_FORMAT, LABEL_CONFLICTS, LABEL_SYNC, PR_BODY_FILE, SYNC_LABELS
from .settings import Settings, UpsertPrSettings
from .utils import gh, gha_warning, git, log_rows, set_outputs


def ensure_labels() -> None:
    for name, description, color in SYNC_LABELS:
        gh("label", "create", name, "--description", description, "--color", color, "--force")


def _find_open_pr(cfg: Settings) -> dict | None:
    raw = gh(
        "pr", "list",
        "--head", cfg.sync_branch, "--base", cfg.base_branch,
        "--state", "open", "--limit", "1",
        "--json", "number,url", "--jq", ".[0] // empty",
    )
    return json.loads(raw) if raw else None


def _apply_pr_state(cfg: Settings, inputs: UpsertPrSettings, pr_number: str) -> None:
    if inputs.has_conflicts:
        gh("api", f"repos/{cfg.github_repository}/pulls/{pr_number}",
           "--method", "PATCH", "--field", "draft=true", "--silent")
        gh("pr", "edit", pr_number, "--add-label", LABEL_CONFLICTS)
    else:
        try:
            gh("pr", "ready", pr_number)
        except RuntimeError as exc:
            # Already ready for review — not an error worth failing the step over.
            gha_warning(f"gh pr ready: {exc}")
        gh("pr", "edit", pr_number, "--remove-label", LABEL_CONFLICTS, check=False)


def _delta_comment(prev_sha: str, upstream_ref: str) -> str | None:
    raw = git("log", f"{prev_sha}..{upstream_ref}", f"--pretty={GIT_LOG_FORMAT}", "--date=short")
    if not raw:
        return None
    rows = log_rows(raw)
    if not rows:
        return None
    return (
        f"{len(rows)} new commit(s) added since the last sync update:\n\n"
        "| SHA | Message | Author | Date |\n"
        "|---|---|---|---|\n" + "\n".join(rows)
    )


def _update_pr(cfg: Settings, inputs: UpsertPrSettings, pr_number: str, title: str) -> None:
    gh("pr", "edit", pr_number,
       "--title", title, "--body-file", str(PR_BODY_FILE),
       "--add-label", LABEL_SYNC)  # re-add in case it was manually removed
    _apply_pr_state(cfg, inputs, pr_number)

    if inputs.prev_sha:
        comment = _delta_comment(inputs.prev_sha, cfg.upstream_ref)
        if comment:
            gh("pr", "comment", pr_number, "--body", comment)


def upsert_pr() -> None:
    cfg = Settings()
    inputs = UpsertPrSettings()

    title = (
        "chore: sync upstream "
        f"{cfg.upstream_repo_name} ({inputs.oldest_date} to {inputs.newest_date}, {inputs.commit_count} commits)"
    )

    existing = _find_open_pr(cfg)

    if existing:
        pr_number = str(existing["number"])
        pr_url = existing["url"]
        _update_pr(cfg, inputs, pr_number, title)
        action = "updated"
    else:
        cmd = [
            "pr", "create",
            "--head", cfg.sync_branch, "--base", cfg.base_branch,
            "--title", title, "--body-file", str(PR_BODY_FILE),
            "--label", LABEL_SYNC,
        ]
        if inputs.has_conflicts:
            cmd.append("--draft")

        try:
            pr_url = gh(*cmd)
        except RuntimeError as exc:
            # Race condition: a PR appeared between our list check and the create call.
            if "already exists" not in str(exc):
                raise
            existing = _find_open_pr(cfg)
            if not existing:
                raise RuntimeError(
                    "PR creation failed with 'already exists' but no open PR found"
                ) from exc
            pr_url = existing["url"]
            pr_number = str(existing["number"])
            _update_pr(cfg, inputs, pr_number, title)
            action = "updated"
        else:
            pr_number = pr_url.rstrip("/").split("/")[-1]
            _apply_pr_state(cfg, inputs, pr_number)
            action = "created"

    set_outputs({"pr_url": pr_url, "pr_number": pr_number, "pr_action": action})
