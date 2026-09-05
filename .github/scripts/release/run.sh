#!/usr/bin/env bash
set -euxo pipefail # -x: full command trace in the log
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$dir/utils.sh"
source "$dir/constants.sh"
source "$dir/package.sh"
source "$dir/destinations.sh"
source "$dir/publish.sh"

case "${1:-}" in
  build-linux) build_linux ;;
  build-darwin) build_darwin ;;
  resolve-destinations) resolve_destinations ;;
  stamp-version) stamp_version ;;
  checksums) compute_checksums ;;
  publish-github) publish_github ;;
  publish-jfrog) publish_jfrog ;;
  -h | --help | *)
    echo "usage: $0 <build-linux|build-darwin|resolve-destinations|stamp-version|checksums|publish-github|publish-jfrog>" >&2
    exit 1
    ;;
esac
