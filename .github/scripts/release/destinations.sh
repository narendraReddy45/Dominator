#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/constants.sh"

is_supported_destination() {
  local d="$1" s
  for s in "${SUPPORTED_DESTINATIONS[@]}"; do [[ "$s" == "$d" ]] && return 0; done
  return 1
}

# destinations feeds release.yml's fromJson() matrix, so it must always be valid JSON, even empty.
resolve_destinations() {
  : "${RAW_TARGETS:?set PUBLISH_TARGETS (repo var) or the publish_targets dispatch input}"
  : "${VERSION:?}"
  # Newline-string, not an array -- empty array expansion is unbound-variable on bash 3.2.
  local raw dest matched="" parts dest_json
  IFS=',' read -ra parts <<<"$RAW_TARGETS"
  for raw in "${parts[@]}"; do
    read -r dest <<<"$raw"
    [[ -z "$dest" ]] && continue
    if ! is_supported_destination "$dest"; then
      gha_error "unsupported publish destination '$dest' (supported: ${SUPPORTED_DESTINATIONS[*]})"
      exit 1
    fi
    matched="${matched}${dest}"$'\n'
  done
  # Standalone assignment so set -e catches a failure here, not swallowed as gha_output's argument.
  dest_json="$(printf '%s' "$matched" | sed '/^$/d' | sort -u | jq -R . | jq -sc .)"
  gha_output version "$VERSION"
  gha_output destinations "$dest_json"
}

# Missing/empty here means a build silently produced nothing -- fail loudly, not crash downstream.
require_dist_populated() {
  local group
  for group in tarballs binaries; do
    if [[ -z "$(ls -A "$DIST_DIR/$group" 2>/dev/null)" ]]; then
      gha_error "dist/$group is missing or empty -- nothing to publish"
      exit 1
    fi
  done
}

# Must run before compute_checksums -- a downloaded file otherwise carries no version of its own.
stamp_version() {
  : "${VERSION:?}"
  require_dist_populated
  local f
  for f in "$DIST_DIR"/tarballs/*.tar.gz; do
    mv "$f" "$(dirname "$f")/$(basename "$f" .tar.gz)-${VERSION}.tar.gz"
  done
  for f in "$DIST_DIR"/binaries/*; do
    mv "$f" "${f}-${VERSION}"
  done
}

# One combined file, not one per group -- GitHub release assets are a flat
# namespace, so a tarballs/SHA256SUMS and a binaries/SHA256SUMS would collide.
compute_checksums() {
  require_dist_populated
  (cd "$DIST_DIR" && sha256sum tarballs/* binaries/* | sed -E 's#  (tarballs|binaries)/#  #' >SHA256SUMS.tmp && mv SHA256SUMS.tmp SHA256SUMS)
  cat "$DIST_DIR/SHA256SUMS"
}
