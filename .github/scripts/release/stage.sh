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

# A downloaded file carries no version of its own -- stamp it before checksums.
stamp_version() {
  require_dist_populated
  local f
  for f in "$DIST_DIR"/tarballs/*.tar.gz; do
    mv "$f" "${f%.tar.gz}-${VERSION}.tar.gz"
  done
  for f in "$DIST_DIR"/binaries/*; do
    mv "$f" "${f}-${VERSION}"
  done
}

# One file for both groups -- GitHub release assets are a flat namespace.
compute_checksums() {
  require_dist_populated
  (cd "$DIST_DIR" && sha256sum tarballs/* binaries/* | sed -E 's#  (tarballs|binaries)/#  #' >SHA256SUMS.tmp && mv SHA256SUMS.tmp SHA256SUMS)
  cat "$DIST_DIR/SHA256SUMS"
}
