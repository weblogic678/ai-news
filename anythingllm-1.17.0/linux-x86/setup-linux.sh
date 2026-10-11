#!/usr/bin/env bash
# Optional prerequisite setup, following official Docker apt repository instructions.
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [[ "${1:-}" == "--install-prerequisites" ]]; then
  [[ $EUID -eq 0 ]] || { echo 'Run this explicit setup with sudo; normal install.sh does not change system packages.'; exit 1; }
  [[ $(uname -m) == x86_64 ]] || { echo 'Only x86_64 is supported.'; exit 1; }
  source /etc/os-release
  case "$ID:$VERSION_ID" in ubuntu:22.04|ubuntu:24.04|debian:12) ;; *) echo 'Only Ubuntu 22.04/24.04 and Debian 12 are supported by this setup.'; exit 1;; esac
  apt-get update
  apt-get install -y ca-certificates curl python3
  install -m 0755 -d /etc/apt/keyrings
  if [[ ! -f /etc/apt/keyrings/docker.asc ]]; then
    curl --fail --show-error --location "https://download.docker.com/linux/$ID/gpg" -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
  fi
  if [[ ! -f /etc/apt/sources.list.d/docker.sources && ! -f /etc/apt/sources.list.d/docker.list ]]; then
    cat > /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/$ID
Suites: $VERSION_CODENAME
Components: stable
Architectures: amd64
Signed-By: /etc/apt/keyrings/docker.asc
EOF
  fi
  apt-get update
  # Do not remove an existing Docker installation or conflicting packages automatically.
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  systemctl start docker
elif [[ $# -gt 0 ]]; then
  echo 'Usage: bash setup-linux.sh [--install-prerequisites]'; exit 1
fi
exec bash install.sh
