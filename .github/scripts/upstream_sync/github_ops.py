import json

from .settings import Settings, UpsertPrSettings
from .utils import PR_BODY_FILE, gh, set_output


def ensure_labels() -> None:
    for name, description, color in [
        ("upstream-sync", "Automated PR syncing commits from Cloud-Foundations/Dominator", "0075ca"),
        ("conflicts",     "PR has merge conflicts requiring manual resolution",              "d93f0b"),
    ]:
        gh("label", "create", name, "--description", description, "--color", color, "--force")


def upsert_pr() -> None:
    cfg    = Settings()
    inputs = UpsertPrSettings()

    title = (
        f"chore: sync upstream Cloud-Foundations/Dominator"
        f" ({inputs.oldest_date} to {inputs.newest_date}, {inputs.commit_count} commits)"
    )

    existing_json = gh(
        "pr", "list",
        "--head",  cfg.sync_branch,
        "--base",  cfg.base_branch,
        "--state", "open",
        "--json",  "number,url",
        "--jq",    ".[0] // empty",
    )

    if existing_json:
        pr        = json.loads(existing_json)
        pr_number = str(pr["number"])
        pr_url    = pr["url"]
        action    = "updated"

        gh("pr", "edit", pr_number, "--title", title, "--body-file", str(PR_BODY_FILE))

        if inputs.has_conflicts:
            gh("api", f"repos/{cfg.github_repository}/pulls/{pr_number}",
               "--method", "PATCH", "--field", "draft=true", "--silent", check=False)
        else:
            gh("pr", "ready", pr_number, check=False)
            gh("pr", "edit",  pr_number, "--remove-label", "conflicts", check=False)
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

        pr_url    = gh(*cmd)
        pr_number = pr_url.rstrip("/").split("/")[-1]
        action    = "created"

    if inputs.has_conflicts:
        gh("pr", "edit", pr_number, "--add-label", "conflicts")

    set_output("pr_url",    pr_url)
    set_output("pr_number", pr_number)
    set_output("pr_action", action)

    # CONFIGURE: uncomment to auto-request reviews
    # gh("pr", "edit", pr_number, "--add-reviewer", "username1,username2")
    # gh("pr", "edit", pr_number, "--add-reviewer", "PureStorage/your-team-slug")
