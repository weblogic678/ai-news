from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
for name in ('dify-1.17.1','n8n-2.42.6','flowise-3.1.4','anythingllm-1.17.0'):
    for system in ('Windows11','linux-x86'):
        p=ROOT/name/system/'操作步骤.md'
        s=p.read_text(encoding='utf-8')
        old='本包是联网安装辅助包，无容器镜像、无模型权重、无 API Key。制作环境未提供 Docker daemon、Windows 主机或客户服务地址，尚无真实部署截图；不得把静态检查当成实机兼容性保证。'
        state=('本机 Windows 11 Docker 已验证启动、工作流导入与基础执行、重复导入、重启数据保留、冷备份与独立空卷恢复。真实模型调用按用户要求跳过；独立 Linux 服务器未验证。' if name.startswith('n8n') else '已完成配置、脚本保护和压缩包校验；本机固定镜像仍在下载，实际部署、运行及恢复尚未完成，不作为已通过承诺。')
        s=s.replace(old,'本包是联网安装辅助包，无容器镜像、无模型权重、无 API Key。'+state)
        s=s.replace('尚未做恢复实机验证。','n8n 2.42.6 已在本机 Docker 独立空卷验证恢复；其他产品与独立 Linux 服务器恢复未验证。')
        s=s.replace('本交付已制作两个导入文件，未在真实 n8n 实例运行。先完成本机验收再承诺安装服务。','本交付两个文件已在 n8n 2.42.6 实例中导入；无模型的基础工作流已实际执行。DeepSeek 工作流需自备凭据后验证，不承诺模型效果。')
        s += '\n## 本项目本机目录约定\n\n在 `D:\\demo_xianyu` 仓库中，运行配置通过仅本机存在的 `temp/private/runtime-paths.json` 映射到 `temp/private/runtime/`。冷备份与导出的镜像亦留在 `temp/private/` 下。此映射和私密数据均不上传。买家 ZIP 解压后使用自己的同目录 `runtime/`，不需要仓库映射。请勿上传 runtime、.env 或备份。\n'
        p.write_text(s,encoding='utf-8')
p=ROOT/'temp/AGENTS.md'
s=p.read_text(encoding='utf-8').replace('临时验收资料放 `.local/`；产品数据放各包 `runtime/`。','私密验收资料、运行配置和备份放 `temp/private/`；通过本机 runtime-paths.json 选择路径，买家包默认使用其自己的 runtime/。')
s += '\n- 根目录只保留交付项目、images/、发布描述.md 及 Git 必需文件；维护工具、报告、测试和其他资料放 temp/，其中 temp/private/ 永不上传。\n'
p.write_text(s,encoding='utf-8')
p=ROOT/'temp/README.md'
s=p.read_text(encoding='utf-8').replace('私密验收资料放 `.local/`，运行数据放各包 `runtime/`','私密验收资料和运行数据放 `temp/private/`')
s='''# 本机维护资料

根目录的 `../发布描述.md` 汇总闲鱼发布文案，`../images/` 存放发布图片。交付项目按 Windows11 与 linux-x86 分目录，目录中包含入口、教程及 ZIP；Linux 另含 TAR.GZ。以下维护资料归入 temp，不属于买家交付包。

- `docs/LOCAL-VALIDATION.md`：真实验收结果与待完成项。
- `tools/repackage-install-kits.py`：重建四款容器工具的交付包。
- `tests/`：安装、数据保护和导入回归；在根目录运行 `python -m unittest discover -s temp/tests -v`。
- `automation/`、`projects/`、`product-metadata/`：制作来源、旧版商品准备资料、许可审查与历史素材。
- `private/`：仅本机账户、日志、运行数据、备份；由 .gitignore 排除，不得上传或打包。

Windows Docker 的 n8n 实测已通过，其他三款镜像下载待完成。DeepSeek 真实调用按用户决定跳过；Linux 回归通过不代表独立服务器验收。
'''
p.write_text(s,encoding='utf-8')
p=ROOT/'temp/docs/INSTALL-KITS-STATUS.json'
s=json.loads(p.read_text(encoding='utf-8'))
s['stage']='n8n-runtime-passed-other-images-downloading'
for item in s['projects']:
    if item['tool']=='n8n':
        item.update(runtime_tested=True,workflow_import_tested=True,smoke_execution_tested=True,repeat_import_tested=True,restart_preservation_tested=True,backup_restore_tested=True,model_call_tested=False)
        item['listing_allowed']=False  # platform review is distinct from runtime testing
s['blockers']=['Dify, Flowise, AnythingLLM pinned images still downloading; runtime acceptance pending','Real DeepSeek calls explicitly skipped by user','Independent Linux server runtime validation not performed']
s['resume_policy']='Run locally from D:\\demo_xianyu; preserve private data under temp/private and report untested items truthfully.'
s['workflow_import_helpers']='n8n real imports, repeat import and smoke execution passed; Dify pending image downloads'
s['core_tests_passed']=22
s['local_validation'].update(windows_kit_tests_passed=22,wsl_debian13_tests_passed=43,workbench_screenshot='temp/docs/screenshots/windows-local-workbench.png',product_runtime_screenshots_captured=2,report='temp/docs/LOCAL-VALIDATION.md')
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Updated delivery instructions, maintenance index and sanitized status.')
