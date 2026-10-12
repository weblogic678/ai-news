#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
sha256sum -c - <<'CHECKS'
f242fb9fc6b8e0b22f7e1bb05213aa82d89d0bcbc45687ec6c4f630b0df0c0e2  flowise-2.2.8-linux-x86-offline.part001.gz
81cbc6ae812771fc3a52735337a3320b8f8d2db5bb1e6731c1cbc0b9de913ad0  flowise-2.2.8-linux-x86-offline.part002.gz
485578fff0564fdfecc4215d62a14324689fc467152c4293ed9127e6bae95716  flowise-2.2.8-linux-x86-offline.part003.gz
9646350f6e27a2f0fd14154a8a3c2202bae6d73759659742a638c6fb58212f09  flowise-2.2.8-linux-x86-offline.part004.gz
b8533d927f79de9109a3e5cf08f02e2bc7ddce04346b2b8875d07634f251ff68  flowise-2.2.8-linux-x86-offline.part005.gz
f598525ca4dcec15c67848ea918b1949f90bc0819145f1181913463636de6554  flowise-2.2.8-linux-x86-offline.part006.gz
c5a59f59108c7ed9547038069fe4d0893f87579266dec083494b042f63764244  flowise-2.2.8-linux-x86-offline.part007.gz
885b5289b56d9eb1ded47ba80794f6de51f5c816c47ab4d25ad7cb52cb184696  flowise-2.2.8-linux-x86-offline.part008.gz
256b88c4eabd5516c983b2f457ea7a3e4ef80310b071ec9b0a3c6a2b9b968aea  flowise-2.2.8-linux-x86-offline.part009.gz
5b50d4480d9875c8d3825af52948dfee1e4c5c6f982265a0ee9d90881825bc03  flowise-2.2.8-linux-x86-offline.part010.gz
d4f924fb1a1da06b4a6b199e5f610e144e48d50348a2acafd448fe95675ac973  flowise-2.2.8-linux-x86-offline.part011.gz
CHECKS
mkdir -p .offline-runtime/package
gzip -dc "flowise-2.2.8-linux-x86-offline.part001.gz" "flowise-2.2.8-linux-x86-offline.part002.gz" "flowise-2.2.8-linux-x86-offline.part003.gz" "flowise-2.2.8-linux-x86-offline.part004.gz" "flowise-2.2.8-linux-x86-offline.part005.gz" "flowise-2.2.8-linux-x86-offline.part006.gz" "flowise-2.2.8-linux-x86-offline.part007.gz" "flowise-2.2.8-linux-x86-offline.part008.gz" "flowise-2.2.8-linux-x86-offline.part009.gz" "flowise-2.2.8-linux-x86-offline.part010.gz" "flowise-2.2.8-linux-x86-offline.part011.gz" > .offline-runtime/package/payload.tar
echo 'cddd211c000800382ec022741ccdde29ee5e740830352f5e31b1759517857a1e  .offline-runtime/package/payload.tar' | sha256sum -c -
tar -xf .offline-runtime/package/payload.tar -C .offline-runtime/package
bash .offline-runtime/package/install-offline.sh "$@"
