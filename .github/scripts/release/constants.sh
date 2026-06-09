#!/usr/bin/env bash
SERVERS=(disruption-manager dominator filegen-server fleet-manager hypervisor
  image-unpacker imageserver imaginator installer mdbd subd)

# Plain binary, no tarball. Trim this list to publish fewer clients.
CLIENTS=(ami-publisher builder-tool domtool filegen-client fs2objectcache
  fsbench fsreadslow hyper-control imagetool list-cert-expirations logtool
  mdb-relayd objecttool scan show-cert srpc-test subtool unpacker-tool
  vm-control)

DIST_DIR="dist"
SUPPORTED_DESTINATIONS=(github jfrog)
