"""Build public delivery layout; never read local credentials or runtime data."""
from pathlib import Path
import shutil, zipfile, tarfile, hashlib

ROOT=Path(__file__).resolve().parents[2]
sections=['# 闲鱼发布描述\n\n图片统一位于 `images/项目名/`；安装入口、教程和交付压缩包位于对应项目的 `Windows11/` 或 `linux-x86/`。下列内容按项目单独复制发布，标注待验收的项目保留草稿。\n\n公开材料可从 GitHub 免费获取，费用对应约定的整理、配置和答疑服务。发布前确认平台当前允许的类目和交付方式，成交前约定价格、服务次数和环境。\n']
for project in sorted((ROOT/'temp/projects').glob('0[123]-*')):
    name=project.name
    title=(project/'listing-title.txt').read_text(encoding='utf-8').strip()
    description=(project/'listing-description.txt').read_text(encoding='utf-8').strip()
    sections.append(f'## {title}\n\n图片：`images/{name}/`\n\n{description}\n')
    for system in ('Windows11','linux-x86'):
        folder=ROOT/name/system
        if folder.exists():
            raise RuntimeError('Existing delivery folder: '+str(folder))
        shutil.copytree(project/'buyer',folder)
        if name.startswith('01-'):
            (folder/'start-demo.py').write_text('''from pathlib import Path
from datetime import datetime
import pdf_batch
base=Path(__file__).resolve().parent
dest=base/'runtime'/datetime.now().strftime('%Y%m%d-%H%M%S-%f')/'merged.pdf'
dest.parent.mkdir(parents=True)
try:
    pdf_batch.process('merge',base/'samples',dest,'pdfcpu')
    print('Created:',dest)
except pdf_batch.ToolError as error:
    print(error)
    raise SystemExit(1)
''',encoding='utf-8')
            if system=='Windows11':
                (folder/'start.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\npy -3 start-demo.py\r\npause\r\n',encoding='ascii')
            else:
                (folder/'start.sh').write_text('#!/bin/sh\nset -eu\ncd "$(dirname "$0")"\nexec python3 start-demo.py\n',encoding='utf-8')
        else:
            # Browser material packs have no native installer. Open the local guide.
            if system=='Windows11':
                (folder/'start.cmd').write_text('@echo off\r\ncd /d "%~dp0"\r\nstart "" "guide.md"\r\n',encoding='ascii')
            else:
                (folder/'start.sh').write_text('#!/bin/sh\nset -eu\ncd "$(dirname "$0")"\ncat guide.md\n',encoding='utf-8')
        (folder/'操作步骤.md').write_text('# 使用入口\n\n'+('先安装 Python 3.10+ 和官方 pdfcpu，并让 pdfcpu 位于 PATH。Windows 双击 start.cmd；Linux 执行 bash start.sh，运行随包样例合并，结果写入新建的 runtime 时间目录。其他操作见 guide.md。Windows 示例入口尚未完成实机验证。' if name.startswith('01-') else '本项目是浏览器配方/模板材料包。Windows 双击 start.cmd 打开本机 guide.md；Linux 执行 bash start.sh 显示教程。按教程在官方工具中导入 JSON 或模板，入口不执行自动导入或安装。')+'\n',encoding='utf-8')
        files=[f for f in folder.rglob('*') if f.is_file()]
        archive=folder/f'{name}-{system}.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for f in files:z.write(f,f.relative_to(folder))
        archives=[archive]
        if system=='linux-x86':
            tgz=folder/f'{name}-{system}.tar.gz'
            with tarfile.open(tgz,'w:gz') as t:
                for f in files:t.add(f,arcname=str(f.relative_to(folder)))
            archives.append(tgz)
        (folder/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n' for f in archives),encoding='utf-8')
for name in ('dify-1.17.1','n8n-2.42.6','flowise-3.1.4','anythingllm-1.17.0'):
    meta=ROOT/'temp/product-metadata'/name/'listing'
    title=(meta/'标题.txt').read_text(encoding='utf-8').strip()
    description=(meta/'描述-待验收.txt').read_text(encoding='utf-8').strip()
    if name.startswith('n8n'):
        description=description.replace('【上架前草稿：实际部署未验收，完成后才能采用对应承诺】','【本机 Windows Docker 验收已完成；Linux 服务器与模型调用未验收】\n已验证固定版本启动、两个工作流导入与重复导入、基础工作流执行、重启数据保留、冷备份与独立空卷恢复。真实运行图片见 images/n8n-2.42.6/03-real-workflow.png 和 04-real-output.png。DeepSeek 流程仅提供配置材料，真实调用按要求跳过。')
    sections.append(f'## {title}\n\n图片：`images/{name}/`\n\n{description}\n')
(ROOT/'发布描述.md').write_text('\n'.join(sections),encoding='utf-8')
print('Created 7 listing descriptions and 6 material delivery directories.')
