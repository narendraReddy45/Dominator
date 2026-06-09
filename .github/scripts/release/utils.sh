#!/usr/bin/env bash

gha_output() {
  local key="$1" value="$2"
  if [[ -z "${GITHUB_OUTPUT:-}" ]]; then
    echo "  [output] $key=$value"
    return
  fi
  if [[ "$value" == *$'\n'* ]]; then
    {
      echo "$key<<__DELIM__"
      echo "$value"
      echo "__DELIM__"
    } >>"$GITHUB_OUTPUT"
  else
    echo "$key=$value" >>"$GITHUB_OUTPUT"
  fi
}

gha_error() {
  echo "::error::$1"
}
