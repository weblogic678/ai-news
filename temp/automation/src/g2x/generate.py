import hashlib
import html
import json
import shutil
import zipfile
from pathlib import Path
from . import ai
from .audit import audit, review_template, validate_review
from .catalog import product
from .github import check_repo


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def json_write(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def bundle_digest(folder):
    digest = hashlib.sha256()
    for path in sorted(folder.rglob("*")):
        if path.is_symlink():
            raise ValueError("上架包不能包含符号链接")
        if path.is_file() and path.name not in ("review.json", "review-template.json"):
            digest.update(path.relative_to(folder).as_posix().encode() + b"\0")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def cover(p, index):
    # Native SVG typography and diagrams, not fabricated app screenshots.
    subtitles = ["原创教程与场景脚本", "交付内容与运行环境", "软件免费 · 收费为整理与服务"]
    rows = [p["offer"], "上游许可证与免费获取地址随附", "先核对环境，再约定服务范围"]
    esc = html.escape
    feature_rows = "".join(f'<text x="80" y="{440+i*68}" font-size="25" fill="#243a52">{esc(x[:30])}</text>' for i, x in enumerate(p["features"][:3]))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1080" viewBox="0 0 1080 1080">
<rect width="1080" height="1080" fill="#f2f5f7"/><rect x="48" y="48" width="984" height="984" rx="32" fill="white"/>
<rect x="80" y="82" width="330" height="50" rx="25" fill="#fff2dc"/><text x="104" y="115" font-family="sans-serif" font-size="23" fill="#8b5605">待审核草稿 · 示意主图</text>
<g font-family="sans-serif"><text x="80" y="238" font-size="55" font-weight="bold" fill="#153653">{esc(p['name'])}</text>
<text x="80" y="320" font-size="32" fill="#356777">{esc(subtitles[index])}</text>
{feature_rows}
<rect x="80" y="700" width="920" height="170" rx="20" fill="#edf4f5"/>
<text x="110" y="753" font-size="25" fill="#153653">基于 {esc(p['repo'])}</text>
<text x="110" y="808" font-size="22" fill="#356777">不代表上游官方或独家授权</text>
<text x="80" y="942" font-size="24" fill="#8b5605">功能、平台兼容性和类目准入须审核后再发布</text></g></svg>'''


def buyer_guide(snapshot, p):
    facts = f"上游项目：{snapshot['repo']}\n固定版本：{snapshot['version']}\n固定提交：{snapshot['sha']}\n免费获取：https://github.com/{snapshot['repo']}\n"
    common = """\n## 收费与交付说明\n\n原项目免费。本包提供自编材料，未附上游安装程序、模型或付费账号；请从官方渠道安装。未完成最终审核，当前仅用于卖家准备。\n\n## 数据与售后\n\n先用样例或文件副本验证，再处理自己的文件。不要把买家文件、密码或访问令牌上传给AI。售后按商品约定的环境、次数和时间提供，不承诺无限支持。\n"""
    if snapshot["repo"] == "pdfcpu/pdfcpu":
        body = """\n## 安装准备\n\n1. 安装Python 3.10或以上版本。Windows可先运行 `py --version`。\n2. 从上述官方仓库发行页下载适合操作系统的pdfcpu。不要使用未知来源的安装程序。\n3. 解压后运行 `pdfcpu version`；不在PATH时，用脚本的 `--pdfcpu` 参数指定完整路径。\n4. 首次使用先处理随包样例，输出到新的目录。\n\n## Windows PowerShell示例\n\n以下命令在本教程目录运行。Windows实机验证尚未完成；交付前须在买家目标环境复测。\n\n```powershell\npy pdf_batch.py merge samples output\\merged.pdf --pdfcpu "C:\\tools\\pdfcpu\\pdfcpu.exe"\npy pdf_batch.py split samples output\\split --pdfcpu "C:\\tools\\pdfcpu\\pdfcpu.exe"\npy pdf_batch.py optimize samples output\\optimized --pdfcpu "C:\\tools\\pdfcpu\\pdfcpu.exe"\n```\n\n## Linux / WSL示例\n\n```bash\npython3 pdf_batch.py merge samples output/merged.pdf --pdfcpu /path/to/pdfcpu\npython3 pdf_batch.py split samples output/split --pdfcpu /path/to/pdfcpu\npython3 pdf_batch.py optimize samples output/optimized --pdfcpu /path/to/pdfcpu\n```\n\n脚本按文件名排序，建议文件用01、02等前缀。只处理当前目录的.pdf文件，不递归。已存在的输出位置会被拒绝，避免覆盖。单文件首期限制200MB。出错时可能留下部分输出，应查看日志后使用新输出路径重试。\n\n## 验收\n\n- 合并：两个一页样例合并后共两页，顺序与文件名一致。\n- 拆分：样例应各得到一个独立页面；实际多页文件逐页核对。\n- 优化：输出通过pdfcpu validate，页面数不变；不保证文件体积减小。\n- 原文件：处理前后校验值相同。\n\n## 不支持\n\nOCR、密码破解、去水印不属于本商品。加密或签名标记会被保守拦截，但这不是完整签名鉴定；不要用此脚本处理合同签名原件。\n"""
    elif snapshot["repo"] == "gchq/CyberChef":
        body = """\n## 准备与使用\n\n从固定版本发行页获取官方CyberChef。浏览器本地运行、导入配方和输出一致性需在目标环境测试；目前三份配方是待导入验证的草稿。\n\n1. 打开官方工具，使用Import Recipe功能导入recipes目录的JSON。\n2. Base64编码示例输入：Hello；预期输出：SGVsbG8=。\n3. Base64解码示例输入：SGVsbG8=；预期输出：Hello。\n4. URL解码示例输入：hello%20world；预期输出：hello world。\n5. 比较输出并记录浏览器、版本、操作结果及截图。\n\n示例仅用于合法的文本处理，不用于破解、入侵或绕过权限。公式预期值不代表已完成应用导入测试。\n"""
    elif snapshot["repo"] == "localsend/localsend":
        body = """\n## 双设备验收清单\n\n1. 两台设备都从官方渠道安装LocalSend；记录操作系统与软件版本。\n2. 检查是否连接同一可互访局域网；访客Wi-Fi、AP隔离或企业隔离网络可能阻止设备发现。\n3. 使用原创测试文本，A发送给B，再由B发送给A。\n4. 记录设备发现时间、传输结果、文件校验值；大文件需单独测试。\n5. 如防火墙阻拦，仅按官方文档允许相应应用和必要端口，不要求关闭整个防火墙。\n6. 测试取消、拒收、重复文件及目标存储权限。\n\n当前没有完成双设备实测。服务范围必须约定设备数量、支持系统、排障时长和无法解决时的处理方式。\n"""
    else:
        body = "\n## 待开发\n\n此项目仅完成候选调研与主许可初筛，原创模板或参数教程尚未制作，不能作为成品售卖。\n"
    return f"# {p['name']}：中文使用材料（草稿）\n\n{facts}" + body + common


def generate(snapshot, folder, project_root, provider=None):
    folder = Path(folder)
    if folder.exists():
        raise ValueError("商品目录已存在，不覆盖人工修改；请使用新的 --workspace 或先备份后移动该目录")
    p = product(snapshot["repo"])
    result = audit(snapshot)
    folder.mkdir(parents=True)
    json_write(folder / "license" / "source-evidence.json", snapshot)
    json_write(folder / "license" / "audit.json", result)
    for file in snapshot.get("license_files", []):
        # Root files only; names must not become arbitrary paths.
        if "/" not in file["path"] and "\\" not in file["path"] and file["path"] not in (".", ".."):
            write(folder / "license" / file["path"], file["text"])
    listing = f"""# {p['title']}\n\n**待审核草稿：不要直接发布。**\n\n适用人群：{p['audience']}。\n\n收费内容：{p['offer']}。原软件可以免费获取：https://github.com/{snapshot['repo']} 。本商品不是软件官方授权或独家产品。\n\n计划内容（未验证部分不作为交付承诺）：\n"""
    listing += "\n".join("- " + x for x in p["features"]) + "\n\n限制与待确认：\n"
    listing += "\n".join("- " + x for x in p["limits"])
    listing += f"\n\n价格测试建议：{p['prices']}元（仅实验起点，不是市场行情或收益预测）。每档单独明确交付，不设置误导性低价。\n\n软件版本：{snapshot['version']}；固定提交：{snapshot['sha']}。\n\n交付：本包只包含原创材料与许可证据，不包含上游程序。不得承诺终身更新、无限售后或保证收益。\n\n发布前核对账号与类目准入、真实截图、运行环境及售后范围。上架由卖家手动完成。\n"
    write(folder / "listing.md", listing)
    write(folder / "buyer" / "guide.md", buyer_guide(snapshot, p))
    write(folder / "buyer" / "FAQ.md", "# 常见问题（待审核）\n\n**软件是不是免费的？** 是，官方项目可免费获取，收费针对本商品声明的原创材料及服务。\n\n**是否保证安装成功？** 仅支持完成测试的环境，先确认系统、架构和服务范围；其他环境需另行评估。\n\n**是否可以退款？** 按适用平台规则及约定处理，不设置‘虚拟商品一律不退’。\n\n**是否含付费账号？** 不含第三方账号、商业授权或模型API额度。\n")
    for index in range(3):
        write(folder / "images" / f"cover-{index+1}.svg", cover(p, index))
    write(folder / "seller-checklist.md", "# 卖家发布前检查\n\n- [ ] 固定版本许可及引用内容已核对\n- [ ] 交付范围内依赖、素材、字体已审核\n- [ ] 买家目标系统已实测，安装及关键功能通过\n- [ ] 截图来自真实测试，无个人信息及密钥\n- [ ] 商品类目与卖家资格符合当前平台要求\n- [ ] 交付、价格、售后与验收标准明确\n- [ ] AI草稿及所有文案已检查，无夸大承诺\n- [ ] 主图草稿标识仅在真实审核完成后移除\n\n当前没有自动批准任何商品。\n")
    write(folder / "test-evidence.md", "# 功能验证记录\n\n本文件留给卖家记录目标环境实测。默认没有测试通过记录。\n\n|环境|版本|测试操作|结果|证据文件|\n|---|---|---|---|---|\n|待填写|待填写|待填写|未测试|待填写|\n")
    if snapshot["repo"] == "pdfcpu/pdfcpu":
        for filename in ("pdf_batch.py", "make_samples.py"):
            shutil.copyfile(project_root / "examples" / "pdf-toolkit" / filename, folder / "buyer" / filename)
        samples = project_root / "examples" / "pdf-toolkit" / "samples"
        if samples.exists():
            shutil.copytree(samples, folder / "buyer" / "samples")
        test = project_root / "docs" / "pdf-functional-test.json"
        if test.exists():
            shutil.copyfile(test, folder / "seller-pdf-functional-test.json")
    elif snapshot["repo"] == "gchq/CyberChef":
        recipes = {"01-to-base64": [{"op": "To Base64", "args": ["A-Za-z0-9+/="]}],
                   "02-from-base64": [{"op": "From Base64", "args": ["A-Za-z0-9+/=", True, False]}],
                   "03-url-decode": [{"op": "URL Decode", "args": []}]}
        for name, recipe in recipes.items():
            json_write(folder / "buyer" / "recipes" / (name + ".json"), recipe)
    elif snapshot["repo"] == "excalidraw/excalidraw":
        templates = project_root / "examples" / "excalidraw-templates"
        if templates.exists():
            shutil.copytree(templates, folder / "buyer" / "templates")
    if provider:
        # Keep AI output separate from trusted boilerplate and core listing.
        output = ai.draft(provider, {"project": p, "version": snapshot["version"], "sha": snapshot["sha"], "license_audit": result,
                                   "readme_excerpt": (snapshot.get("readme") or {}).get("text", "")[:12000],
                                   "test_status": "目标平台与最终交付尚未审核"})
        json_write(folder / "ai-draft.json", output)
        write(folder / "ai-draft.md", "# AI草稿：必须人工核验\n\n" + "\n\n".join(output.values()))
    write(folder / "ai-status.md", f"AI状态：{'已请求生成，结果待人工审核' if provider else '未调用AI；当前材料由确定性模板生成，可另行显式启用AI'}。\n")
    json_write(folder / "review-template.json", review_template(snapshot, p, bundle_digest(folder)))
    return folder


def export(snapshot, folder, destination, review=None):
    folder = Path(folder)
    destination = Path(destination)
    if destination.exists():
        raise ValueError("导出文件已存在，拒绝覆盖")
    digest = bundle_digest(folder)
    if review is not None:
        errors = validate_review(review, snapshot, digest)
        if audit(snapshot)["status"] == "blocked":
            errors.append("主项目许可/维护初筛仍有阻塞，首期禁止发布版导出")
        if errors:
            raise ValueError("发布版导出被阻止：\n" + "\n".join(errors))
    destination.parent.mkdir(parents=True, exist_ok=True)
    status = "seller_approved_manual_upload" if review is not None else "DRAFT_NOT_FOR_SALE"
    manifest = {"repo": snapshot["repo"], "sha": snapshot["sha"], "bundle_digest": digest,
                "status": status, "delivery_mode": "original_materials_only", "marketplace_upload": "manual"}
    with zipfile.ZipFile(destination, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(folder.rglob("*")):
            if file.is_file():
                archive.write(file, file.relative_to(folder).as_posix())
        archive.writestr("EXPORT-MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        if review is not None:
            archive.writestr("SELLER-APPROVAL.json", json.dumps(review, ensure_ascii=False, indent=2))
        else:
            archive.writestr("DRAFT-NOT-FOR-SALE.txt", "当前为卖家准备草稿，未经最终审核，不要直接发布或交付买家。\n")
    return manifest


def report(snapshots, destination):
    esc = html.escape
    rows = []
    for snap in sorted(snapshots, key=lambda s: product(s["repo"])["rank"]):
        p, a = product(snap["repo"]), audit(snap)
        price = " / ".join(str(x) for x in p["prices"]) or "待定"
        source_url = "https://github.com/" + check_repo(snap["repo"])
        rows.append(f"<tr><td>{p['rank']}</td><td><strong>{esc(p['name'])}</strong><br><a href='{esc(source_url)}'>{esc(snap['repo'])}</a></td><td>{esc(snap['version'])}<br>{esc(', '.join(a['detected']))}</td><td>{sum(p['scores'])}/100<br>主观初筛</td><td>{price}元<br>实验价格</td><td>{esc(p['decision'])}<br><span class='warn'>尚未批准销售</span></td></tr>")
    body = "".join(rows)
    page = f"""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>开源工具商品工作台</title><style>
body{{margin:0;background:#f4f6f8;color:#213547;font:16px/1.7 system-ui,sans-serif}}main{{max-width:1200px;margin:40px auto;padding:24px}}h1{{font-size:34px;margin-bottom:4px}}.badge{{display:inline-block;padding:6px 16px;border-radius:18px;background:#fff0d8;color:#7d4a00}}.card{{background:white;border:1px solid #dce4e9;padding:24px;border-radius:18px;margin:24px 0}}.table{{overflow:auto}}table{{width:100%;border-collapse:collapse;min-width:850px}}th,td{{padding:15px;text-align:left;border-bottom:1px solid #e4e9ed;vertical-align:top}}th{{background:#edf4f5}}a{{color:#145d77}}.warn{{color:#8b5605}}code{{background:#edf1f4;padding:3px 6px}}footer{{color:#53677a}}</style><main>
<span class="badge">本地卖家工作台 · 手动上架</span><h1>GitHub → 商品准备流水线</h1><p>固定版本、保存许可证据、生成原创材料。此页面为静态报告，不登录闲鱼、不发布商品。</p>
<section class="card"><h2>首批候选</h2><div class="table"><table><thead><tr><th>顺序</th><th>商品方向</th><th>固定版本 / 主许可</th><th>评分</th><th>试验价</th><th>处理建议</th></tr></thead><tbody>{body}</tbody></table></div></section>
<section class="card"><h2>开始操作</h2><ol><li>先做PDF批处理脚本的目标系统实测。</li><li>查看对应商品包中的listing.md、license目录和seller-checklist.md。</li><li>记录review-template.json中的证据，保存为review.json。</li><li>审核后执行发布版导出；你在闲鱼手动上传文案及真实图片。</li></ol><p>完整命令见源码README。AI为可选功能，默认不发送数据。</p></section>
<footer>候选评分、价格均为经营假设；没有闲鱼销量、转化率或收益证据。主许可初筛不等于完整商业授权。</footer></main></html>"""
    write(Path(destination), page)
