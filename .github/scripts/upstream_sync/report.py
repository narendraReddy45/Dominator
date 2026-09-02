from datetime import datetime, timezone
from pathlib import Path

from .settings import Settings, PrBodySettings, SummarySettings
from .utils import PR_BODY_FILE, append_summary, git

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _commit_table(base_ref: str, upstream_ref: str) -> str:
    return git(
        "log", f"{base_ref}..{upstream_ref}",
        "--pretty=format:| `%h` | %s | %an | %ad |", "--date=short",
    ).rstrip("\n")


def build_pr_body() -> None:
    from jinja2 import Environment, FileSystemLoader

    cfg    = Settings()
    inputs = PrBodySettings()

    status = (
        "CONFLICTS DETECTED -- draft PR, manual resolution required before merging"
        if inputs.has_conflicts else
        "Clean merge -- ready for review and merge"
    )

    env = Environment(
        loader=FileSystemLoader(_TEMPLATES_DIR),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    PR_BODY_FILE.write_text(env.get_template("pr_body.md.j2").render(
        sync_date      = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        status         = status,
        is_ff          = inputs.is_ff,
        has_conflicts  = inputs.has_conflicts,
        conflict_files = inputs.conflict_files,
        conflict_count = inputs.conflict_count,
        commit_count   = inputs.commit_count,
        oldest_date    = inputs.oldest_date,
        newest_date    = inputs.newest_date,
        diffstat       = inputs.diffstat,
        event_name     = inputs.event_name,
        run_number     = inputs.run_number,
        run_url        = inputs.run_url,
        sync_branch    = cfg.sync_branch,
        commit_table   = _commit_table(cfg.origin_base_ref, cfg.upstream_ref),
    ), encoding="utf-8")


def write_summary() -> None:
    inputs = SummarySettings()

    if inputs.skip:
        return

    if inputs.dry_run:
        conflict_note = (
            "Conflicts would be detected -- PR would open as draft."
            if inputs.has_conflicts else
            "Clean merge -- PR would open ready for review."
        )
        append_summary(
            "### Dry run -- no PR created",
            "",
            f"**{inputs.commit_count}** new commit(s) found ({inputs.diffstat}).",
            "",
            conflict_note,
            "",
            "Re-run with Dry run unchecked to create the actual PR.",
        )
        return

    if inputs.commit_count == "":
        # check step never produced output — an earlier step failed
        append_summary("### Sync did not complete", "", "Check the workflow logs for details.")
        return

    if inputs.commit_count == "0":
        append_summary(
            "### Already up to date",
            "",
            "Fork is fully synced with upstream. No PR created.",
        )
        return

    if not inputs.pr_url:
        append_summary("### Sync did not complete", "", "Check the workflow logs for details.")
        return

    label = inputs.pr_action.capitalize() if inputs.pr_action else "Created"
    append_summary(
        f"### PR {label}: [{inputs.pr_url}]({inputs.pr_url})",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Commits   | {inputs.commit_count} |",
        f"| Changes   | {inputs.diffstat} |",
        f"| Conflicts | {inputs.has_conflicts} |",
        f"| Draft     | {inputs.has_conflicts} |",
    )
