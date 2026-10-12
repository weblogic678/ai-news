# 闲鱼单图封面制作记录

使用内置 imagegen，共生成 7 张，最终文件清单见 COVER-SPEC.json。没有使用 CLI 或 API Key。

每款图片仅保留四行：软件名、v版本号、一键安装、windows 11 / linux x86_64。软件与版本对应 pdfcpu 0.16.1、CyberChef 11.5.0、Excalidraw 0.18.1、AnythingLLM 1.17.0、Dify 1.17.1、Flowise 3.1.4、n8n 2.42.6。

## 生成提示词模板

Create one square 1:1 high-quality flat typographic cover for a Chinese Xianyu software listing. Clean minimal graphic, warm pale yellow background, dark charcoal text, very generous whitespace, professionally aligned centered layout. No logos, icons, illustration, decorations, additional copy, badges, frame, watermark or screenshots. EXACTLY FOUR TEXT LINES, each appearing once: first line "{software}" in large bold clean Latin type; second line "v{version}" in medium Latin type; third line "一键安装" in extremely prominent huge heavy Chinese type, the largest element on the cover; fourth line "windows 11 / linux x86_64" in much smaller lowercase Latin type near bottom. All English OS characters must be lowercase. Preserve spelling, capitalization of software name, numeric version and all four Chinese characters perfectly. Keep all text fully inside ample safe margins. This is a newly generated simple poster, not an app screenshot.

图片简化不改变交付能力、依赖或验收范围。PDF 是脚本包，CyberChef 和 Excalidraw 是配方/模板材料包；具体范围仍见发布描述.md，不将封面制作视作完成部署验收。旧图与真实截图保留在 temp/listing-history/20261012-simple-covers/。
