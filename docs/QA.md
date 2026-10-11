# 验证报告

## 结果

核心Python回归21项通过；离线批处理完整生成5份独立草稿ZIP；PNG生成通过。3份首批成果已完成对应功能验证，没有验证平台准入或销量。

## 环境

Linux x86_64，Python 3；PDF工具v0.16.1。Browser插件不可用，使用Playwright与官方Chrome for Testing Chromium 151；默认下载镜像失败后改用官方分发源。桌面视口1440×1000，工作台另检查390×844。代理测试会话使用测试专用证书处理，不涉及登录或用户凭据。

## 检查

|检查|结果|证据|
|---|---|---|
|页面身份及非空|通过|CyberChef / Excalidraw页面标题、编辑器及模板状态|
|异常页面/运行错误|通过|无相关页面运行错误；CyberChef控制台错误为空|
|真实截图|通过|项目screenshots目录，原创无个人信息输入|
|配方交互|通过|Load recipe → Input → 自动计算 → 3项Output逐一核对；阻断外网|
|模板交互|通过|Open → 导入 → 元素与标题核对 → 选择删除 → 撤销恢复|
|PDF成果|通过|顺序、页数、输出校验、输入校验值、拒绝覆盖|
|手机尺寸报告|通过|静态工作台5行表格，可横向查看|

## 未验证

Windows/macOS、移动端工具使用、全部异常文件、大文件、完整第三方依赖许可，以及卖家账号类目权限。Dify与兼容模型连接仅完成请求/响应模拟测试，没有调用用户真实模型服务。LocalSend和Squoosh仍是候选。

完整数据：[browser-qa.json](browser-qa.json)、[pdf-functional-test.json](pdf-functional-test.json)。操作截图在各项目子目录。
