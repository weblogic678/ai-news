# 本机维护资料

正式交付入口在根目录 `发布版`，发布文案在根目录 `发布描述.md`。

`source-kits` 是三个固定版本的安装器源码；`tools` 是本机离线下载、导出、打包和审计工具；`tests` 是数据保留与失败拒绝检查；`docs` 是当前验收记录。源码目录中的旧操作说明不作为交付入口。

`private` 包含本机凭据、下载缓存、运行与备份等私有资料，已被 Git 忽略。维护时在 D:\demo_xianyu 本机操作，不上传私有目录、运行卷或 `.offline-runtime`。

打包：`python temp/tools/build-release.py`。镜像导出：`python temp/tools/export-offline-images.py 项目版本目录名`。包审计：`python temp/tools/audit-release-content.py`。回归：`python -m unittest discover -s temp/tests`。
