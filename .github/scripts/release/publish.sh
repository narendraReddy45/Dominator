#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/constants.sh"

publish_github() {
  require_dist_populated
  local files=("$DIST_DIR"/tarballs/* "$DIST_DIR"/binaries/* "$DIST_DIR/BUILD_INFO" "$DIST_DIR/SHA256SUMS")

  if ! gh release view "$VERSION" >/dev/null 2>&1; then
    gh release create "$VERSION" --title "$VERSION" --generate-notes --verify-tag --latest "${files[@]}"
    return
  fi

  # Release exists: upload only missing assets, no-op if complete.
  local existing_assets missing=() f base
  existing_assets="$(gh release view "$VERSION" --json assets --jq '.assets[].name')"
  for f in "${files[@]}"; do
    base="$(basename "$f")"
    grep -qxF "$base" <<<"$existing_assets" || missing+=("$f")
  done

  if [[ ${#missing[@]} -eq 0 ]]; then
    echo "::notice::release $VERSION already has every expected asset -- nothing to publish"
    return
  fi
  gh release upload "$VERSION" "${missing[@]}"
}

publish_jfrog() {
  require_dist_populated
  local match_count
  match_count="$(jf rt search "${JFROG_REPO}/dominator/${VERSION}/BUILD_INFO" | jq 'length')"
  if [[ "$match_count" != "0" ]]; then
    echo "::notice::artifacts already exist under ${JFROG_REPO}/dominator/${VERSION}/ -- nothing to publish"
    return
  fi

  # --fail-no-op: jf rt upload exits 0 even when the glob matches nothing without it.
  jf rt upload "$DIST_DIR/tarballs/*" "${JFROG_REPO}/dominator/${VERSION}/tarballs/" --flat=true --fail-no-op
  jf rt upload "$DIST_DIR/binaries/*" "${JFROG_REPO}/dominator/${VERSION}/binaries/" --flat=true --fail-no-op
  jf rt upload "$DIST_DIR/SHA256SUMS" "${JFROG_REPO}/dominator/${VERSION}/" --flat=true --fail-no-op
  # BUILD_INFO is the completion marker the check above trusts -- upload it last.
  jf rt upload "$DIST_DIR/BUILD_INFO" "${JFROG_REPO}/dominator/${VERSION}/" --flat=true --fail-no-op
  # latest/ is a pointer to the current version, overwritten each release.
  local pointer
  pointer="$(mktemp)"
  printf 'version=%s\n' "$VERSION" >"$pointer"
  jf rt upload "$pointer" "${JFROG_REPO}/dominator/latest/VERSION" --flat=true --fail-no-op
  rm -f "$pointer"
}
