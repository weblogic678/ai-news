"""Actual delivery-file overview, explicitly not screenshots of running upstream apps."""
from pathlib import Path
import html,json
ROOT=Path(__file__).resolve().parents[1]
names={'dify-1.17.1':('Dify','工作流与应用原型'),'n8n-2.42.6':('n8n','自动化与 API 串联'),'flowise-3.1.4':('Flowise','可视化 AI 聊天流程'),'anythingllm-1.17.0':('AnythingLLM','自用知识库与聊天')}
style='''*{box-sizing:border-box}body{margin:0;background:#f4f7fc;color:#17253e;font-family:"Noto Sans CJK SC",sans-serif}main{padding:54px;width:1080px;min-height:1080px}small{color:#506580;font-size:20px}h1{font-size:76px;letter-spacing:-2px;margin:28px 0 8px}h2{font-size:34px;margin:0 0 24px}p{font-size:24px;line-height:1.8;margin:12px 0}.tag{display:inline-block;padding:9px 17px;background:#e2ebfc;border-radius:30px;margin:16px 12px 16px 0;font-size:21px;color:#245aca}.cards{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:24px 0}.card{background:white;border:1px solid #dce4ef;border-radius:18px;padding:26px;min-height:165px}.card h3{font-size:27px;margin:0 0 12px}.card p{font-size:21px;color:#53627b}.notice{background:#fff0cf;border-left:6px solid #d59b24;padding:22px 26px;margin-top:24px;border-radius:8px}.notice strong{font-size:26px}.notice p{font-size:21px}.foot{margin-top:26px;font-size:19px;color:#65748c}table{border-collapse:collapse;background:white;width:100%;font-size:21px;margin:24px 0}td,th{border-bottom:1px solid #dde5ef;padding:20px;text-align:left}td:last-child{white-space:nowrap;color:#546880}code{font-family:monospace;font-size:20px}a{color:#245aca;text-decoration:none;word-break:break-all}'''
for project,(name,purpose) in names.items():
 p=ROOT/project;meta=json.loads((p/'Windows11/manifest.json').read_text(encoding='utf-8'));version=meta['version']
 hasflow=name in ('Dify','n8n')
 cards=[('双系统入口','Windows11 x64 / Linux x86_64'),('安装与维护','启动、状态、停止、日志、冷备份'),('DeepSeek 教程','自备 Key；API 费用自行承担'),('基础工作流' if hasflow else '场景操作说明','验收流程 + AI 摘要导入文件' if hasflow else '最小配置步骤与验收清单')]
 body=''.join(f'<section class="card"><h3>{html.escape(a)}</h3><p>{html.escape(b)}</p></section>' for a,b in cards)
 page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>{name} 交付包内容</title><style>{style}</style><main><small>自编安装辅助包 · 实际交付内容展示</small><h1>{name} <span style="font-size:38px;color:#587197">{version}</span></h1><p>{purpose} · 脚本、教程与配置材料</p><span class="tag">Windows11</span><span class="tag">Linux x86_64</span><span class="tag">ZIP / TAR.GZ</span><div class="cards">{body}</div><section class="notice"><strong>需要联网与安装前准备</strong><p>不含容器镜像、模型权重、API Key 或充值。<br>Docker / Python 与管理员首次设置需要自行完成。</p></section><section class="notice" style="background:#edf1f7;border-color:#7b8aa1"><strong>部署与工作流执行：待实机验收</strong><p>本图展示实际包内容，不是产品运行截图。<br>来源、许可、校验与验收状态随材料提供。</p></section><p class="foot">上游软件可官方获取；服务费用应对应自编材料与约定的配置劳动。<br>核验日期 2026-10-11 · 保留上游品牌与版权</p></main></html>'''
 (p/'listing/preview.html').write_text(page,encoding='utf-8')
 rows=[]
 for system in ('Windows11','linux-x86'):
  d=p/system
  for f in sorted(d.iterdir()):
   if f.is_file() and (f.suffix in ('.zip','.gz') and f.name!='upstream-docker.zip' or f.name in ('操作步骤.md','SHA256SUMS.txt')):
    rows.append(f'<tr><td><a href="../{system}/{html.escape(f.name)}">{system}/<br>{html.escape(f.name)}</a></td><td>{f.stat().st_size/1024:.1f} KB</td></tr>')
 files=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>{name} 文件清单</title><style>{style}h1{{font-size:52px}}td{{padding:16px}}td a{{font-size:20px}}</style><main><small>实际文件清单 · 不是产品运行截图</small><h1>{name} {version} 交付文件</h1><p>两个平台分别打包，解压后阅读操作步骤。</p><table><thead><tr><th>文件</th><th>大小</th></tr></thead><tbody>{''.join(rows)}</tbody></table><section class="notice"><strong>验收状态随包保留</strong><p>已检查配置和包完整性；真实部署、模型调用与恢复待测试。<br>购买前应确认系统、联网条件、服务范围与平台类目。</p></section></main></html>'''
 (p/'listing/files.html').write_text(files,encoding='utf-8')
 print(project)
