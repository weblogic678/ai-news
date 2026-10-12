"""Render text-based marketplace cards. Product UI screenshots stay separate."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[2]
FONT=Path('C:/Windows/Fonts/msyh.ttc')
if not FONT.exists():
    FONT=Path('/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc')
def text(d,xy,value,size,color='#17253e'):
    d.text(xy,value,font=ImageFont.truetype(str(FONT),size),fill=color,spacing=18)
for name,tool,version in [('dify-1.17.1','Dify','1.17.1'),('n8n-2.42.6','n8n','2.42.6'),('flowise-3.1.4','Flowise','3.1.4'),('anythingllm-1.17.0','AnythingLLM','1.17.0')]:
    folder=ROOT/'images'/name;folder.mkdir(parents=True,exist_ok=True)
    passed=tool=='n8n'
    for index in (1,2):
        im=Image.new('RGB',(1080,1080),'#f4f7fc');d=ImageDraw.Draw(im)
        text(d,(64,52),'安装辅助材料 / 配置答疑',28,'#526580')
        text(d,(64,115),tool,90 if len(tool)<8 else 76)
        text(d,(66,230),f'固定版本 {version} · 中文操作步骤',33)
        d.rounded_rectangle((60,305,1020,665),radius=24,fill='white',outline='#dce4ef',width=2)
        if index==1:
            text(d,(92,345),'Windows 11 x64 / Linux x86_64',34)
            text(d,(92,418),'一键入口 + ZIP / TAR.GZ',36)
            text(d,(92,497),'启动、状态、日志、停止、冷备份',30)
            text(d,(92,568),'自备 Docker / Python，首次需联网',29,'#526580')
        else:
            text(d,(92,345),'交付文件按操作系统分别整理',35)
            text(d,(92,423),'start.cmd / start.sh + installer.py',29)
            text(d,(92,495),'操作步骤.md + SHA256 校验',31)
            text(d,(92,568),'附来源许可；不含镜像、Key、充值',29,'#526580')
        d.rounded_rectangle((60,705,1020,930),radius=18,fill='#e6f4ed' if passed else '#fff0cf')
        text(d,(92,735),'Windows Docker 已实测' if passed else '当前为待验收草稿',38)
        text(d,(92,801),'工作流执行、重启、冷备份恢复已通过' if passed else '固定镜像仍在下载，未承诺部署通过',28)
        text(d,(92,853),'Linux 服务器与真实模型调用未验证',27,'#526580')
        text(d,(64,967),'上游软件可免费获取；费用对应约定的整理与服务',25,'#526580')
        text(d,(64,1013),'内容展示图 · 产品真实截图另列 · 2026-10-12',23,'#526580')
        im.save(folder/('01-content-overview.png' if index==1 else '02-delivery-files.png'))
print('Rendered 8 marketplace cards with explicit acceptance status.')
