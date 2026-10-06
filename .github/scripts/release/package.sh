#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/constants.sh"

# strict hard-fails on a missing binary instead of warning (Linux only).
collect_client_binaries() {
  local src="$1" suffix="$2" strict="${3:-}" name
  mkdir -p "$DIST_DIR/binaries"
  for name in "${CLIENTS[@]}"; do
    if [[ -f "$src/$name" ]]; then
      cp -p "$src/$name" "$DIST_DIR/binaries/${name}-${suffix}"
    elif [[ -n "$strict" ]]; then
      echo "::error::expected client binary '$name' not found in $src"
      exit 1
    else
      echo "::warning::expected client binary '$name' not found in $src, skipping"
    fi
  done
}

package_dist() {
  cp lib/version/BUILD_INFO "$DIST_DIR/BUILD_INFO"
  find "$DIST_DIR" -type f | sort
}

build_linux() {
  export GOPATH="$(go env GOPATH)" # c/Makefile reads it as a Make variable
  local out="/tmp/${LOGNAME:-runner}"
  mkdir -p "$out" "$DIST_DIR/tarballs" ssl
  make all
  # shellcheck disable=SC2046 # word splitting is the point: one make target per server
  make $(printf '%s.tarball ' "${SERVERS[@]}")
  cp "$out"/*.tar.gz "$DIST_DIR/tarballs/"
  collect_client_binaries "$GOPATH/bin" linux-amd64 strict
  package_dist
}

# Servers don't compile on darwin, so only CLIENTS are built.
build_darwin() {
  make generate # //go:embed needs BUILD_INFO before go build
  local out="/tmp/${LOGNAME:-runner}-darwin" targets=() name
  mkdir -p "$out"
  for name in "${CLIENTS[@]}"; do
    targets+=("./cmd/$name")
  done
  # Trailing slash on -o: multi-package go build discards binaries without it.
  CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build -buildvcs=true -o "$out/" "${targets[@]}"
  collect_client_binaries "$out" darwin-arm64
  package_dist
}
