# 本机维护资料

根目录的 `../发布描述.md` 汇总闲鱼发布文案，`../images/项目名/cover.png` 存放每款唯一的发布封面；旧图和真实截图保留在 `listing-history/20261012-simple-covers/`。交付项目按 Windows11 与 linux-x86 分目录，目录中包含入口、教程及 ZIP；Linux 另含 TAR.GZ。以下维护资料归入 temp，不属于买家交付包。

- `docs/LOCAL-VALIDATION.md`：真实验收结果与待完成项。
- `tools/repackage-install-kits.py`：重建四款容器工具的交付包。
- `tests/`：安装、数据保护和导入回归；在根目录运行 `python -m unittest discover -s temp/tests -v`。
- `automation/`、`projects/`、`product-metadata/`：制作来源、旧版商品准备资料、许可审查与历史素材。
- `private/`：仅本机账户、日志、运行数据、备份；由 .gitignore 排除，不得上传或打包。

Windows Docker 的 n8n 实测已通过，其他三款镜像下载待完成。DeepSeek 真实调用按用户决定跳过；Linux 回归通过不代表独立服务器验收。
