#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/constants.sh"

# An empty group means a build silently produced nothing -- fail before the globs below crash on it.
require_dist_populated() {
  local group
  for group in tarballs binaries; do
    if [[ -z "$(ls -A "$DIST_DIR/$group" 2>/dev/null)" ]]; then
      echo "::error::dist/$group is missing or empty -- nothing to publish"
      exit 1
    fi
  done
}

# Flat names for manual download: <name>-<platform>-<version>.
stage_github_assets() {
  local out="$DIST_DIR/github" dir f platform
  rm -rf "$out"
  mkdir -p "$out"
  for f in "$DIST_DIR"/tarballs/*.tar.gz; do
    cp -p "$f" "$out/$(basename "${f%.tar.gz}")-${VERSION}.tar.gz"
  done
  for dir in "$DIST_DIR"/binaries/*/; do
    platform="$(basename "$dir")"
    for f in "$dir"*; do
      cp -p "$f" "$out/$(basename "$f")-${platform}-${VERSION}"
    done
  done
  (cd "$out" && sha256sum ./* | sed 's#  \./#  #' >SHA256SUMS)
}

compute_checksums() {
  require_dist_populated
  (cd "$DIST_DIR" && sha256sum tarballs/* binaries/*/* >SHA256SUMS.tmp && mv SHA256SUMS.tmp SHA256SUMS)
  cat "$DIST_DIR/SHA256SUMS"
}
