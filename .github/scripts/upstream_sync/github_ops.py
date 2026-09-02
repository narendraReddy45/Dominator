import json

from .settings import Settings, UpsertPrSettings
from .utils import PR_BODY_FILE, gh, set_output


def ensure_labels() -> None:
    for name, description, color in [
        ("upstream-sync", "Automated PR syncing commits from Cloud-Foundations/Dominator", "0075ca"),
        ("conflicts",     "PR has merge conflicts requiring manual resolution",              "d93f0b"),
    ]:
        gh("label", "create", name, "--description", description, "--color", color, "--force")


def _find_open_pr(cfg: Settings) -> dict | None:
    raw = gh(
        "pr", "list",
        "--head",  cfg.sync_branch,
        "--base",  cfg.base_branch,
        "--state", "open",
        "--limit", "1",
        "--json",  "number,url",
        "--jq",    ".[0] // empty",
    )
    return json.loads(raw) if raw else None


def _apply_pr_state(cfg: Settings, inputs: UpsertPrSettings, pr_number: str) -> None:
    if inputs.has_conflicts:
        gh("api", f"repos/{cfg.github_repository}/pulls/{pr_number}",
           "--method", "PATCH", "--field", "draft=true", "--silent", check=False)
        gh("pr", "edit", pr_number, "--add-label", "conflicts")
    else:
        gh("pr", "ready", pr_number, check=False)
        gh("pr", "edit",  pr_number, "--remove-label", "conflicts", check=False)


def _update_pr(cfg: Settings, inputs: UpsertPrSettings, pr_number: str, title: str) -> None:
    gh(
        "pr", "edit", pr_number,
        "--title",     title,
        "--body-file", str(PR_BODY_FILE),
        "--add-label", "upstream-sync",  # re-add in case it was manually removed
    )
    _apply_pr_state(cfg, inputs, pr_number)

    # Comment so reviewers know the branch was updated with new upstream commits.
    # This is especially important when the PR was already approved — the approval
    # may be auto-dismissed by GitHub (if "Dismiss stale reviews" is on), but the
    # comment makes the update explicit regardless of repo settings.
    comment = f"Updated by upstream-sync: {inputs.commit_count} commit(s) now queued from upstream."
    if inputs.run_url:
        comment += f"\n\nWorkflow run: {inputs.run_url}"
    gh("pr", "comment", pr_number, "--body", comment)


def upsert_pr() -> None:
    cfg    = Settings()
    inputs = UpsertPrSettings()

    title = (
        f"chore: sync upstream Cloud-Foundations/Dominator"
        f" ({inputs.oldest_date} to {inputs.newest_date}, {inputs.commit_count} commits)"
    )

    existing = _find_open_pr(cfg)

    if existing:
        pr_number = str(existing["number"])
        pr_url    = existing["url"]
        _update_pr(cfg, inputs, pr_number, title)
        action = "updated"
    else:
        cmd = [
            "pr", "create",
            "--head",      cfg.sync_branch,
            "--base",      cfg.base_branch,
            "--title",     title,
            "--body-file", str(PR_BODY_FILE),
            "--label",     "upstream-sync",
        ]
        if inputs.has_conflicts:
            cmd.append("--draft")

        try:
            pr_url = gh(*cmd)
        except RuntimeError as exc:
            # Race condition: a PR appeared between our list check and the create call.
            # Fetch it and fall back to an in-place update.
            if "already exists" not in str(exc):
                raise
            existing = _find_open_pr(cfg)
            if not existing:
                raise RuntimeError("PR creation failed with 'already exists' but no open PR found") from exc
            pr_url    = existing["url"]
            pr_number = str(existing["number"])
            _update_pr(cfg, inputs, pr_number, title)
            action = "updated"
        else:
            pr_number = pr_url.rstrip("/").split("/")[-1]
            _apply_pr_state(cfg, inputs, pr_number)
            action = "created"

    set_output("pr_url",    pr_url)
    set_output("pr_number", pr_number)
    set_output("pr_action", action)

    # CONFIGURE: uncomment to auto-request reviews
    # gh("pr", "edit", pr_number, "--add-reviewer", "username1,username2")
    # gh("pr", "edit", pr_number, "--add-reviewer", "PureStorage/your-team-slug")
