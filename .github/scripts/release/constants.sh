#!/usr/bin/env bash
# Everything else in cmd/ is a client (plain binary, no tarball).
SERVERS=(disruption-manager dominator filegen-server fleet-manager hypervisor
  image-unpacker imageserver imaginator installer mdbd subd)

DIST_DIR="dist"
SUPPORTED_DESTINATIONS=(github jfrog)
