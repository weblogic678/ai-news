#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
sha256sum -c - <<'CHECKS'
02e4f99ad446f6914fe694dbcaf2bb9b1f4f1ece19aa516c4ae43c76b0f0feea  n8n-2.42.6-linux-x86-offline.part001.gz
e3945dd145fd4151ee7ccb9109e64c927ca56c0c9423e4d2407593d92d00a0ae  n8n-2.42.6-linux-x86-offline.part002.gz
defec5ecec6272198c39653c3667f24142f60d745e1a4bd1fc5786bded3e6198  n8n-2.42.6-linux-x86-offline.part003.gz
a0f3efbe9b2a262e3b1a14f9f1afac76b45c1dcc134dd922adc701bdfb48d09d  n8n-2.42.6-linux-x86-offline.part004.gz
ba890c7b708cc42b39b6d29ff933de08b392a698c737f71d705308efad56af65  n8n-2.42.6-linux-x86-offline.part005.gz
CHECKS
mkdir -p .offline-runtime/package
gzip -dc "n8n-2.42.6-linux-x86-offline.part001.gz" "n8n-2.42.6-linux-x86-offline.part002.gz" "n8n-2.42.6-linux-x86-offline.part003.gz" "n8n-2.42.6-linux-x86-offline.part004.gz" "n8n-2.42.6-linux-x86-offline.part005.gz" > .offline-runtime/package/payload.tar
echo '3acb63f833cf6578ec58c1db548b19ba9916490e3433629302dedf32c4988a9e  .offline-runtime/package/payload.tar' | sha256sum -c -
tar -xf .offline-runtime/package/payload.tar -C .offline-runtime/package
bash .offline-runtime/package/install-offline.sh "$@"
