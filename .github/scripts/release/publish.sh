#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/constants.sh"

publish_github() {
  : "${VERSION:?}"
  local files=("$DIST_DIR"/tarballs/* "$DIST_DIR"/binaries/* "$DIST_DIR/BUILD_INFO")

  if ! gh release view "$VERSION" >/dev/null 2>&1; then
    gh release create "$VERSION" --title "$VERSION" --generate-notes --verify-tag --latest "${files[@]}"
    return
  fi

  # Release exists already -- resume by uploading only missing assets, refuse if complete.
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
  : "${VERSION:?}"
  : "${JFROG_REPO:?set the JFROG_REPO repository variable}"
  local match_count
  match_count="$(jf rt search "${JFROG_REPO}/dominator/${VERSION}/BUILD_INFO" | jq 'length')"
  if [[ "$match_count" != "0" ]]; then
    echo "::notice::artifacts already exist under ${JFROG_REPO}/dominator/${VERSION}/ -- nothing to publish"
    return
  fi

  local v
  # --fail-no-op: jf rt upload otherwise exits 0 (success) even when the glob matches nothing.
  for v in "$VERSION" latest; do
    jf rt upload "$DIST_DIR/tarballs/*" "${JFROG_REPO}/dominator/${v}/tarballs/" --flat=true --fail-no-op
    jf rt upload "$DIST_DIR/binaries/*" "${JFROG_REPO}/dominator/${v}/binaries/" --flat=true --fail-no-op
  done
  # BUILD_INFO under $VERSION must be uploaded last -- it's what the existence check above trusts.
  jf rt upload "$DIST_DIR/BUILD_INFO" "${JFROG_REPO}/dominator/latest/" --flat=true --fail-no-op
  jf rt upload "$DIST_DIR/BUILD_INFO" "${JFROG_REPO}/dominator/${VERSION}/" --flat=true --fail-no-op
}
