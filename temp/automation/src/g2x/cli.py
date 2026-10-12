import argparse
import csv
import json
import shutil
import sys
from pathlib import Path
from .audit import audit, review_template
from .catalog import CATALOG
from .generate import generate, export, report, bundle_digest
from .github import GitHub, check_repo


ROOT = Path(__file__).resolve().parents[2]


def slug(repo):
    return check_repo(repo).replace("/", "__")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def snapshots(work):
    return [read(p) for p in sorted((work / "snapshots").glob("*.json"))]


def main(argv=None):
    parser = argparse.ArgumentParser(description="GitHub选品与手动上架包生产工具；不会登录或操作闲鱼")
    parser.add_argument("--workspace", default="work", help="本地工作目录；默认为当前目录下work")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="导入随包真实来源快照，可离线运行")
    sync = commands.add_parser("sync", help="只读GitHub API更新来源，需联网")
    sync.add_argument("--repo")
    sync.add_argument("--all", action="store_true")
    search = commands.add_parser("discover", help="GitHub仓库搜索，不代表商业推荐")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=10)
    check = commands.add_parser("audit", help="许可证证据初筛")
    check.add_argument("--repo")
    gen = commands.add_parser("generate", help="生成原创材料与商品草稿，默认不调用AI")
    gen.add_argument("--repo")
    gen.add_argument("--all", action="store_true")
    gen.add_argument("--ai", choices=["compatible", "dify"])
    exp = commands.add_parser("export", help="导出单项目ZIP；发布版须提供有效审核记录")
    exp.add_argument("--repo", required=True)
    exp.add_argument("--release", action="store_true")
    exp.add_argument("--review", type=Path)
    exp.add_argument("--output", type=Path)
    rev = commands.add_parser("prepare-review", help="在人工编辑完成后重新生成待填写审核表，不批准商品")
    rev.add_argument("--repo", required=True)
    png = commands.add_parser("render-images", help="生成1080像素PNG商品说明图，需要Pillow和中文字体")
    png.add_argument("--repo", required=True)
    png.add_argument("--font", type=Path, required=True)
    commands.add_parser("report", help="生成静态中文候选报告")
    metrics = commands.add_parser("metrics", help="按CSV订单数据核算利润，不抓取平台")
    metrics.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args(argv)
    work = Path(args.workspace).resolve()
    try:
        if args.command == "init":
            (work / "snapshots").mkdir(parents=True, exist_ok=True)
            count = 0
            for p in (ROOT / "data" / "snapshots").glob("*.json"):
                dest = work / "snapshots" / p.name
                if not dest.exists():
                    shutil.copyfile(p, dest)
                    count += 1
            print(f"导入{count}份快照；来源时间见fetched_at，不代表始终为最新版本")
        elif args.command == "discover":
            found = GitHub().discover(args.query, args.limit)
            save(work / "discovery.json", found)
            print(json.dumps(found, ensure_ascii=False, indent=2))
        elif args.command == "sync":
            if bool(args.repo) == bool(args.all):
                raise ValueError("指定 --repo 或 --all，二选一")
            repos = [check_repo(args.repo)] if args.repo else [x["repo"] for x in CATALOG]
            failed = []
            for repo in repos:
                try:
                    s = GitHub().snapshot(repo)
                    save(work / "snapshots" / (slug(repo) + ".json"), s)
                    print(repo, s["version"], s["sha"])
                except Exception as exc:
                    print(repo, "更新失败：", str(exc), file=sys.stderr)
                    failed.append(repo)
            if failed:
                return 1
        elif args.command == "audit":
            items = [read(work / "snapshots" / (slug(args.repo) + ".json"))] if args.repo else snapshots(work)
            if not items:
                raise ValueError("没有快照，请先执行init或sync")
            for s in items:
                result = audit(s)
                save(work / "audits" / (slug(s["repo"]) + ".json"), result)
                print(s["repo"], result["status"], result["detected"], "；".join(result["issues"]))
        elif args.command == "generate":
            if bool(args.repo) == bool(args.all):
                raise ValueError("指定 --repo 或 --all，二选一")
            items = [read(work / "snapshots" / (slug(args.repo) + ".json"))] if args.repo else snapshots(work)
            if not items:
                raise ValueError("没有快照，请先执行init或sync")
            for s in items:
                path = generate(s, work / "bundles" / slug(s["repo"]), ROOT, args.ai)
                print("已生成待审核草稿：", path)
        elif args.command == "export":
            s = read(work / "snapshots" / (slug(args.repo) + ".json"))
            folder = work / "bundles" / slug(args.repo)
            if not folder.is_dir():
                raise ValueError("先执行generate生成商品草稿")
            if args.release and not args.review:
                raise ValueError("发布版需要 --review 指定逐项有证据的审核记录")
            if args.review and not args.release:
                raise ValueError("--review 只与 --release 配合使用")
            review = read(args.review) if args.review else None
            dest = args.output or work / "exports" / (slug(args.repo) + ("-release.zip" if args.release else "-draft.zip"))
            result = export(s, folder, dest, review)
            print(dest, result["status"])
        elif args.command == "prepare-review":
            s = read(work / "snapshots" / (slug(args.repo) + ".json"))
            folder = work / "bundles" / slug(args.repo)
            if not folder.is_dir():
                raise ValueError("先生成商品草稿")
            dest = folder / "review-template.json"
            save(dest, review_template(s, {}, bundle_digest(folder)))
            print("已更新待填写审核表（未批准）：", dest)
        elif args.command == "render-images":
            from .images import render
            folder = work / "bundles" / slug(args.repo)
            if not folder.is_dir():
                raise ValueError("先生成商品草稿")
            print(render(args.repo, folder, args.font))
        elif args.command == "report":
            items = snapshots(work)
            if not items:
                raise ValueError("没有快照，请先执行init或sync")
            dest = work / "report.html"
            report(items, dest)
            print(dest)
        elif args.command == "metrics":
            from decimal import Decimal, InvalidOperation
            total = Decimal("0")
            count = 0
            with args.csv.open(encoding="utf-8-sig", newline="") as file:
                for row in csv.DictReader(file):
                    revenue = Decimal(row["received"])
                    costs = sum((Decimal(row[x]) for x in ("platform_fee", "delivery_cost", "ai_cost", "refund")), Decimal("0"))
                    costs += Decimal(row["support_minutes"]) * Decimal(row["hourly_cost"]) / Decimal("60")
                    profit = revenue - costs
                    total += profit
                    count += 1
                    print(row["order_id"], "贡献利润", str(profit.quantize(Decimal("0.01"))))
            print("订单数", count, "贡献利润合计", str(total.quantize(Decimal("0.01"))))
    except Exception as exc:
        print("错误：" + str(exc), file=sys.stderr)
        return 1
    return 0
