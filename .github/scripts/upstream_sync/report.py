from datetime import UTC, datetime

from .constants import GIT_LOG_FORMAT, PR_BODY_FILE, TEMPLATES_DIR
from .settings import PrBodySettings, Settings, SummarySettings
from .utils import append_summary, git, log_rows


def _commit_table(base_ref: str, upstream_ref: str) -> str:
    raw = git("log", f"{base_ref}..{upstream_ref}", f"--pretty={GIT_LOG_FORMAT}", "--date=short")
    return "\n".join(log_rows(raw)) if raw else ""


def build_pr_body() -> None:
    from jinja2 import Environment, FileSystemLoader

    cfg = Settings()
    inputs = PrBodySettings()

    status = (
        "CONFLICTS DETECTED -- draft PR, manual resolution required before merging"
        if inputs.has_conflicts
        else "Clean merge -- ready for review and merge"
    )

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    PR_BODY_FILE.write_text(
        env.get_template("pr_body.md.j2").render(
            sync_date=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            status=status,
            is_ff=inputs.is_ff,
            has_conflicts=inputs.has_conflicts,
            conflict_files=inputs.conflict_files,
            conflict_count=inputs.conflict_count,
            commit_count=inputs.commit_count,
            oldest_date=inputs.oldest_date,
            newest_date=inputs.newest_date,
            diffstat=inputs.diffstat,
            event_name=inputs.event_name,
            run_number=inputs.run_number,
            run_url=inputs.run_url,
            sync_branch=cfg.sync_branch,
            upstream_repo=cfg.upstream_repo_name,
            upstream_repo_url=cfg.upstream_repo_url,
            target_repo=cfg.github_repository,
            commit_table=_commit_table(cfg.origin_base_ref, cfg.upstream_ref),
        ),
        encoding="utf-8",
    )


def write_summary() -> None:
    inputs = SummarySettings()

    if inputs.skip:
        return

    if inputs.commit_count == "":
        append_summary("### Sync did not complete", "", "Check the workflow logs for details.")
        return

    if inputs.dry_run:
        conflict_note = (
            "Conflicts would be detected -- PR would open as draft."
            if inputs.has_conflicts
            else "Clean merge -- PR would open ready for review."
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
    )
