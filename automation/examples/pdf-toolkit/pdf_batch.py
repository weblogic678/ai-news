#!/usr/bin/env python3
"""Original wrapper around a separately installed, trusted pdfcpu CLI.

No shell interpolation, no deletion, no input overwrite. Python 3.10+.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


class ToolError(RuntimeError):
    pass


def run(binary, args, timeout=120):
    try:
        result = subprocess.run([binary, *map(str, args)], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ToolError("运行超时，请缩小文件规模；检查输出目录中的部分结果") from None
    except OSError:
        raise ToolError("无法启动pdfcpu，请确认程序路径和系统架构") from None
    if result.returncode != 0:
        raise ToolError("pdfcpu运行失败：" + (result.stderr or result.stdout)[-2000:])
    return result.stdout


def inputs(folder):
    folder = Path(folder).resolve()
    if not folder.is_dir():
        raise ToolError("输入目录不存在")
    files = sorted((x.resolve() for x in folder.iterdir() if x.is_file() and x.suffix.lower() == ".pdf"), key=lambda x: x.name.casefold())
    if not files:
        raise ToolError("目录中没有PDF文件（只处理当前目录，不递归）")
    # Reject ambiguous names on case-insensitive target filesystems.
    if len({x.stem.casefold() for x in files}) != len(files):
        raise ToolError("文件名大小写冲突，请先改名")
    for file in files:
        if file.stat().st_size > 200_000_000:
            raise ToolError("单文件超过200MB，首期不支持")
        content = file.read_bytes()
        if not content.startswith(b"%PDF-"):
            raise ToolError("文件不是可识别的PDF：" + file.name)
        if re.search(rb"/(Encrypt|ByteRange)\b", content):
            raise ToolError("检测到加密或签名标记，拒绝处理：" + file.name)
    return files


def process(action, folder, output, binary="pdfcpu"):
    resolved = shutil.which(binary)
    if not resolved:
        raise ToolError("未找到pdfcpu；从官方发行页安装，或用 --pdfcpu 指定路径")
    version = run(resolved, ["version"], timeout=15).strip()
    files = inputs(folder)
    output = Path(output).resolve()
    if output.exists():
        raise ToolError("输出位置已存在；请使用新的文件名或新目录，程序不会覆盖")
    if output in files or output == Path(folder).resolve():
        raise ToolError("输入和输出不能相同")
    for file in files:
        run(resolved, ["validate", file])
    results = []
    if action == "merge":
        if output.suffix.lower() != ".pdf":
            raise ToolError("合并输出文件须以.pdf结尾")
        if len(files) < 2:
            raise ToolError("合并至少需要两个PDF文件")
        output.parent.mkdir(parents=True, exist_ok=True)
        run(resolved, ["merge", output, *files])
        run(resolved, ["validate", output])
        results.append({"output": str(output), "bytes": output.stat().st_size})
        log = output.with_suffix(output.suffix + ".report.json")
        if log.exists():
            # Do not replace a pre-existing sidecar even when the PDF is new.
            log = None
    else:
        if action not in ("split", "optimize"):
            raise ToolError("未知操作")
        output.mkdir(parents=True)
        for file in files:
            if action == "split":
                dest = output / file.stem
                dest.mkdir()
                run(resolved, ["split", file, dest])
                pieces = sorted(dest.glob("*.pdf"))
                if not pieces:
                    raise ToolError("拆分没有生成PDF：" + file.name)
                for piece in pieces:
                    run(resolved, ["validate", piece])
                results.append({"input": file.name, "pages": len(pieces), "directory": str(dest)})
            else:
                dest = output / file.name
                run(resolved, ["optimize", file, dest])
                run(resolved, ["validate", dest])
                results.append({"input": file.name, "output": str(dest), "before_bytes": file.stat().st_size, "after_bytes": dest.stat().st_size})
        log = output / "report.json"
    report = {"created_at": datetime.now(timezone.utc).isoformat(), "action": action,
              "pdfcpu_version": version, "input_order": [x.name for x in files],
              "results": results,
              "warning": "优化不保证体积缩小。加密/签名仅做保守标记检测，不构成完整安全鉴定。失败时可能保留部分输出，原文件不变。"}
    if log:
        # Exclusive creation avoids accidentally overwriting unrelated logs.
        with log.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
    return report


def main():
    parser = argparse.ArgumentParser(description="PDF批量处理：合并、按页拆分、优化；不覆盖原文件")
    parser.add_argument("action", choices=["merge", "split", "optimize"])
    parser.add_argument("input", help="含PDF的目录，按文件名排序，不递归")
    parser.add_argument("output", help="新的输出文件或目录")
    parser.add_argument("--pdfcpu", default="pdfcpu", help="已安装可信pdfcpu的路径")
    args = parser.parse_args()
    try:
        print(json.dumps(process(args.action, args.input, args.output, args.pdfcpu), ensure_ascii=False, indent=2))
    except ToolError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
