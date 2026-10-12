"""Install imagegen covers, archive replaced images, and fix public references."""
from pathlib import Path
import json,shutil,re
ROOT=Path(__file__).resolve().parents[2]
jobs=json.loads((ROOT/'temp/private/cover-files.json').read_text(encoding='utf-8'))
history=ROOT/'temp/listing-history/20261012-simple-covers'
if history.exists():raise RuntimeError('Image history already exists; refuse overwrite')
for job in jobs:
    folder=ROOT/'images'/job['folder']
    assert folder.resolve().is_relative_to(ROOT/'images')
    archive=history/job['folder'];archive.mkdir(parents=True)
    for p in folder.iterdir():
        assert p.is_file(),p
        shutil.move(str(p),str(archive/p.name))
    shutil.copy2(job['source'],folder/'cover.png')
old=ROOT/'temp/tools/make-listing-images.py'
if old.exists():shutil.move(str(old),str(history/'old-make-listing-images.py'))
p=ROOT/'发布描述.md';s=p.read_text(encoding='utf-8')
s=s.replace('图片统一位于 `images/项目名/`','每款仅一张发布封面，统一位于 `images/项目名/cover.png`')
for job in jobs:
    s=s.replace(f"图片：`images/{job['folder']}/`",f"图片：`images/{job['folder']}/cover.png`")
s=s.replace('真实运行图片见 images/n8n-2.42.6/03-real-workflow.png 和 04-real-output.png。','真实运行截图留在 temp/listing-history/20261012-simple-covers/n8n-2.42.6/，发布时只使用 cover.png。')
p.write_text(s,encoding='utf-8')
p=ROOT/'temp/docs/LOCAL-VALIDATION.md';s=p.read_text(encoding='utf-8')
s=s.replace('../../images/n8n-2.42.6/03-real-workflow.png','../listing-history/20261012-simple-covers/n8n-2.42.6/03-real-workflow.png').replace('../../images/n8n-2.42.6/04-real-output.png','../listing-history/20261012-simple-covers/n8n-2.42.6/04-real-output.png')
s=s.replace('根目录 images/：闲鱼发布主图及真实结果截图；文字主图明确区分已测与待验收。','根目录 images/：每款仅一张闲鱼发布封面；仅显示软件名、版本、一键安装及小写系统名。验收范围与待完成项保留在本报告和发布描述.md；旧图及运行截图移入 temp/listing-history/20261012-simple-covers/。')
p.write_text(s,encoding='utf-8')
p=ROOT/'temp/README.md';s=p.read_text(encoding='utf-8')
s=s.replace('`../images/` 存放发布图片。','`../images/项目名/cover.png` 存放每款唯一的发布封面；旧图和真实截图保留在 `listing-history/20261012-simple-covers/`。')
p.write_text(s,encoding='utf-8')
spec={'generator':'built-in imagegen','format':'square PNG','style':'warm yellow background, dark bold centered typography','exact_lines':['{software}','v{version}','一键安装','windows 11 / linux x86_64'],'assets':[{'software':j['name'],'version':j['version'],'path':'images/'+j['folder']+'/cover.png'} for j in jobs]}
(ROOT/'temp/docs/COVER-SPEC.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Saved 7 covers and archived previous images; updated public references.')
