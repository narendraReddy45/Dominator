#!/usr/bin/env bash
set -euxo pipefail # -x: full command trace in the log
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$dir/constants.sh"
source "$dir/package.sh"
source "$dir/stage.sh"
source "$dir/publish.sh"

cmd="${1:-}"
case "$cmd" in
  stamp-version | publish-github | publish-jfrog) : "${VERSION:?}" ;;
esac
case "$cmd" in
  publish-github) : "${GH_TOKEN:?}" ;;
  publish-jfrog) : "${JFROG_REPO:?}" ;;
esac

case "$cmd" in
  build-linux) build_linux ;;
  build-darwin) build_darwin ;;
  stamp-version) stamp_version ;;
  checksums) compute_checksums ;;
  publish-github) publish_github ;;
  publish-jfrog) publish_jfrog ;;
  -h | --help | *)
    echo "usage: $0 <build-linux|build-darwin|stamp-version|checksums|publish-github|publish-jfrog>" >&2
    exit 1
    ;;
esac
