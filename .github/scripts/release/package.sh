#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/constants.sh"

is_server() {
  local s
  for s in "${SERVERS[@]}"; do [[ "$s" == "$1" ]] && return 0; done
  return 1
}

# Catches a server added to one of SERVERS / Makefile .tarball targets but not the other.
verify_servers_list() {
  local makefile_servers declared missing extra
  makefile_servers="$(grep -oE '^[A-Za-z0-9_-]+\.tarball:' Makefile | sed 's/\.tarball:$//' | sort -u)"
  declared="$(printf '%s\n' "${SERVERS[@]}" | sort -u)"
  missing="$(comm -23 <(printf '%s\n' "$makefile_servers") <(printf '%s\n' "$declared"))"
  extra="$(comm -13 <(printf '%s\n' "$makefile_servers") <(printf '%s\n' "$declared"))"
  if [[ -n "$missing" || -n "$extra" ]]; then
    gha_error "SERVERS in constants.sh is out of sync with Makefile .tarball targets (in Makefile but not SERVERS: ${missing:-none}; in SERVERS but no Makefile target: ${extra:-none})"
    exit 1
  fi
}

# Platform-suffixed so two build legs can merge into one dist/ without collisions.
# strict hard-fails on a missing binary instead of warning (Linux only).
collect_client_binaries() {
  local src="$1" suffix="$2" strict="${3:-}" name d
  mkdir -p "$DIST_DIR/binaries"
  for d in cmd/*/; do
    name="${d%/}"
    name="${name##*/}"
    is_server "$name" && continue
    if [[ -f "$src/$name" ]]; then
      cp -p "$src/$name" "$DIST_DIR/binaries/${name}-${suffix}"
    elif [[ -n "$strict" ]]; then
      gha_error "expected client binary '$name' not found in $src"
      exit 1
    else
      echo "::warning::expected client binary '$name' not found in $src, skipping"
    fi
  done
}

build_linux() {
  : "${PLATFORM:?}"
  verify_servers_list
  local out="/tmp/${LOGNAME:-runner}" gobin
  GOPATH="$(go env GOPATH)"
  export GOPATH
  gobin="$GOPATH/bin"
  mkdir -p "$out" "$DIST_DIR/tarballs" "$DIST_DIR/binaries" ssl
  make all
  # shellcheck disable=SC2046 # word splitting is the point: one make target per server
  make $(printf '%s.tarball ' "${SERVERS[@]}")
  cp "$out"/*.tar.gz "$DIST_DIR/tarballs/"
  collect_client_binaries "$gobin" "$PLATFORM" strict
  strip "$DIST_DIR"/binaries/* 2>/dev/null || true
  cp lib/version/BUILD_INFO "$DIST_DIR/BUILD_INFO"
  find "$DIST_DIR" -type f | sort
}

# Servers won't compile on darwin, so only non-server cmd/ packages are built here.
build_darwin() {
  : "${PLATFORM:?}"
  make generate # //go:embed needs BUILD_INFO before go build touches that package
  local out="/tmp/${LOGNAME:-runner}-darwin" targets=() d name
  mkdir -p "$out"
  for d in cmd/*/; do
    name="${d%/}"
    name="${name##*/}"
    is_server "$name" && continue
    targets+=("./$d")
  done
  # Trailing slash on -o: go build with multiple packages discards binaries without it.
  CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build -buildvcs=true -o "$out/" "${targets[@]}"
  collect_client_binaries "$out" "$PLATFORM"
  strip "$DIST_DIR"/binaries/* 2>/dev/null || true
  cp lib/version/BUILD_INFO "$DIST_DIR/BUILD_INFO"
  find "$DIST_DIR" -type f | sort
}
