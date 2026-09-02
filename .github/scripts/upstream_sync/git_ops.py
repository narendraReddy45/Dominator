from .constants import CONFLICT_WORKTREE
from .settings import CheckSettings, Settings
from .utils import append_summary, gha_warning, git, git_rc, set_outputs


def check() -> None:
    cfg = Settings()
    inputs = CheckSettings()
    ref = f"{cfg.origin_base_ref}..{cfg.upstream_ref}"
    raw = git("rev-list", ref, "--count")
    try:
        count = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"unexpected output from git rev-list: {raw!r}") from exc

    if count == 0 and not inputs.force_sync:
        set_outputs({"skip": "true", "commit_count": "0"})
        append_summary(
            "### Fork is already up to date",
            "",
            f"No new commits found in `{cfg.upstream_repo_name}` since last sync.",
        )
        return

    # Commits exist in the log but may have been squash-merged or cherry-picked into
    # the fork. Compare actual trees so we don't create a no-op PR.
    if (
        not inputs.force_sync
        and git_rc("diff", "--quiet", cfg.origin_base_ref, cfg.upstream_ref) == 0
    ):
        set_outputs({"skip": "true", "commit_count": "0"})
        append_summary(
            "### Fork is already up to date",
            "",
            f"No effective changes from `{cfg.upstream_repo_name}` "
            "(upstream commits appear squash-merged or cherry-picked into the fork).",
        )
        return

    lines = git("diff", "--stat", cfg.origin_base_ref, cfg.upstream_ref).splitlines()
    diffstat = lines[-1] if lines else "no file changes"
    dates = git("log", ref, "--format=%ad", "--date=short").splitlines()

    set_outputs({
        "skip": "false",
        "commit_count": str(count),
        "diffstat": diffstat,
        "oldest_date": dates[-1] if dates else "",
        "newest_date": dates[0] if dates else "",
    })


def detect_conflicts() -> None:
    cfg = Settings()
    try:
        git("worktree", "add", "--detach", CONFLICT_WORKTREE, cfg.origin_base_ref)

        is_ff = git_rc("merge-base", "--is-ancestor", cfg.origin_base_ref, cfg.upstream_ref) == 0
        if not is_ff:
            gha_warning("Fork's master has diverged from upstream — this will be a merge commit, not a fast-forward.")

        merge_rc = git_rc(
            "merge", cfg.upstream_ref, "--no-commit", "--no-ff", "--quiet", cwd=CONFLICT_WORKTREE
        )

        raw = git("ls-files", "-u", cwd=CONFLICT_WORKTREE)
        if not raw:
            if merge_rc != 0:
                raise RuntimeError(
                    f"git merge exited {merge_rc} with no conflict markers — "
                    "possible unrelated histories or corrupt upstream ref"
                )
            set_outputs({
                "fast_forward": str(is_ff).lower(),
                "has_conflicts": "false",
                "conflict_count": "0",
                "conflict_files": "",
            })
        else:
            files = sorted({line.split("\t", 1)[1] for line in raw.splitlines()})
            set_outputs({
                "fast_forward": str(is_ff).lower(),
                "has_conflicts": "true",
                "conflict_count": str(len(files)),
                "conflict_files": "\n".join(files),
            })

    finally:
        if CONFLICT_WORKTREE.is_dir():
            git("merge", "--abort", check=False, cwd=CONFLICT_WORKTREE)
        git("worktree", "remove", "--force", CONFLICT_WORKTREE, check=False)
