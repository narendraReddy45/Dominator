from pydantic_settings import BaseSettings, SettingsConfigDict


class _Base(BaseSettings):
    model_config = SettingsConfigDict(env_ignore_empty=True)


class Settings(_Base):
    upstream_branch: str = "master"
    sync_branch: str     = "chore/sync-upstream"
    base_branch: str     = "master"
    github_repository: str = ""

    @property
    def upstream_ref(self) -> str:
        return f"upstream/{self.upstream_branch}"

    @property
    def origin_base_ref(self) -> str:
        return f"origin/{self.base_branch}"


class CheckSettings(_Base):
    force_sync: bool = False


class PrBodySettings(_Base):
    has_conflicts: bool  = False
    is_ff: bool          = True
    conflict_files: str  = ""
    conflict_count: int  = 0
    commit_count: str    = "?"
    oldest_date: str     = ""
    newest_date: str     = ""
    diffstat: str        = ""
    event_name: str      = ""
    run_number: str      = ""
    run_url: str         = ""


class UpsertPrSettings(_Base):
    has_conflicts: bool = False
    commit_count: str   = "?"
    oldest_date: str    = ""
    newest_date: str    = ""
    prev_sha: str       = ""


class SummarySettings(_Base):
    skip: bool          = False
    dry_run: bool       = False
    has_conflicts: bool = False
    commit_count: str   = ""   # "" = check step never ran; "0" = ran and found nothing
    diffstat: str       = ""
    pr_url: str         = ""
    pr_action: str      = ""
