from .settings import Settings, CheckSettings
from .utils import git, git_rc, set_output, append_summary


def check() -> None:
    cfg    = Settings()
    inputs = CheckSettings()
    ref    = f"HEAD..{cfg.upstream_ref}"
    count  = int(git("rev-list", ref, "--count"))

    if count == 0 and not inputs.force_sync:
        set_output("skip", "true")
        set_output("commit_count", "0")
        append_summary(
            "### Fork is already up to date",
            "",
            "No new commits found in `Cloud-Foundations/Dominator` since last sync.",
        )
        return

    lines    = git("diff", "--stat", "HEAD", cfg.upstream_ref).splitlines()
    diffstat = lines[-1] if lines else "no file changes"
    dates    = git("log", ref, "--format=%ad", "--date=short").splitlines()

    set_output("skip",         "false")
    set_output("commit_count", str(count))
    set_output("diffstat",     diffstat)
    set_output("oldest_date",  dates[-1] if dates else "")
    set_output("newest_date",  dates[0]  if dates else "")


def detect_conflicts() -> None:
    cfg = Settings()
    try:
        git("checkout", "-B", "_conflict_check", cfg.base_branch, "--quiet")

        is_ff = git_rc("merge-base", "--is-ancestor", "HEAD", cfg.upstream_ref) == 0
        set_output("fast_forward", "true" if is_ff else "false")
        if not is_ff:
            print("::warning::Upstream may have rewritten history (non-fast-forward).")

        git("merge", cfg.upstream_ref, "--no-commit", "--no-ff", "--quiet", check=False)

        raw = git("ls-files", "-u")
        if not raw:
            set_output("has_conflicts",  "false")
            set_output("conflict_count", "0")
            set_output("conflict_files", "")
        else:
            files = sorted({line.split("\t", 1)[1] for line in raw.splitlines()})
            set_output("has_conflicts",  "true")
            set_output("conflict_count", str(len(files)))
            set_output("conflict_files", "\n".join(files))

    finally:
        git("merge",    "--abort",                  check=False)
        git("checkout", cfg.base_branch, "--quiet", check=False)
        git("branch",   "-D", "_conflict_check",    check=False)
