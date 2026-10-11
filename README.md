# 开源工具商品准备系统

这批工作包含3项有实际产出的首批项目、2项储备候选，以及可运行的自动化准备程序。闲鱼上架由卖家手动完成。没有真实销量或收益承诺。

|项目|产出|技术状态|实验价格|
|---|---|---|---|
|[PDF批处理](projects/01-pdf-batch/)|原创脚本、中文教程、样例与实际PDF成果、3张主图、成果预览|Linux基本操作已测，Windows待验证|29元|
|[CyberChef配方](projects/02-cyberchef-recipes/)|3份配方、中文教程、3张主图、3张实际操作截图|本地版配方导入与输出已测，阻断外网|19元|
|[Excalidraw模板](projects/03-excalidraw-templates/)|3份原创模板、中文教程、3张主图、3张实际导入截图|桌面网页导入和删除撤销已测|19元|
|[LocalSend候选](projects/04-localsend-candidate/)|来源与许可初筛、待验证草稿|暂不上架|待定|
|[Squoosh候选](projects/05-squoosh-candidate/)|来源与许可初筛、待验证草稿|暂不上架|待定|

## 如何使用上架材料

每个首批项目内：

- `listing-title.txt`：可复制标题。
- `listing-description.txt`：如实说明免费来源、收费交付、测试环境与售后范围。
- `images/`：3张1080像素PNG商品说明图。
- `screenshots/`：真实操作截图或明确标识的实际产出预览。
- `buyer/`、`delivery-prepared.zip`：可交付成果。
- `license/`、`seller-notes.md`：许可与平台核对资料。

原软件和本公开仓库资料均可免费获取。收费针对原创整理、按约定交付和一次文字使用答疑；不销售官方授权、付费账号或独家资格。先核对闲鱼当前类目与卖家资格，无法发布的类目不发布。不能以“教程”命名规避实际商品限制。

## 自动化程序

[完整说明](automation/README.md)。Python 3.10+，核心无第三方依赖；PNG可选依赖Pillow。

```powershell
cd automation
py daily.py
```

一次生成独立的候选审核、商品草稿、主图和5份草稿ZIP。`--live`更新GitHub；`--ai dify`或`--ai compatible`启用配置的模型服务。默认不调用AI、不执行下载项目代码、不联系买家、不操作闲鱼。

主许可自动初筛不等于完整商业授权。源证据和商品文件变化会让旧审核失效，发布版需要卖家逐项记录证据。

## 验证与规则

- [测试报告](docs/QA.md)：19项回归、PDF实际处理、3配方、3模板、工作台尺寸检查。
- [上架规则核对](docs/MARKETPLACE-REVIEW.md)：公开协议核对日期2026-10-11；账号具体类目权限仍待卖家确认。
- 每份许可证保留上游声明；没有根许可证代表整个仓库重新授权。原创内容与上游证据分别记录，不把上游软件冒充原创。




## AI 一键安装辅助包

- [Dify 工作流安装配置 1.17.1](dify-1.17.1/README.md)：双平台脚本、压缩包和 DeepSeek 教程；实际部署待验收。
- [n8n 自动化安装配置 2.42.6](n8n-2.42.6/README.md)：双平台脚本、压缩包和 DeepSeek 教程；实际部署待验收。
- [Flowise AI 流程安装配置 3.1.4](flowise-3.1.4/README.md)：双平台脚本、压缩包和 DeepSeek 教程；实际部署待验收。
- [AnythingLLM 知识库安装配置 1.17.0](anythingllm-1.17.0/README.md)：双平台脚本、压缩包和 DeepSeek 教程；实际部署待验收。

详见 [选品说明](docs/AI-选品说明.md) 和 [验收状态](docs/INSTALL-KITS-STATUS.json)。
