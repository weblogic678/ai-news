#!/usr/bin/env python3
"""One command produces a fresh, timestamped draft batch. No marketplace writes."""
import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="生成一批独立的选品与上架草稿")
    parser.add_argument("--live", action="store_true", help="更新GitHub来源，默认使用离线快照")
    parser.add_argument("--ai", choices=["dify", "compatible"], help="显式开启AI，会向配置的模型服务发送公开项目资料")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    work = ROOT / "runs" / stamp
    prefix = [sys.executable, str(ROOT / "run.py"), "--workspace", str(work)]
    commands = [["init"], *([["sync", "--all"]] if args.live else []), ["audit"],
                ["generate", "--all", *(["--ai", args.ai] if args.ai else [])], ["report"]]
    for command in commands:
        result = subprocess.run(prefix + command, cwd=ROOT)
        if result.returncode:
            print("批处理停止，保留已有结果供排查：", work, file=sys.stderr)
            return result.returncode
    sys.path.insert(0, str(ROOT / "src"))
    from g2x.catalog import CATALOG
    for item in CATALOG:
        result = subprocess.run(prefix + ["export", "--repo", item["repo"]], cwd=ROOT)
        if result.returncode:
            return result.returncode
    print("批次完成（所有商品仍是草稿）：", work)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
