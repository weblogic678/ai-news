#!/usr/bin/env bash
set -euo pipefail
BASE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$BASE"
umask 077
RUN="$BASE/.offline-runtime"
if [ -f "$BASE/manifest.json" ]; then
  PROJECT="$(sed -n 's/.*"project": "\([^"]*\)".*/\1/p' "$BASE/manifest.json")"
  [[ "$PROJECT" =~ ^ai-news-[a-z0-9-]+$ ]] || { echo 'Invalid project identifier' >&2; exit 1; }
  if [ "$(id -u)" = 0 ]; then
    RUN="/var/lib/ai-news-offline/$PROJECT/bootstrap"
    export AI_NEWS_RUNTIME="/var/lib/ai-news-offline/$PROJECT/runtime"
  fi
fi
mkdir -p "$RUN"
# Archives are shipped and hashed by the outer verified delivery package.
if [ ! -x "$RUN/python/bin/python3" ]; then
  tar -xzf "$BASE/offline/python-linux.tar.gz" -C "$RUN"
fi
if [ -f "$BASE/installer.py" ]; then
  if [ "${AI_NEWS_FORCE_LOCAL_ENGINE:-0}" = 1 ] || ! command -v docker >/dev/null || ! docker info >/dev/null 2>&1; then
    if [ "$(id -u)" != 0 ]; then
      echo 'Docker 未运行。请使用 sudo bash install-offline.sh（离线安装本地 Engine）。' >&2
      exit 1
    fi
    if [ ! -x "$RUN/docker/dockerd" ]; then
      tar -xzf "$BASE/offline/docker-engine.tgz" -C "$RUN"
    fi
    if [ ! -x "$RUN/network/usr/sbin/xtables-legacy-multi" ]; then
      "$RUN/python/bin/python3" "$BASE/offline/offline-network.py" "$BASE/offline/network" "$RUN/network"
    fi
    mkdir -p "$RUN/network-bin"
    for name in iptables ip6tables iptables-save iptables-restore ip6tables-save ip6tables-restore; do
      ln -sf "$RUN/network/usr/sbin/xtables-legacy-multi" "$RUN/network-bin/$name"
    done
    export LD_LIBRARY_PATH="$RUN/network/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
    export XTABLES_LIBDIR="$RUN/network/usr/lib/x86_64-linux-gnu/xtables"
    STATE="/var/lib/ai-news-offline/$PROJECT"
    EXEC="/run/ai-news-offline/$PROJECT"
    mkdir -p "$RUN/docker-config/cli-plugins" "$STATE" "$EXEC"
    cp "$BASE/offline/docker-compose" "$RUN/docker-config/cli-plugins/docker-compose"
    chmod +x "$RUN/docker-config/cli-plugins/docker-compose"
    export PATH="$RUN/network-bin:$RUN/docker:$PATH" DOCKER_CONFIG="$RUN/docker-config" DOCKER_HOST="unix://$EXEC/docker.sock"
    if ! docker info >/dev/null 2>&1; then
      # No firewall or global Docker configuration changes. Loopback publication uses docker-proxy.
      nohup setsid dockerd --host="$DOCKER_HOST" --data-root="$STATE" \
        --exec-root="$EXEC" --pidfile="$EXEC/docker.pid" \
        --iptables=false --ip6tables=false --ip-masq=false --ip-forward=false --bridge=none \
        >"$RUN/docker.log" 2>&1 < /dev/null &
      for _ in {1..90}; do docker info >/dev/null 2>&1 && break; sleep 1; done
      docker info >/dev/null 2>&1 || { echo "Docker 启动失败：$RUN/docker.log" >&2; exit 1; }
    fi
  fi
  "$RUN/python/bin/python3" installer.py "${1:-install}"
else
  export PATH="$BASE/offline/pdfcpu:$PATH"
  "$RUN/python/bin/python3" "${ENTRYPOINT:-start-demo.py}"
fi
